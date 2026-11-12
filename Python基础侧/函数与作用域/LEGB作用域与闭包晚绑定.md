# LEGB作用域与闭包晚绑定

> 复习优先级：必背。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

名字按局部、外层函数、模块全局、内建作用域解析。内部函数引用外层局部名字可形成闭包，通常保存的是绑定关系，调用时取当前值。

## 面试问答

**问：循环中创建lambda为什么常取最后一个值？** 多个闭包引用同一循环变量绑定，调用时循环已结束。

**问：global与nonlocal的区别？** global声明模块全局绑定；nonlocal声明最近的已有外层函数绑定，不能凭空创建。

## 实际案例与代码

[企业报告问答与回归评估](../../应用侧/知识问答与文档处理/企业报告问答与回归评估/案例说明.md) · [reranking.py，208–216行](../../应用侧/知识问答与文档处理/企业报告问答与回归评估/src/reranking.py#L208-L216)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
def process_batch(batch):
    # 批量重排
    texts = [doc['text'] for doc in batch]
    rankings = self.get_rank_for_multiple_blocks(query, texts)
    results = []
    block_rankings = rankings.get('block_rankings', [])

    if len(block_rankings) < len(batch):
        print(f"\nWarning: Expected {len(batch)} rankings but got {len(block_rankings)}")
```

process_batch使用外层query与self，不必把它们逐个作为形参传入。这里说明闭包机制；片段没有循环创建函数，不应声称它已经存在晚绑定bug。

## 易错点与追问

闭包捕获可变对象时可能延长其生命周期。默认参数可在定义时绑定当前对象，但并不深拷贝对象。

## Harness补充案例：循环中的绑定修复

[s14_mcp_plugin/code.py，357–360行](../../应用侧/自动化与工具助手/通用AgentHarness/s14_mcp_plugin/code.py#L357-L360)

```python
handlers[prefixed] = (
    lambda *, client=server, tool=raw_name, **kwargs:
    client.call_tool(tool, kwargs)
)
```

lambda的client=server、tool=raw_name在创建函数时取得当前对象。否则函数体直接引用循环变量，循环结束后多个处理器可能都调用最后一个插件。默认参数固定的是对象引用，不是深拷贝对象。

