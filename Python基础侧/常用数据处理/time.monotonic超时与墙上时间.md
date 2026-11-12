# time.monotonic超时与墙上时间

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

time.time反映墙上时间，可能受系统校时影响；monotonic适合测量经过时长与超时预算，不用于展示日期。

## 面试问答

**问：为何deadline用monotonic而不是time.time？** 避免系统时间跳变打乱剩余等待时长。

**问：monotonic值能存起来当跨进程长期到期日期吗？** 不宜这样使用，它的参考点不适合作为业务日历时间。

## 实际案例与代码

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 递减总等待预算

[s13_agent_teams/code.py，901–908行](../../应用侧/自动化与工具助手/通用AgentHarness/s13_agent_teams/code.py#L901-L908)

```python
deadline = None if timeout is None else time.monotonic() + timeout
with self._changed:
    while not self.peek(agent):
        remaining = (None if deadline is None
                     else deadline - time.monotonic())
        if remaining is not None and remaining <= 0:
            return []
        self._changed.wait(remaining)
```

先确定截止值，每次唤醒后用deadline减当前monotonic，剩余<=0时退出。None表示没有设超时。

## 易错点与追问

调度日历与测量超时是不同问题。不要把monotonic解释成CPU时间，也不要混用两种时钟做减法。
