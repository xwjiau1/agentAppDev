# asynccontextmanager异步上下文管理

> 复习优先级：进阶。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

async with通过__aenter__和__aexit__管理可等待的资源边界。asynccontextmanager可把单次yield的异步生成器封装成异步上下文管理器。

## 面试问答

**问：yield前后分别做什么？** 前面准备并进入，后面清理；代码块异常会在yield处重新进入生成器的异常处理。

**问：它和普通异步生成器完全一样吗？** 不是，装饰器赋予上下文管理接口，必须遵守其单次yield协议。

## 实际案例与代码

[OpenManus通用任务助手](../../应用侧/自动化与工具助手/OpenManus通用任务助手/案例说明.md) · [base.py，58–82行](../../应用侧/自动化与工具助手/OpenManus通用任务助手/app/agent/base.py#L58-L82)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
@asynccontextmanager
async def state_context(self, new_state: AgentState):
    """用于安全 agent 状态转换的上下文管理器。

    Args:
        new_state: 在上下文中要转换到的状态。

    Yields:
        None: 允许在新状态下执行。

    Raises:
        ValueError: 如果 new_state 无效。
    """
    if not isinstance(new_state, AgentState):
        raise ValueError(f"Invalid state: {new_state}")

    previous_state = self.state
    self.state = new_state
    try:
        yield
    except Exception as e:
        self.state = AgentState.ERROR  # 失败时转换到 ERROR 状态
        raise e
    finally:
        self.state = previous_state  # 恢复到之前的状态
```

state_context保存旧状态，进入时切换，yield让调用方在新状态内运行，finally恢复旧状态；这是一种可复用的状态边界。

## 易错点与追问

清理应写在finally中，且要检查异常抑制与状态覆盖。这个机制不意味着资源在进程崩溃时也能可靠释放。
