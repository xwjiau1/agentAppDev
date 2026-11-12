# Harness任务绑定Git Worktree隔离

## 技术实现

任务在创建worktree之前校验名称、归属和已有绑定，后续把工具cwd解析到分配给任务的工作目录。

## 应用思路

并行改不同文件或分支时可以减少工作区相互覆盖，但合并冲突和共享外部资源仍需管理。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 创建前核验

[s13_agent_teams/code.py，489–510行](../../应用侧/自动化与工具助手/通用AgentHarness/s13_agent_teams/code.py#L489-L510)

```python
def create_worktree(name: str, task_id: str) -> str:
    """Create and bind a dedicated worktree after all inputs validate."""
    error = validate_worktree_name(name)
    if error:
        return f"Error: {error}"
    try:
        path = _worktree_path(name)
        task_path = _task_path(task_id)
    except ValueError as exc:
        return f"Error: {exc}"
    branch = _worktree_branch(name)

    with task_lock:
        if not task_path.exists():
            return f"Error: Task {task_id} not found"
        task = load_task(task_id)
        if task.status != "pending" or task.owner is not None:
            return f"Error: Task {task_id} must be pending and unowned"
        if task.worktree:
            return f"Error: Task {task_id} already uses worktree '{task.worktree}'"
        if any(t.worktree == name for t in list_tasks() if t.id != task_id):
            return f"Error: Worktree '{name}' is already bound to another task"
```

要求pending且未被领取，拒绝重复绑定与已有目录；校验后才进入Git创建逻辑。

## 实现差异与边界

worktree隔离文件修改，不隔离网络、数据库、密钥或主机权限。创建和删除会改变Git及本地目录，本次只阅读代码，没有执行。
