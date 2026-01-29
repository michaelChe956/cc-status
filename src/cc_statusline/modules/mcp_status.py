"""MCP 状态模块。

显示所有 MCP 服务器的状态信息。
"""

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from cc_statusline.modules.base import (
    BaseModule,
    ModuleMetadata,
    ModuleOutput,
    ModuleStatus,
)
from cc_statusline.modules.registry import ModuleRegistry


@dataclass
class MCPServerInfo:
    """MCP 服务器信息。"""

    name: str
    status: str  # running, stopped, error
    command: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    error_message: Optional[str] = None


class MCPStatusModule(BaseModule):
    """MCP 状态模块。

    显示所有 MCP 服务器的状态。
    """

    def __init__(self) -> None:
        self._servers: dict[str, MCPServerInfo] = {}
        self._last_update: float = 0.0
        self._cache_timeout: float = 5.0  # 5秒缓存

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="mcp_status",
            description="显示所有 MCP 服务器状态",
            version="1.0.0",
            author="Claude Code",
            enabled=True,
        )

    def initialize(self) -> None:
        """初始化模块。"""
        # 移除立即刷新，改为延迟到第一次 get_output() 时
        # self._refresh_servers()  # 延迟初始化，避免导入时触发 MCP 命令
        pass

    def refresh(self) -> None:
        """刷新 MCP 服务器状态。"""
        self._refresh_servers()

    def _refresh_servers(self) -> None:
        """刷新服务器列表。"""
        servers = self._detect_mcp_servers()
        self._servers = {s.name: s for s in servers}
        self._last_update = _get_current_time()

    def _detect_mcp_servers(self) -> list[MCPServerInfo]:
        """检测 MCP 服务器。

        Returns:
            MCP 服务器列表
        """
        servers: list[MCPServerInfo] = []

        # 方法1: 尝试使用 claude mcp list 命令
        servers.extend(self._get_from_claude_command())

        # 方法2: 解析配置文件
        servers.extend(self._get_from_config())

        return servers

    def _get_from_claude_command(self) -> list[MCPServerInfo]:
        """从 claude mcp list 命令获取服务器信息。

        Returns:
            MCP 服务器列表
        """
        servers: list[MCPServerInfo] = []

        try:
            # 尝试运行 claude mcp list
            result = subprocess.run(
                ["claude", "mcp", "list"],
                capture_output=True,
                text=True,
                timeout=10,  # 增加超时时间到10秒
            )

            if result.returncode == 0:
                servers.extend(self._parse_mcp_list_output(result.stdout))
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return servers

    def _parse_mcp_list_output(self, output: str) -> list[MCPServerInfo]:
        """解析 claude mcp list 命令输出。

        Args:
            output: 命令输出

        Returns:
            MCP 服务器列表
        """
        servers: list[MCPServerInfo] = []
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()

            # 跳过空行和非服务器行
            if not line or line.startswith("Checking"):
                continue

            # 新格式: "server-name: command - ✓ Connected"
            if " - ✓ Connected" in line:
                # 提取服务器名称（冒号前的部分）
                parts = line.split(":", 1)
                if len(parts) >= 1:
                    name = parts[0].strip()
                    status = "running"  # ✓ Connected 表示正在运行

                    servers.append(
                        MCPServerInfo(
                            name=name,
                            status=status,
                        )
                    )

        return servers

    def _get_from_config(self) -> list[MCPServerInfo]:
        """从配置文件获取服务器信息。

        Returns:
            MCP 服务器列表
        """
        servers: list[MCPServerInfo] = []

        # 查找 MCP 配置文件
        config_paths = [
            Path.home() / ".claude" / "mcp.json",
            Path.home() / ".config" / "claude" / "mcp.json",
            Path(os.environ.get("CLAUDE_CONFIG_DIR", "")) / "mcp.json",
        ]

        for config_path in config_paths:
            if config_path.exists():
                servers.extend(self._parse_mcp_config(config_path))
                break

        return servers

    def _parse_mcp_config(self, config_path: Path) -> list[MCPServerInfo]:
        """解析 MCP 配置文件。

        Args:
            config_path: 配置文件路径

        Returns:
            MCP 服务器列表
        """
        servers: list[MCPServerInfo] = []

        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)

            # 解析 mcpServers 字段
            mcp_servers = config.get("mcpServers", {})
            for name, server_config in mcp_servers.items():
                command = None
                if isinstance(server_config, dict):
                    command = server_config.get("command")
                    args = server_config.get("args", [])
                    if command:
                        command = f"{command} {' '.join(args)}"

                servers.append(
                    MCPServerInfo(
                        name=name,
                        status="unknown",
                        command=command,
                    )
                )
        except (json.JSONDecodeError, OSError):
            pass

        return servers

    def get_output(self) -> ModuleOutput:
        """获取模块输出。

        Returns:
            模块输出
        """
        # 延迟初始化：只在第一次获取输出时刷新
        if not self._servers and self._last_update == 0.0:
            self._refresh_servers()

        # 检查缓存是否过期
        if self._servers and _get_current_time() - self._last_update > self._cache_timeout:
            self._refresh_servers()

        if not self._servers:
            return ModuleOutput(
                text="无 MCP 服务器",
                icon="🔌",
                color="gray",
                status=ModuleStatus.SUCCESS,
            )

        # 统计各状态服务器数量
        running = sum(1 for s in self._servers.values() if s.status == "running")
        errors = sum(1 for s in self._servers.values() if s.status == "error")
        total = len(self._servers)

        # 构建显示文本
        if errors > 0:
            status = ModuleStatus.ERROR
            color = "red"
            icon = "🔴"
        elif running < total:
            status = ModuleStatus.WARNING
            color = "yellow"
            icon = "🟡"
        else:
            status = ModuleStatus.SUCCESS
            color = "green"
            icon = "🟢"

        # 格式化输出: "🔌 5/5 运行中" 或 "🔴 2 错误"
        if running == total:
            text = f"{running}/{total} 运行中"
        elif errors > 0:
            text = f"{errors} 错误"
        else:
            text = f"{running}/{total} 运行中"

        return ModuleOutput(
            text=text,
            icon=icon,
            color=color,
            status=status,
            tooltip=f"MCP 服务器: {', '.join(self._servers.keys())}",
        )

    def get_server_details(self) -> list[dict[str, Any]]:
        """获取服务器详细信息。

        Returns:
            服务器详情列表
        """
        return [
            {
                "name": name,
                "status": server.status,
                "command": server.command,
                "error": server.error_message,
            }
            for name, server in self._servers.items()
        ]

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
        return 10.0  # MCP 状态变化不频繁，10秒刷新一次

    def cleanup(self) -> None:
        """清理资源。"""
        self._servers.clear()


# 获取当前时间的辅助函数
def _get_current_time() -> float:
    """获取当前时间戳。"""
    import time

    return time.time()


# 注册模块
def _register_module() -> None:
    """注册模块到注册表。"""
    ModuleRegistry.register(
        "mcp_status",
        MCPStatusModule,
    )
    ModuleRegistry.enable("mcp_status")


# 自动注册
_register_module()
