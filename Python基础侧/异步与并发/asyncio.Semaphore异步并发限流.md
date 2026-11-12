# asyncio.Semaphore异步并发限流

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

Semaphore维护可用许可，async with进入时等待取得许可，退出时归还；可限制同时进入某段代码的协程数。

## 面试问答

**问：它能直接限制每分钟API请求数吗？** 不能，并发数与单位时间请求数不是一回事。

**问：信号量等于任务总数上限吗？** 不等于，任务可排队很多；总任务数还要单独计数与限制。

## 实际案例与代码

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 许可控制执行窗口

[s16_workflow_runtime/code.py，484–489行](../../应用侧/自动化与工具助手/通用AgentHarness/s16_workflow_runtime/code.py#L484-L489)

```python
async with self._limits.semaphore:
    run = await asyncio.to_thread(
        self.runner.run, prompt, schema, label
    )
    result = run.value
    tokens = run.tokens
```

只有取得许可后才把runner送入工作线程；许可覆盖await等待结果的时间。ExecutionLimits另用agents计数实现总调用上限。

## 易错点与追问

需要同时考虑超时、取消和预算。不能因使用async with就认为取消等待一定能停止已经运行的同步线程。
