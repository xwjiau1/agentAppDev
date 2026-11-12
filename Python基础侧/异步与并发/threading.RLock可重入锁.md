# threading.RLock可重入锁

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

RLock允许同一线程重复取得同一把锁，每次成功取得都要对应释放。适用于锁内再调用同样需要锁的辅助函数。

## 面试问答

**问：RLock是否让多个线程同时进入？** 不会，可重入只针对同一线程。

**问：普通Lock能安全替换这里的RLock吗？** 若受保护调用链再次请求同一把锁，可能死锁，应先分析嵌套路径。

## 实际案例与代码

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 条件变量共享可重入锁

[s13_agent_teams/code.py，856–857行](../../应用侧/自动化与工具助手/通用AgentHarness/s13_agent_teams/code.py#L856-L857)

```python
self._lock = threading.RLock()
self._changed = threading.Condition(self._lock)
```

MessageBus将RLock交给Condition；等待函数持有Condition时又调用peek，而peek也会进入self._lock，存在重入需求。

## 易错点与追问

可重入并不解决多把锁之间的死锁。锁顺序、等待条件与持锁范围仍需明确。
