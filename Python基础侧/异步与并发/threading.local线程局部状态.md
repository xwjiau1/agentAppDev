# threading.local线程局部状态

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

threading.local使同一对象的属性在不同线程中分别保存，适合记录每个线程的上下文或重入深度。

## 面试问答

**问：线程局部对象就是锁吗？** 不是，它隔离线程属性，不协调共享文件或全局字典。

**问：协程里用它能隔离每个请求吗？** 同一线程中的多个协程会共享该线程状态，协程上下文通常需要不同机制。

## 实际案例与代码

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 记录文件锁重入深度

[s13_agent_teams/code.py，74–81行](../../应用侧/自动化与工具助手/通用AgentHarness/s13_agent_teams/code.py#L74-L81)

```python
depth = getattr(_task_store_state, "depth", 0)
if depth == 0:
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    handle = TASK_LOCK_PATH.open("a+", encoding="utf-8")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    _task_store_state.handle = handle
_task_store_state.depth = depth + 1
try:
```

每个线程单独记录depth与文件句柄，仅最外层获取文件锁；_task_store_state在模块中由threading.local创建。

## 易错点与追问

线程池线程会被复用，需在适当范围清理局部属性。不要混淆thread-local和进程隔离。
