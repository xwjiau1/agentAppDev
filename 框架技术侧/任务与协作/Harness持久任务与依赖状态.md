# Harness持久任务与依赖状态

## 技术实现

TaskStore把任务持久化到工作区，任务记录status、owner和blockedBy。领取任务前检查状态及未完成依赖。

## 应用思路

跨轮次任务需要持久状态与依赖关系；单会话Todo不能替代领取和完成协议。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 任务数据结构

[s10_task_system/code.py，74–81行](../../应用侧/自动化与工具助手/通用AgentHarness/s10_task_system/code.py#L74-L81)

```python
@dataclass
class Task:
    id: str
    subject: str
    description: str
    status: str
    owner: str | None
    blockedBy: list[str]
```

dataclass定义存储字段，但状态合法性和依赖关系仍需业务代码校验。

### 领取任务

[s10_task_system/code.py，240–251行](../../应用侧/自动化与工具助手/通用AgentHarness/s10_task_system/code.py#L240-L251)

```python
def claim_task(task_id: str, owner: str = "agent") -> str:
    task = load_task(task_id)
    if task.status != "pending":
        return f"Task {task_id} is {task.status}, cannot claim"
    dependencies = incomplete_dependencies(task)
    if dependencies:
        return f"Blocked by: {dependencies}"
    task.owner = owner
    task.status = "in_progress"
    TASKS.save(task)
    print(f"  [claim] {task.subject} -> in_progress (owner: {owner})")
    return f"Claimed {task.id} ({task.subject})"
```

只有pending且依赖已完成的任务才能领取；写owner和in_progress后保存。

## 实现差异与边界

单模块示例的读改写不等于跨进程原子事务；团队版本另外增加锁与分配版本。不要把文件存在视为任务状态一致。
