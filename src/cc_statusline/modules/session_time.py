"""会话时间模块。

跟踪和显示当前会话的使用时间。
"""

import os
from datetime import datetime, timedelta
from typing import Optional

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
    """

    # 会话状态文件路径
    STATE_FILE = os.path.expanduser("~/.claude/session_time.json")

    def __init__(self) -> None:
        self._start_time: Optional[datetime] = None
        self._last_elapsed: Optional[timedelta] = None
        self._paused: bool = False
        self._pause_start: Optional[datetime] = None
        self._format: str = "short"  # short: "2h 15m", long: "02:15:30"

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="session_time",
            description="显示当前会话使用时间",
            version="1.0.0",
            author="Claude Code",
            enabled=True,
        )

    def initialize(self) -> None:
        """初始化模块。"""
        self._load_state()
        if self._start_time is None:
            self._start_time = datetime.now()

    def refresh(self) -> None:
        """刷新时间数据。"""
        self._calculate_elapsed()

    def _load_state(self) -> None:
        """加载会话状态。"""
        try:
            import json

            if os.path.exists(self.STATE_FILE):
                with open(self.STATE_FILE, encoding="utf-8") as f:
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

            os.makedirs(os.path.dirname(self.STATE_FILE), exist_ok=True)
            with open(self.STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f)
        except (OSError, AttributeError):
            pass

    def _calculate_elapsed(self) -> Optional[timedelta]:
        """计算经过的时间。

        Returns:
            经过的时间
        """
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

        start_time_str = self._start_time.strftime("%H:%M:%S") if self._start_time else "未知"
        return ModuleOutput(
            text=formatted,
            icon="⏱️",
            color=color,
            status=status,
            tooltip=f"会话开始于 {start_time_str}",
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
