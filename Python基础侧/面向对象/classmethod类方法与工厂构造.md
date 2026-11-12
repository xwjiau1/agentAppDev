# classmethod类方法与工厂构造

> 复习优先级：常考。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

classmethod绑定类而非实例，第一个参数通常为cls；适合替代构造入口。staticmethod不自动注入self或cls，只是放在类命名空间中的函数。

## 面试问答

**问：为什么工厂里用cls而不是写死Manus？** 子类调用时cls指向子类，有利于扩展。

**问：classmethod可以是异步吗？** 可以，async def仍返回协程，调用方需要await。

## 实际案例与代码

[OpenManus通用任务助手](../../应用侧/自动化与工具助手/OpenManus通用任务助手/案例说明.md) · [manus.py，63–70行](../../应用侧/自动化与工具助手/OpenManus通用任务助手/app/agent/manus.py#L63-L70)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
@classmethod
async def create(cls, **kwargs) -> "Manus":
    """工厂方法，创建并正确初始化 Manus 实例。"""
    instance = cls(**kwargs)
    await instance.initialize_mcp_servers()
    instance._initialized = True
    return instance
```

create用cls(**kwargs)构建实例，再await连接MCP服务。classmethod只负责类绑定，异步等待来自async def和await。

## 易错点与追问

__init__不能直接写成异步初始化并让普通构造自动await；异步工厂常用于补齐需要await的准备步骤。
