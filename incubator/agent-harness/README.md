# Agent Harness MVP

一个能执行工具任务，并且**可取消、有预算、可追溯、可验收**的单 Agent 运行时。

**当前状态：设计与开发计划已落盘，运行时代码尚未实现。** 本目录是新项目孵化区，与仓库中已有的第三方 Harness 参考案例独立维护。

## 先看这三份文档

| 文档 | 回答的问题 |
|---|---|
| [MVP 设计](docs/MVP设计.md) | 产品做什么、怎么使用、架构和功能怎么实现、怎样算完成 |
| [开发计划](docs/开发计划.md) | 先做什么、每一步交付什么、如何验证和提交 |
| [开发记录](docs/开发记录.md) | 当前进度、已作决策、验证结果和下一步 |

## 一句话看懂首版

用户给出一个文件整理任务 → Agent 读取输入 → 调用工具生成结果 → 程序自动核对结果 → 留下完整运行记录。过程中可以按 Ctrl+C，达到预算也会停止。

首个示例：读取 [输入说明](examples/demo/input/brief.txt)，提取三个字段并生成 `result.json`，与 [预期结果](examples/demo/expected.json) 比较。任务描述见 [task.txt](examples/demo/task.txt)。示例文件已创建，Agent 执行程序尚未创建。

## 首版范围

- Python 3.11 及以上，本地 CLI，单进程、单 Agent、工具串行执行。
- `read_file`、`write_file` 两个工具；模拟模型优先，之后接一个真实模型适配器。
- 三项预算：模型调用次数、工具调用次数、总时长。
- 本地 JSONL 轨迹、JSON 结果、固定规则验收。

长期记忆、历史压缩、子 Agent、MCP、插件系统、服务端和图形界面留给后续版本。

## 最终会怎样使用

以下是**计划实现的命令**，当前不能执行：

```powershell
python -m harness_agent run --case examples/demo
python -m harness_agent run --case examples/demo --max-steps 8 --max-tool-calls 12 --max-seconds 60
python -m harness_agent show RUN_ID
python -m harness_agent verify RUN_ID
```

默认使用模拟模型，离线跑通完整流程。真实模型通过显式 `--model api` 选择；接口配置在接入阶段确定，凭据仅从环境变量读取。

## 项目与知识库

整体背景见 [Harness 调研与孵化方案](../../doc/Harness项目调研与孵化方案.md)。本次 MVP 进一步缩小了该方案的范围：暂缓 SQLite、恢复、记忆和子任务，先用单写入者 JSONL 把一条完整任务跑通。

每次开发同步更新开发记录，完成一个能力后再把真实代码、边界和验证结论回写技术库；未实现的设计不登记为已运行案例。仓库整体维护遵守 [维护规则](../../doc/维护规则.md)。
