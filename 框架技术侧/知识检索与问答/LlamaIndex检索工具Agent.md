# LlamaIndex检索工具Agent

## 技术实现

LlamaIndex版使用VectorStoreIndex构建索引，QueryEngine负责检索并合成结果，FunctionTool将查询引擎暴露给ReActAgent。

## 应用思路

需要让Agent选择何时查文档时，可把检索作为工具。QueryEngine可能已经调用模型生成，Agent再整合时应关注多次调用成本。

## 代码解析

### 查询引擎包装成工具

[多框架多文件智能问答](../../应用侧/知识问答与文档处理/多框架多文件智能问答/案例说明.md) · [llamaindex-agent-multi-files.py，91–114行](../../应用侧/知识问答与文档处理/多框架多文件智能问答/llamaindex-agent-multi-files.py#L91-L114)

```python
    retriever = index.as_retriever(similarity_top_k=5)

    # 创建查询引擎（用于检索工具）
    query_engine = index.as_query_engine(similarity_top_k=5)

    # 定义系统提示词
    system_instruction = '''你是一个乐于助人的AI助手。
你可以从给定的文档中检索相关信息来回答用户的问题。
你总是用中文回复用户。'''

    # 创建检索工具（用于查询文档）
    def retrieve_documents(query: str) -> str:
        """从文档中检索相关信息"""
        response = query_engine.query(query)
        return str(response)

    retrieve_tool = FunctionTool.from_defaults(fn=retrieve_documents)

    # 创建智能体（新版 API）
    agent = ReActAgent(
        tools=[retrieve_tool],
        llm=llm,
        system_prompt=system_instruction,
    )
```

similarity_top_k=5控制候选数；retrieve_documents调用query_engine.query并返回字符串。FunctionTool从函数说明与参数构建schema，ReActAgent使用该工具。

