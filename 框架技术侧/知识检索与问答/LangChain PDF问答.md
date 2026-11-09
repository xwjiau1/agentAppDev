# LangChain PDF问答

## 技术实现

PDF文本经切分后向量化，由FAISS召回片段，再交给stuff问答链生成回答。页码映射在索引外单独维护。

## 应用思路

用于本地文档问答；页码可辅助核对答案，但当前采用启发式文本定位，不能代替严格的字符偏移映射。

## 代码解析

### 切片与入库

[PDF问答与页码溯源](../../应用侧/知识问答与文档处理/PDF问答与页码溯源/案例说明.md) · [chatpdf-faiss.py，50–68行](../../应用侧/知识问答与文档处理/PDF问答与页码溯源/chatpdf-faiss.py#L50-L68)

```python
text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ".", " ", ""],
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

# 分割文本
chunks = text_splitter.split_text(text)
print(f"文本被分割成 {len(chunks)} 个块。")

# 创建嵌入模型
embeddings = DashScopeEmbeddings(
    model="text-embedding-v1",
    dashscope_api_key=DASHSCOPE_API_KEY,
)

# 从文本块创建知识库
knowledgeBase = FAISS.from_texts(chunks, embeddings)
```

chunk_size=1000、chunk_overlap=200按字符长度切分；重叠保留相邻上下文，FAISS.from_texts同时生成向量和存储文本。

### 检索与生成

[PDF问答与页码溯源](../../应用侧/知识问答与文档处理/PDF问答与页码溯源/案例说明.md) · [chatpdf-faiss.py，199–213行](../../应用侧/知识问答与文档处理/PDF问答与页码溯源/chatpdf-faiss.py#L199-L213)

```python
docs = knowledgeBase.similarity_search(query,k=2)

# 加载问答链
chain = load_qa_chain(llm, chain_type="stuff")

# 准备输入数据
input_data = {"input_documents": docs, "question": query}

# 使用回调函数跟踪API调用成本
with get_openai_callback() as cost:
    # 执行问答链
    response = chain.invoke(input=input_data)
    print(f"查询已处理。成本: {cost}")
    print(response["output_text"])
    print("来源:")
```

k=2仅取两段；stuff把检索片段放入一次问答上下文。input_documents提供材料，question提供问题。get_openai_callback包裹Tongyi调用并不保证能准确计算其费用。

