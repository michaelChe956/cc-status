"""pytest 配置和共享 fixtures"""

from typing import Any

import pytest


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """提供测试用的示例配置"""
    return {"name": "test", "value": 42}
