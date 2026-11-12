# Condition条件变量与循环等待

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

Condition协调状态变化通知。wait会在等待时释放关联锁，被唤醒后重新取得；调用方必须重新检查条件。

## 面试问答

**问：为什么用while而不是if等待消息？** 唤醒不保证条件一定为真，可能是虚假唤醒，也可能被其他消费者先取走。

**问：notify_all是否立刻让所有线程执行？** 不会，它们还需等锁可用并重新检查条件。

## 实际案例与代码

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 等待消息或超时

[s13_agent_teams/code.py，898–909行](../../应用侧/自动化与工具助手/通用AgentHarness/s13_agent_teams/code.py#L898-L909)

```python
def wait_for_messages(self, agent: str,
                      timeout: float | None = None) -> list[dict]:
    """Block until the agent has messages or timeout expires."""
    deadline = None if timeout is None else time.monotonic() + timeout
    with self._changed:
        while not self.peek(agent):
            remaining = (None if deadline is None
                         else deadline - time.monotonic())
            if remaining is not None and remaining <= 0:
                return []
            self._changed.wait(remaining)
        return self._read_unlocked(agent)
```

循环检查peek，用remaining控制总等待预算；不能把每次wait都重置成完整超时，否则总等待可能超出预期。

## 易错点与追问

操作Condition应持有关联锁。通知用于提示状态可能改变，不是持久消息本身；消息仍在邮箱中。
