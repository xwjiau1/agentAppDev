# 集成Harness的模块复用与入口协调

## 技术实现

s15把工具循环、记忆、团队、背景执行、调度与停止钩子组合起来。它动态加载s09并注入同一个宿主模型、客户端和工作区。

## 应用思路

集成时应维护单一配置来源，并理清输入与事件的入口，减少多个终端读者争抢用户输入。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 复用记忆运行时

[s15_integrated_harness/code.py，84–99行](../../应用侧/自动化与工具助手/通用AgentHarness/s15_integrated_harness/code.py#L84-L99)

```python
def load_memory_runtime():
    """Load s09 once and share this host's client, model, and workspace."""
    path = Path(__file__).resolve().parents[1] / "s09_memory" / "code.py"
    spec = importlib.util.spec_from_file_location(
        f"integrated_memory_{id(client)}", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load memory runtime from {path}")
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    runtime.WORKDIR = WORKDIR
    runtime.MEMORY_DIR = WORKDIR / ".memory"
    runtime.MEMORY_INDEX = runtime.MEMORY_DIR / "MEMORY.md"
    runtime.client = client
    runtime.MODEL = MODEL
    return runtime
```

从相邻s09按文件路径加载，然后覆盖WORKDIR、记忆目录、client和MODEL。整个案例内部目录不可打散。

## 实现差异与边界

这是当前文件组合方式，并非任意模块都能安全猴子补丁。导入会执行顶层初始化，真实凭据和环境仍需另行配置。
