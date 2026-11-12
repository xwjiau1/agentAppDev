# dataclasses.field默认工厂

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

field(default_factory=fn)为每个实例在需要默认值时调用工厂。它不同于在类定义时立即计算一个默认值。

## 面试问答

**问：`default=time.time()`有什么问题？** 时间会在定义类时固定，而不是创建实例时分别取得。

**问：列表默认值如何处理？** 通常用default_factory=list，每个实例独立创建列表。

## 实际案例与代码

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 实例创建时间

[s13_agent_teams/code.py，931–931行](../../应用侧/自动化与工具助手/通用AgentHarness/s13_agent_teams/code.py#L931-L931)

```python
created_at: float = field(default_factory=time.time)
```

传入time.time函数本身，数据类初始化时调用它；这里是计算时间的工厂，不是提前取得的时间戳。

## 易错点与追问

默认工厂没有参数，不能直接假设能访问self。它解决默认值创建时机，不自动让嵌套外部对象彼此隔离。
