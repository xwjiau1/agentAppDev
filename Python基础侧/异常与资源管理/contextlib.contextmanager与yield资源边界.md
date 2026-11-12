# contextlib.contextmanager与yield资源边界

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

contextmanager把单次yield生成器封装为with上下文：yield前进入，yield后退出；try/finally确保离开时释放。

## 面试问答

**问：正常协议要求yield几次？** 恰好一次；零次或多次会违反上下文管理协议。

**问：with块的异常如何返回管理器？** 在yield处重新注入，管理器可处理或继续传播。

## 实际案例与代码

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 完整文件锁边界

[s13_agent_teams/code.py，71–89行](../../应用侧/自动化与工具助手/通用AgentHarness/s13_agent_teams/code.py#L71-L89)

```python
def task_store_lock():
    """Serialize task mutations across threads and host processes."""
    with task_lock:
        depth = getattr(_task_store_state, "depth", 0)
        if depth == 0:
            TASKS_DIR.mkdir(parents=True, exist_ok=True)
            handle = TASK_LOCK_PATH.open("a+", encoding="utf-8")
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            _task_store_state.handle = handle
        _task_store_state.depth = depth + 1
        try:
            yield
        finally:
            _task_store_state.depth -= 1
            if _task_store_state.depth == 0:
                handle = _task_store_state.handle
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                handle.close()
                del _task_store_state.handle
```

函数由前一行@contextmanager装饰。最外层取得文件锁，yield进入业务块，finally递减深度并在最外层退出时解锁、关闭句柄。

## 易错点与追问

同步with与async with协议不同。不要在不该吞异常时捕获后悄悄结束，也不要把contextmanager当成普通可重复yield的迭代器。
