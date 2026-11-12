# 类型注解与Optional和返回类型

> 复习优先级：必背。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

形参后的冒号和箭头描述期望类型，普通Python函数不会仅因注解就自动验证、转换或禁止不匹配值。Optional[T]表示T或None，不代表该参数一定可以省略。

## 面试问答

**问：`x: Optional[str]`可以不传吗？** 只有提供默认值或调用签名允许时才可省略；类型与是否必填是两回事。

**问：Any意味着什么？** 对静态类型检查通常放宽约束，不提供运行时结构保证。

## 实际案例与代码

[多查询混合检索与重排问答](../../应用侧/知识问答与文档处理/多查询混合检索与重排问答/案例说明.md) · [2-chatpdf-faiss-MultiQueryRetriever.py，130–134行](../../应用侧/知识问答与文档处理/多查询混合检索与重排问答/2-chatpdf-faiss-MultiQueryRetriever.py#L130-L134)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
def multi_query_search(query: str, vectorstore, llm, k: int = 4) -> List:
    """
    执行多查询检索，合并去重结果
    """
    queries = generate_multi_queries(query, llm)
```

query:str和k:int说明预期入参，->List说明返回列表；实际参数检查仍由代码或外部工具承担，函数没有自动强制k为整数。

## 易错点与追问

Pydantic等框架可根据注解生成运行时验证，这是框架额外行为。不要把普通dict注解与模型校验混为一谈。
