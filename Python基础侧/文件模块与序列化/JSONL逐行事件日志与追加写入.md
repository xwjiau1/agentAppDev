# JSONL逐行事件日志与追加写入

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

JSONL每行是一个独立JSON值，适合追加事件并逐行读取。它不是把多个JSON对象直接连成一个合法JSON文档。

## 面试问答

**问：进程崩溃可能留下什么？** 最后一行可能不完整，读取方需要处理损坏尾行。

**问：open("a")足以保证多人消息一致性吗？** 不足，仍需定义锁、写入粒度与跨进程协调。

## 实际案例与代码

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 邮箱追加记录

[s13_agent_teams/code.py，883–885行](../../应用侧/自动化与工具助手/通用AgentHarness/s13_agent_teams/code.py#L883-L885)

```python
with self._path(to_agent).open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(msg, ensure_ascii=True) + "\n")
self._changed.notify_all()
```

每条消息先dumps，再追加换行；Condition锁协调当前MessageBus实例的线程，notify_all提示新记录到达。

## 易错点与追问

不要承诺追加写入等于事务或消息只投递一次。读取、清空和确认协议也决定是否丢失或重复处理。
