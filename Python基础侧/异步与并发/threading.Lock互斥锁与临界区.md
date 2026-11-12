# threading.Lock互斥锁与临界区

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

Lock把共享状态更新围成临界区。同一时刻只允许持锁线程进入受保护代码；with负责异常路径下释放锁。

## 面试问答

**问：为什么counter加一还需要锁？** 任务ID生成与写入任务表是整体约束，不能只看一条赋值是否恰好原子。

**问：所有读取都可以不加锁吗？** 取决于一致性要求；复合读改写需遵守同一协议。

## 实际案例与代码

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 任务编号与注册

[s11_background_tasks/code.py，363–370行](../../应用侧/自动化与工具助手/通用AgentHarness/s11_background_tasks/code.py#L363-L370)

```python
with self._lock:
    self._counter += 1
    task_id = f"bg_{self._counter:04d}"
    self.tasks[task_id] = {
        "tool_use_id": block.id,
        "command": command,
        "status": "running",
    }
```

在一把锁内分配唯一编号并登记running状态，使其他线程不会看到半注册任务。

## 易错点与追问

锁只约束使用同一把锁的参与者。不要在长网络请求期间无必要地持锁，也不能用线程锁解决多进程竞争。
