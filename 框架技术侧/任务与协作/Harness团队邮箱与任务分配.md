# Harness团队邮箱与任务分配

## 技术实现

团队实现使用持久邮箱传递消息，任务共享状态记录分配，线程间用锁协调；与临时子代理仅返回摘要的机制不同。

## 应用思路

长期协作者需要明确消息来源、任务领取与完成确认，不能仅创建线程后假定团队协议成立。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 任务存储的重入边界

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

RLock保护线程内重入，thread-local记录深度；最外层取得文件锁，最外层退出时释放。

### 邮箱发送

[s13_agent_teams/code.py，876–887行](../../应用侧/自动化与工具助手/通用AgentHarness/s13_agent_teams/code.py#L876-L887)

```python
def send(self, from_agent: str, to_agent: str, content: str,
         msg_type: str = "message", metadata: dict | None = None):
    msg = {"from": from_agent, "to": to_agent,
           "content": content, "type": msg_type,
           "ts": time.time(), "metadata": metadata or {}}
    with self._changed:
        MAILBOX_DIR.mkdir(parents=True, exist_ok=True)
        with self._path(to_agent).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(msg, ensure_ascii=True) + "\n")
        self._changed.notify_all()
    print(f"  [bus] {from_agent} -> {to_agent}: "
          f"({msg_type}) {content[:50]}")
```

send实现具体收件人与消息落盘；消息格式和消费协议决定能否安全重放，应沿read/consume函数继续核对。

## 实现差异与边界

fcntl为Unix依赖；文件锁需要所有写入方遵守，不能替代分布式数据库事务。
