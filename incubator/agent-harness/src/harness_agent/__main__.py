# 包的命令行入口：python -m harness_agent 会执行此文件。
"""Keep the executable entry separate from importable business logic."""

# 从 harness_agent.cli 显式导入 main，声明本模块所需的依赖。
from harness_agent.cli import main

# 执行 CLI，把 main 返回值交给操作系统作为退出码。
raise SystemExit(main())
