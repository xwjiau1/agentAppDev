# Tongyi检索上下文生成

## 技术实现

直接调用版本不再使用load_qa_chain，而是取FAISS片段并拼成上下文提示词，交给Tongyi.invoke。

## 应用思路

适合需要直接控制检索材料格式和回答指令的场景；k增加会提升输入长度，应结合片段质量控制。

## 代码解析

### 检索后拼接提示词

[PDF问答与直接提示词生成](../../应用侧/知识问答与文档处理/PDF问答与直接提示词生成/案例说明.md) · [chatpdf-faiss.py，197–214行](../../应用侧/知识问答与文档处理/PDF问答与直接提示词生成/chatpdf-faiss.py#L197-L214)

```python
    docs = knowledgeBase.similarity_search(query,k=10)

    # 构建上下文
    context = "\n\n".join([doc.page_content for doc in docs])

    # 构建提示
    prompt = f"""根据以下上下文回答问题:

{context}

问题: {query}"""

    # 直接调用 LLM
    response = llm.invoke(prompt)
    print(response)
    print("来源:")

    # 记录唯一的页码
```

k=10取最多十段，join将文本拼成上下文，再加入question；invoke直接发送字符串。与问答链版本相比，主要差异在提示词构造和调用接口，向量入库方式相同。

