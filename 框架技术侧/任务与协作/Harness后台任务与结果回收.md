# Harness后台任务与结果回收

## 技术实现

BackgroundManager让Shell执行在线程中推进，前台返回任务ID；后台结果先暂存，下一轮再回收为通知。

## 应用思路

长命令可转后台，让模型继续其他步骤，同时需要终止、超时和重复回收控制。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 注册后台执行

[s11_background_tasks/code.py，372–384行](../../应用侧/自动化与工具助手/通用AgentHarness/s11_background_tasks/code.py#L372-L384)

```python
thread = threading.Thread(
    target=self._run,
    args=(task_id, command),
    daemon=True,
)
try:
    thread.start()
except Exception:
    with self._lock:
        self.tasks.pop(task_id, None)
    raise
print(f"  [background] started {task_id}: {command[:60]}")
return task_id
```

daemon线程启动失败时回滚任务表记录，异常继续传播；成功后返回ID。

### 锁内领取结果

[s11_background_tasks/code.py，403–412行](../../应用侧/自动化与工具助手/通用AgentHarness/s11_background_tasks/code.py#L403-L412)

```python
def collect(self) -> list[str]:
    with self._lock:
        ready = []
        for task_id in self._ready:
            task = self.tasks.pop(task_id, None)
            result = self.results.pop(task_id, "")
            if task is not None:
                ready.append((task_id, task, result))
        self._ready.clear()
```

锁内把就绪任务移出共享映射并清空_ready，锁外再格式化通知，减少锁占用。

## 实现差异与边界

后台线程与实际Shell子进程不是一回事；只退出daemon线程不能保证子进程被清理，需同时阅读进程组终止逻辑。
