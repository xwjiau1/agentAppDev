# Agent Harness MVP

一个能执行工具任务，并且**可取消、有预算、可追溯、可验收**的单 Agent 运行时。

**当前状态：D1 离线工具循环已实现；D2–D4 尚待开发。** 本目录是新项目孵化区，与仓库中已有的第三方 Harness 参考案例独立维护。

## 文档入口

| 文档 | 回答的问题 |
|---|---|
| [MVP 设计](docs/MVP设计.md) | 产品做什么、怎么使用、架构和功能怎么实现、怎样算完成 |
| [技术实现方案](docs/技术实现方案.md) | 技术栈及选型依据、模块与接口、关键实现、代码质量和扩展规则 |
| [开发计划](docs/开发计划.md) | 先做什么、每一步交付什么、如何验证和提交 |
| [开发记录](docs/开发记录.md) | 当前进度、已作决策、验证结果和下一步 |

## 一句话看懂首版

用户给出一个文件整理任务 → Agent 读取输入 → 调用工具生成结果 → 程序自动核对结果 → 留下完整运行记录。过程中可以按 Ctrl+C，达到预算也会停止。

首个示例：读取 [输入说明](examples/demo/input/brief.txt)，提取三个字段并生成 `result.json`，与 [预期结果](examples/demo/expected.json) 比较。任务描述见 [task.txt](examples/demo/task.txt)。离线模拟程序已运行核对，不代表真实模型完成任务。

## 首版范围

- Python 最低 3.12，首版验收 3.12；本地 CLI，单进程、单 Agent、工具串行执行。
- `read_file`、`write_file` 两个工具；模拟模型优先，之后接一个真实模型适配器。
- 三项预算：模型调用次数、工具调用次数、总时长。
- 本地 JSONL 轨迹、JSON 结果、固定规则验收。

长期记忆、历史压缩、子 Agent、MCP、插件系统、服务端和图形界面留给后续版本。

工程基线采用 asyncio、argparse、dataclass/Protocol 和 JSONL；真实模型可选 HTTPX。uv 管理环境与锁文件，uv_build 打包，Ruff/mypy/unittest/coverage.py 负责质量检查。选型理由与替换条件见技术实现方案，工具与代码将在 D1 起落地。

## 当前可以运行

在本项目目录执行（本次已验证 Windows / Python 3.12.8）：

```powershell
python -m uv sync --locked
python -m uv run --locked python -m harness_agent run --case examples/demo
python -m uv run --locked python -m unittest discover -s tests -v
python -m uv run --locked ruff check src tests
python -m uv run --locked mypy src tests
```

需要先安装 uv 0.13.9。输出文件位于 `.runs/<run_id>/output/result.json`。模拟模型是固定演示脚本，会解析实际输入，不读取 expected.json；不能把它当作通用自然语言模型。

本批验证 11 项测试通过，含分支覆盖统计为 91%。当前 CLI 的 completed 只表示 D1 循环结束；自动验收、持久轨迹、可配置预算和取消收尾仍待 D2/D3。GitHub Actions 已配置，远端执行结果另行核对。

## 后续目标命令

以下参数与命令尚未实现：

```powershell
python -m harness_agent run --case examples/demo --max-steps 8 --max-tool-calls 12 --max-seconds 60
python -m harness_agent show RUN_ID
python -m harness_agent verify RUN_ID
```

真实模型适配在 D4 增加。本期保留固定的 8 次模型调用保险上限；这不等于三项完整预算。

## 项目与知识库

整体背景见 [Harness 调研与孵化方案](../../doc/Harness项目调研与孵化方案.md)。本次 MVP 进一步缩小了该方案的范围：暂缓 SQLite、恢复、记忆和子任务，先用单写入者 JSONL 把一条完整任务跑通。

每次开发同步更新开发记录，完成一个能力后再把真实代码、边界和验证结论回写技术库；未实现的设计不登记为已运行案例。仓库整体维护遵守 [维护规则](../../doc/维护规则.md)。

## 代码阅读顺序

1. [共享契约](src/harness_agent/contracts.py)：模型、消息、工具结果的数据结构。
2. [Runner](src/harness_agent/runner.py)：完整循环与资源释放。
3. [文件工具](src/harness_agent/tools.py)：参数、路径与大小检查。
4. [模拟模型](src/harness_agent/model.py)：固定演示如何发出工具调用。
5. [行为测试](tests/test_core.py)：正常链路与失败边界。
