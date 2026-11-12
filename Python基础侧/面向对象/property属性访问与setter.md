# property属性访问与setter

> 复习优先级：常考。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

property把方法调用暴露为属性访问，可以在读取或赋值时加入计算与校验。它是描述符机制的常见入口。

## 面试问答

**问：`obj.messages`为何能执行函数？** 类上的property在属性访问时调用getter。

**问：只定义getter时能否赋值？** 通常不能直接写入同名property，会抛AttributeError，除非类另有自定义处理。

## 实际案例与代码

[OpenManus通用任务助手](../../应用侧/自动化与工具助手/OpenManus通用任务助手/案例说明.md) · [base.py，188–196行](../../应用侧/自动化与工具助手/OpenManus通用任务助手/app/agent/base.py#L188-L196)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
@property
def messages(self) -> List[Message]:
    """从 agent 的内存中检索消息列表。"""
    return self.memory.messages

@messages.setter
def messages(self, value: List[Message]):
    """设置 agent 内存中的消息列表。"""
    self.memory.messages = value
```

getter返回memory.messages，setter更新同一底层字段。messages不是另一份独立消息副本，读取后原地修改仍可能影响memory。

## 易错点与追问

不要在getter中藏昂贵I/O而让调用方误以为只是取字段；setter和getter应围绕同一个清晰契约。
