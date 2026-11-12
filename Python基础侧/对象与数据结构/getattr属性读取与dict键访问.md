# getattr属性读取与dict键访问

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

getattr(obj, name, default)读取对象属性；dict.get读取映射键，两者不等价。兼容不同数据形态时应先明确协议再选择访问方式。

## 面试问答

**问：getattr能读取dict的"type"键吗？** 不能，键不是普通属性；需要block.get("type")。

**问：getattr只是在字典里查值吗？** 不是，可能触发property或自定义属性访问逻辑，甚至有副作用。

## 实际案例与代码

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 兼容dict和SDK对象

[s17_goal_loop/code.py，98–102行](../../应用侧/自动化与工具助手/通用AgentHarness/s17_goal_loop/code.py#L98-L102)

```python
def _block_type(block: Any) -> str | None:
    if isinstance(block, dict):
        return block.get("type")
    return getattr(block, "type", None)
```

dict走键访问，SDK块对象走属性访问，缺失时返回None；这个适配函数把差异集中处理。

## 易错点与追问

默认值只处理属性缺失，不意味着属性getter内部的任意异常都会变成默认值。不要把兼容适配理解为不需类型校验。
