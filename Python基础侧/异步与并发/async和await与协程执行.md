# async和await与协程执行

> 复习优先级：必背。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

async def定义协程函数；调用后得到协程对象，需要await、任务调度或事件循环驱动。await在等待可等待对象时让出控制，是否真正挂起取决于该对象。

## 面试问答

**问：async函数里调用阻塞请求会自动异步吗？** 不会，同步阻塞仍会占住事件循环线程。

**问：await等于并行吗？** 不等于；连续await通常仍按先后完成，需要任务调度才能让多个协程并发推进。

## 实际案例与代码

[OpenManus通用任务助手](../../应用侧/自动化与工具助手/OpenManus通用任务助手/案例说明.md) · [manus.py，64–70行](../../应用侧/自动化与工具助手/OpenManus通用任务助手/app/agent/manus.py#L64-L70)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
async def create(cls, **kwargs) -> "Manus":
    """工厂方法，创建并正确初始化 Manus 实例。"""
    instance = cls(**kwargs)
    await instance.initialize_mcp_servers()
    instance._initialized = True
    return instance
```

cls(**kwargs)仍是普通构造，await initialize_mcp_servers完成可等待的连接准备；调用方必须await这个工厂才能拿到完成初始化的实例。

## 易错点与追问

不要在已有事件循环中随意调用asyncio.run。异步主要描述协作调度，不保证CPU计算更快。
