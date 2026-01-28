# cc-statusline 项目概述

## 项目基本信息

| 属性 | 值 |
|-----|-----|
| 项目名称 | cc-statusline |
| 项目目的 | Claude Code 状态栏功能模块 |
| 当前版本 | 0.1.0 |
| 许可证 | Apache-2.0 |
| 编程语言 | Python 3.9+ |
| 包管理器 | uv |
| 项目布局 | Src Layout |

## 技术栈详情

- **测试框架**: pytest + pytest-cov
- **代码格式化**: black（行长 100）
- **代码检查**: ruff
- **类型检查**: mypy
- **构建工具**: hatchling

## 项目目录结构

```
cc-statusline/
├── src/cc_statusline/      # 源代码（Src Layout）
│   ├── __init__.py         # 包初始化和版本信息
│   ├── __main__.py         # CLI 入口点
│   ├── core/               # 核心业务逻辑
│   │   ├── status.py       # 状态管理（待实现）
│   │   └── formatter.py    # 格式化输出（待实现）
│   ├── config/             # 配置管理
│   │   └── settings.py     # 配置加载（待实现）
│   └── cli/                # 命令行接口
│       └── commands.py     # CLI 命令（待实现）
├── tests/                  # 测试文件
│   ├── conftest.py         # pytest 配置
│   ├── unit/               # 单元测试
│   └── integration/        # 集成测试
├── docs/                   # 文档目录
├── scripts/                # 工具脚本
│   └── verify_setup.sh     # 环境验证脚本
├── examples/               # 使用示例
├── pyproject.toml          # 项目配置和依赖
└── README.md               # 项目说明
```

## 模块依赖关系

```
cli.commands → core.status → core.formatter
             ↘ config.settings ↗
```

## 关键约束

1. **语言约束**: 所有交流必须使用中文
2. **文档存储**: 所有文档必须存放在 `.claude/` 目录下
3. **包管理**: 必须使用 uv，不得使用 pip
4. **代码检索**: 必须优先使用 CCLSP MCP 服务
5. **时间获取**: 必须使用 Time MCP 服务获取当前时间
6. **文档命名**: 必须遵循 `YYYY-MM-DD_文档类型_文档名称_v版本号.扩展名` 格式

## 设计模式

- **Src Layout**: 源码隔离，避免导入污染
- **模块化设计**: 单一职责原则，清晰的模块边界
- **依赖注入**: 配置通过参数传递，便于测试
- **类型提示**: 使用 Python 类型注解，mypy 静态检查

## 项目状态

项目已完成基础架构初始化，待实现核心功能模块。
