# LangChain多文件问答

## 技术实现

LangChain版显式控制文档加载、切分、FAISS检索以及提示词生成。持久化缓存存在时优先加载，否则从docs构建。

## 应用思路

适合需要控制检索粒度和上下文格式的文档应用，缓存路径应与模型和数据版本绑定。

## 代码解析

### 上下文约束与生成链

[多框架多文件智能问答](../../应用侧/知识问答与文档处理/多框架多文件智能问答/案例说明.md) · [langchain-agent-multi-files.py，91–104行](../../应用侧/知识问答与文档处理/多框架多文件智能问答/langchain-agent-multi-files.py#L91-L104)

```python
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个乐于助人的AI助手。
根据以下上下文内容回答用户的问题。如果上下文中没有相关信息，请如实说明。
你总是用中文回复用户。

上下文内容:
{context}"""),
        ("human", "{question}")
    ])

    # 创建问答链 (LCEL 管道语法)
    qa_chain = qa_prompt | llm | StrOutputParser()

    return qa_chain
```

context提供检索证据，question提供用户问题；StrOutputParser取出文本。没有证据时的回答约束写在system消息。

