# Harness Todo状态校验

## 技术实现

TodoManager把模型提交的列表或字符串规范化后校验，限制项目数、必填字段和进行中数量，再替换当前清单。

## 应用思路

短会话内可用Todo展示执行计划；与跨进程持久任务分开建模，避免把UI清单当成可靠任务数据库。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 输入规范化

[s05_todo_write/code.py，125–138行](../../应用侧/自动化与工具助手/通用AgentHarness/s05_todo_write/code.py#L125-L138)

```python
def update(self, todos: list | str) -> str:
    if isinstance(todos, str):
        try:
            todos = json.loads(todos)
        except json.JSONDecodeError:
            try:
                todos = ast.literal_eval(todos)
            except (SyntaxError, ValueError) as e:
                raise ValueError("todos must be a list or JSON array string") from e

    if not isinstance(todos, list):
        raise ValueError("todos must be a list")
    if len(todos) > 20:
        raise ValueError("Max 20 todos allowed")
```

先尝试JSON，失败后尝试Python字面量；两者都失败时抛带异常链的ValueError，随后检查必须为列表与数量上限。

### 逐项校验

[s05_todo_write/code.py，140–154行](../../应用侧/自动化与工具助手/通用AgentHarness/s05_todo_write/code.py#L140-L154)

```python
validated = []
in_progress_count = 0
for index, todo in enumerate(todos):
    if not isinstance(todo, dict):
        raise ValueError(f"todos[{index}] must be an object")

    content = str(todo.get("content", "")).strip()
    status = str(todo.get("status", "pending")).lower()
    if not content:
        raise ValueError(f"todos[{index}] requires content")
    if status not in ("pending", "in_progress", "completed"):
        raise ValueError(f"todos[{index}] has invalid status '{status}'")
    if status == "in_progress":
        in_progress_count += 1
    validated.append({"content": content, "status": status})
```

检查每项为dict、内容非空、状态属于允许值，再累积规范化对象。

## 实现差异与边界

字符串解析兼容性不代表允许任意表达式；literal_eval不执行一般代码，但不能对不受限的大输入承诺资源安全。
