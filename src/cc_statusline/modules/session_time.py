"""会话时间模块。

跟踪和显示当前会话的使用时间。
优先从 Claude Code 传递的 total_duration_ms 获取时间，回退到本地计时。
"""

import glob
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Optional

from cc_statusline.modules.base import (
    BaseModule,
    ModuleMetadata,
    ModuleOutput,
    ModuleStatus,
)
from cc_statusline.modules.registry import ModuleRegistry


class SessionTimeModule(BaseModule):
    """会话时间模块。

    显示 Claude Code 会话的运行时长。
    优先使用 Claude Code 传递的 total_duration_ms，回退到本地计时。
    """

    def __init__(self) -> None:
        self._start_time: Optional[datetime] = None
        self._last_elapsed: Optional[timedelta] = None
        self._paused: bool = False
        self._pause_start: Optional[datetime] = None
        self._format: str = "short"  # short: "2h 15m", long: "02:15:30"
        self._context: dict[str, Any] = {}  # Claude Code 传递的上下文
        self._total_duration_ms: Optional[int] = None  # 来自 Claude Code 的总时长（毫秒）

    def _get_state_file_path(self) -> str:
        """获取当前会话专属的状态文件路径。

        通过检测 Claude Code 的当前会话ID来确保：
        1. 每个Claude Code窗口有独立的会话时间统计
        2. 同一窗口的时间能够正确累积

        Returns:
            状态文件路径
        """
        import glob

        # 尝试获取当前活跃的 Claude Code 会话ID
        session_id = self._get_active_session_id()

        if session_id:
            # 使用会话ID作为状态文件名
            return os.path.expanduser(f"~/.claude/session_time_{session_id}.json")
        else:
            # 降级方案：使用固定的状态文件
            return os.path.expanduser("~/.claude/session_time.json")

    def _get_active_session_id(self) -> Optional[str]:
        """获取当前活跃的 Claude Code 会话ID。

        Returns:
            会话ID，如果无法获取则返回 None
        """
        try:
            # 获取当前工作目录
            cwd = os.getcwd()

            # Claude Code 将工作目录中的斜杠替换为短横线
            # 例如: /home/michael/workspace/github/cc-statusline
            # 变为: -home-michael-workspace-github-cc-statusline
            project_dir_name = "-" + cwd.replace("/", "-").lstrip("-")

            # 构建项目会话目录路径
            project_session_dir = os.path.expanduser(f"~/.claude/projects/{project_dir_name}")

            if not os.path.exists(project_session_dir):
                return None

            # 查找最近修改的 .jsonl 会话文件
            jsonl_files = glob.glob(os.path.join(project_session_dir, "*.jsonl"))

            if not jsonl_files:
                return None

            # 按修改时间排序，获取最新的
            latest_file = max(jsonl_files, key=os.path.getmtime)

            # 提取会话ID（去掉 .jsonl 扩展名）
            session_id = os.path.basename(latest_file).replace(".jsonl", "")

            return session_id

        except (OSError, IndexError):
            return None

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="session_time",
            description="显示当前会话使用时间",
            version="1.1.0",
            author="Claude Code",
            enabled=True,
        )

    def initialize(self) -> None:
        """初始化模块。"""
        self._load_state()
        if self._start_time is None:
            self._start_time = datetime.now()

    def set_context(self, context: dict[str, Any]) -> None:
        """设置上下文数据。

        从 Claude Code statusLine hook 接收的 JSON 数据。

        Args:
            context: 包含 cost.total_duration_ms 等字段的字典
        """
        self._context = context
        # 提取 total_duration_ms（毫秒）
        cost_data = context.get("cost", {})
        self._total_duration_ms = cost_data.get("total_duration_ms")

    def refresh(self) -> None:
        """刷新时间数据。"""
        self._calculate_elapsed()

    def _load_state(self) -> None:
        """加载会话状态。"""
        try:
            import json

            state_file = self._get_state_file_path()
            if os.path.exists(state_file):
                with open(state_file, encoding="utf-8") as f:
                    state = json.load(f)

                start_str = state.get("start_time")
                if start_str:
                    self._start_time = datetime.fromisoformat(start_str)

                self._format = state.get("format", "short")
        except (json.JSONDecodeError, OSError, ValueError):
            pass

    def _save_state(self) -> None:
        """保存会话状态。"""
        try:
            import json

            state = {
                "start_time": self._start_time.isoformat() if self._start_time else None,
                "format": self._format,
            }

            state_file = self._get_state_file_path()
            os.makedirs(os.path.dirname(state_file), exist_ok=True)
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(state, f)
        except (OSError, AttributeError):
            pass

    def _calculate_elapsed(self) -> Optional[timedelta]:
        """计算经过的时间。

        优先使用 Claude Code 传递的 total_duration_ms，
        回退到本地计时（从文件读取或实时计算）。

        Returns:
            经过的时间
        """
        # 优先使用 Claude Code 传递的时间
        if self._total_duration_ms is not None:
            self._last_elapsed = timedelta(milliseconds=self._total_duration_ms)
            return self._last_elapsed

        # 回退到本地计时
        if self._start_time is None:
            return None

        now = datetime.now()
        self._last_elapsed = now - self._start_time
        return self._last_elapsed

    def _format_elapsed(self, elapsed: timedelta) -> str:
        """格式化经过的时间。

        Args:
            elapsed: 经过的时间

        Returns:
            格式化后的时间字符串
        """
        if self._format == "long":
            # 长格式: "02:15:30"
            total_seconds = int(elapsed.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            # 短格式: "2h 15m" 或 "15m 30s"
            total_seconds = int(elapsed.total_seconds())

            if total_seconds >= 3600:
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                return f"{hours}h {minutes}m"
            elif total_seconds >= 60:
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                return f"{minutes}m {seconds}s"
            else:
                return f"{total_seconds}s"

    def set_format(self, fmt: str) -> None:
        """设置时间格式。

        Args:
            fmt: 格式 ("short" 或 "long")
        """
        if fmt in ("short", "long"):
            self._format = fmt
            self._save_state()

    def get_elapsed(self) -> Optional[timedelta]:
        """获取经过的时间。

        Returns:
            经过的时间
        """
        return self._last_elapsed

    def reset(self) -> None:
        """重置会话计时。"""
        self._start_time = datetime.now()
        self._last_elapsed = None
        self._save_state()

    def get_output(self) -> ModuleOutput:
        """获取模块输出。

        Returns:
            模块输出
        """
        elapsed = self._calculate_elapsed()

        if elapsed is None:
            return ModuleOutput(
                text="--:--",
                icon="⏱️",
                color="gray",
                status=ModuleStatus.SUCCESS,
            )

        formatted = self._format_elapsed(elapsed)

        # 根据时长选择颜色
        hours = elapsed.total_seconds() / 3600
        if hours >= 2:
            color = "green"
            status = ModuleStatus.SUCCESS
        elif hours >= 1:
            color = "yellow"
            status = ModuleStatus.SUCCESS
        else:
            color = "blue"
            status = ModuleStatus.SUCCESS

        # 构建 tooltip
        if self._total_duration_ms is not None:
            # 来自 Claude Code 的时间
            tooltip = f"会话时长: {formatted}"
        elif self._start_time:
            start_time_str = self._start_time.strftime("%H:%M:%S")
            tooltip = f"会话开始于 {start_time_str}"
        else:
            tooltip = "未知"

        return ModuleOutput(
            text=formatted,
            icon="⏱️",
            color=color,
            status=status,
            tooltip=tooltip,
        )

    def get_start_time(self) -> Optional[datetime]:
        """获取会话开始时间。

        Returns:
            开始时间
        """
        return self._start_time

    def get_formatted_start_time(self) -> str:
        """获取格式化的开始时间。

        Returns:
            格式化的时间字符串
        """
        if self._start_time is None:
            return "未知"
        return self._start_time.strftime("%H:%M:%S")

    def is_available(self) -> bool:
        """检查模块是否可用。

        Returns:
            是否可用
        """
        return True

    def get_refresh_interval(self) -> float:
        """获取刷新间隔。

        Returns:
            刷新间隔（秒）
        """
        return 1.0  # 每秒更新

    def cleanup(self) -> None:
        """清理资源。"""
        self._save_state()


# 注册模块
def _register_module() -> None:
    """注册模块到注册表。"""
    ModuleRegistry.register(
        "session_time",
        SessionTimeModule,
    )
    ModuleRegistry.enable("session_time")


# 自动注册
_register_module()
