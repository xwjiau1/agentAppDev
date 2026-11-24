# asyncio.to_thread桥接同步阻塞函数

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

to_thread把同步函数交给线程执行，并返回可等待对象，避免直接在事件循环线程内阻塞。它不会自动把函数内部逻辑改成原生异步。

## 面试问答

**问：await to_thread可以保持事件循环响应吗？** 通常可把同步阻塞转移出去，但计算类型、线程资源和其他阻塞仍需检查。

**问：取消await会杀掉该工作线程吗？** 不会自动强制终止已在运行的同步函数。

## 实际案例与代码

关联应用：[通用AgentHarness](../../application/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 从协程调用同步Runner

[s16_workflow_runtime/code.py，485–489行](../../application/自动化与工具助手/通用AgentHarness/s16_workflow_runtime/code.py#L485-L489)

```python
run = await asyncio.to_thread(
    self.runner.run, prompt, schema, label
)
result = run.value
tokens = run.tokens
```

将self.runner.run作为函数对象传入，后面是它的位置实参。await取得RunnerOutput后读取value与tokens。

## 易错点与追问

取消等待线程结果的协程时，同步函数可能仍在执行。持有资源的范围应覆盖线程真正结束。混合检索 RAG 的 `InferenceSlot` 将释放锁放在后台任务的 `finally` 中，从请求协程用 `asyncio.shield(worker)` 等待该任务。应用持有任务引用，退出时等待剩余计算。测试取消首个等待者，确认后续请求直到线程结束前仍会得到忙碌响应。[后台任务源码](../../incubator/hybrid-rag/encoder/rag_models/api.py#L34-L55) · [取消回归测试](../../incubator/hybrid-rag/encoder/tests/test_api.py)

它主要适合桥接阻塞I/O等同步接口，不应承诺任意CPU计算自动多核加速。共享客户端是否线程安全需依赖其实现。
