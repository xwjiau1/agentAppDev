# 环境、PyCharm 与 CI 排障备忘

记录日期：2026-11-24。本文保存本项目实际遇到的问题，供后续开发优先查阅；具体版本与 GitHub 镜像映射是当时的事实，环境变化后需重新核实。

## 1. Python、pip、uv 与虚拟环境

| 现象 | 本次原因或判断依据 | 处理 |
|---|---|---|
| `No module named pip` | 当前 Python 中没有 pip | 先执行 `python -m ensurepip --upgrade`，再安装 uv |
| `No module named ensurepip` | 可能是精简 Python，需先确认解释器来源 | 查看版本和 sys.executable，针对实际发行版处理，不重复尝试 pip |
| `.venv/Scripts/python.exe: No module named uv` | 当前 python 指向项目虚拟环境，外层安装的 uv 不在其中 | 优先直接使用 `uv` 命令；不要假设所有 Python 里都有 uv |
| 终端能运行，但 IDE 标红 | 终端环境与 PyCharm 编辑器解释器、源码路径可能不同 | 独立核对 IDE 解释器和 src 根目录 |

先诊断实际命令来源：

```powershell
Get-Command python, uv -ErrorAction SilentlyContinue
python --version
python -c "import sys; print(sys.executable)"
```

在**外层 Python 环境**中安装工具；若当前激活了项目环境，先退出该环境，再执行：

```powershell
python -m ensurepip --upgrade
python -m pip install uv==0.13.9
```

日常在项目目录优先使用 uv 可执行命令，不需要手工激活 .venv：

```powershell
cd D:\github\Agent-dev\incubator\agent-harness
uv sync --locked
uv run --locked python -m harness_agent run --case examples/demo
uv run --locked python -m unittest discover -s tests -v
```

`uv run` 会选择项目环境；`python -m uv` 则要求**当前 python**能导入 uv。两者不能在任意激活环境中无条件互换。不要为了这次导入错误，把 uv 加入产品运行时依赖。PowerShell 命令末尾也不需要添加反斜杠。

## 2. 包布局与 PyCharm 导入标红

`harness_agent` 是本项目自身的包，不是缺失的第三方依赖。本次已验证项目 `.venv` 可以导入它。

- `src/` 是源码根；`src/harness_agent/` 是包目录。
- `__init__.py` 定义普通包，可以只有说明；不是每个脚本工程都必须有它。
- `__main__.py` 提供 `python -m harness_agent` 的执行入口，再调用 CLI。
- 分发名 `harness-agent` 与 Python 导入名 `harness_agent` 是不同用途的名称。

PyCharm 设置：使用现有解释器 `D:\github\Agent-dev\incubator\agent-harness\.venv\Scripts\python.exe`，必要时将 `src` 标记为 Sources Root；不要把 harness_agent 包目录本身当作源码根。

在 **PyCharm Python Console** 核对，而不仅看终端提示符：

```python
import sys
import harness_agent
print(sys.executable)
print(harness_agent.__file__)
```

前者应指向项目 .venv，后者应指向 src/harness_agent/__init__.py。不要通过改成相对导入或随处修改 sys.path 来掩盖 IDE 配置问题。

## 3. PyCharm 运行与调试配置

| 界面字段 | 本项目设置 |
|---|---|
| 名称 | Harness Demo |
| script 下拉框 | 改为 Module name / 模块名称 |
| 模块名称输入框 | `harness_agent` |
| Script parameters | `run --case examples/demo` |
| Working directory | `D:\github\Agent-dev\incubator\agent-harness` |
| 解释器 | 本项目 `.venv\Scripts\python.exe` |
| 环境变量 | 可保持 `PYTHONUNBUFFERED=1` |
| .env 文件 | 当前离线版本留空 |

本次曾把 `run --case examples/demo` 误填进脚本位置，应放入参数栏。PyCharm 直接使用 .venv Python 启动模块，不需要把 uv 设置为调试目标。

在 Runner 的模型调用和工具执行处设置断点，查看 messages、response.tool_calls、call.arguments、result、step 和 tool_count。工作目录必须指向孵化项目，否则 examples/demo 和 .runs 的相对路径会变。

## 4. Git 提交、CI 与操作系统镜像

```text
git push 保存代码
    → 匹配工作流触发条件
    → GitHub 分配临时机器
    → 检出代码 → 安装 Python/依赖 → 格式/类型检查 → 测试
```

`.github/workflows/harness-mvp.yml` 是开发质量保障配置，不是本地运行、PyCharm 调试或 Git 推送所必需的业务文件。保留它用于 Windows/Linux 双环境检查。Actions runner 镜像是临时机器的系统模板，不等同于我们制作了 Docker 镜像。

**Git 推送成功不等于 CI 成功；CI 通过也不代表真实模型或所有功能已验收。** 排障先查看失败步骤，再读日志，区分 checkout、环境安装、静态检查和测试失败。`Cancelled` 不等于测试断言失败；旧失败通知也不会因为新运行成功而消失。

## 5. 本次 CI 两个故障与修复证据

### 全仓检出遇到超长文件名

运行 `45244255998` 在 checkout 阶段失败，错误为 `File name too long`，对应历史资料中的长名称 docx。Python 测试尚未运行。Windows 作业因矩阵默认 fail-fast 被取消。

修复提交 `caf5cd2`：使用 sparse-checkout，只检出 `incubator/agent-harness`；设置 fail-fast=false，让两个系统分别给出诊断结果。不通过删除资料、重命名整个知识库或关闭测试来绕过问题。

### 滚动系统镜像与固定 Python 缺少安装组合

后续运行 `45244873933` 确认 checkout 通过，随后 setup-python 失败：当时 ubuntu-latest 已指向 Ubuntu 26.04，但固定 Python 3.12.8 没有对应安装包。

这说明安装工具缺少该组合的预构建包，不能直接推断 Python 程序一定无法在新系统上运行。修复前核对 actions/python-versions 官方安装清单，确认 3.12.8 支持 Ubuntu 24.04。

修复提交 `47b9437`：Linux runner 固定为 ubuntu-24.04；setup-python 使用项目 `.python-version`。本次[远端运行 45244992636](https://github.com/xwjiau1/agentAppDev/actions/runs/45244992636)的 Windows 和 Ubuntu 作业都已成功，这是已观察到的历史验证结果，不是对未来每次运行的保证。

后续升级系统镜像或 Python 时，将两者作为组合验证；安装包可用后还要运行项目检查。修复 CI 后必须追踪对应提交的两个远端作业，不能仅凭本机通过或 push 成功宣布修复完成。

## 6. 后续维护必须延续的约定

- 当前 D1 是固定模拟模型驱动的离线链路，任务文本进入历史，但模拟器不自主理解任意任务；completed 仅表示循环结束。
- 保留离线回归；分别标注已实现、模拟验证、真实服务验证和未来目标。
- 技术栈按场景约束、维护成本和证据选择，不为使用框架而引入框架；LangChain 可在实际模型接入需求下重新评估。
- 延续用户要求：代码清晰，每个非空 Python 代码行有中文说明；注释与代码同批维护。
- 环境错误优先查解释器路径；CI 错误优先查失败步骤。只修复有证据指向的问题，不盲目升级、重装或重构业务代码。

官方依据：[PyCharm 解释器](https://www.jetbrains.com/help/pycharm/configuring-python-interpreter.html)、[源码根目录](https://www.jetbrains.com/help/pycharm/project-structure-dialog.html)、[模块运行配置](https://www.jetbrains.com/help/pycharm/run-debug-configuration-python.html)、[checkout 稀疏检出](https://github.com/actions/checkout/tree/v4)、[Python 安装清单](https://github.com/actions/python-versions/blob/main/versions-manifest.json)。以上链接为本次问题的核对入口，使用时应注意版本变化。
