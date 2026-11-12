# dataclass数据类与asdict序列化

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

dataclass根据声明字段生成初始化、repr和相等比较等方法。asdict将数据类实例按字段递归转换为字典，供JSON等编码使用。

## 面试问答

**问：dataclass会检查所有类型注解吗？** 不会自动按注解验证业务字段。

**问：asdict等同于vars吗？** 不等同，asdict处理数据类字段并递归转换嵌套结构；vars读取对象命名空间。

## 实际案例与代码

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 任务数据类

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

Task的id、subject、status等都是声明字段；owner允许None，但没有默认值，因此构造时仍需提供。

### 转字典后持久化

[s10_task_system/code.py，181–183行](../../应用侧/自动化与工具助手/通用AgentHarness/s10_task_system/code.py#L181-L183)

```python
    json.dumps(asdict(task), indent=2),
    encoding="utf-8",
)
```

先asdict把任务变成dict，再dumps编码文本；JSON还要求字段值可编码。

## 易错点与追问

如果类手写__init__，dataclass不一定替你生成初始化逻辑。不能将其与Pydantic的运行时验证混淆。
