# BGE重排与多查询召回

## 技术实现

查询扩展负责增加候选覆盖，重排模型对原始查询与每个候选联合编码，负责重新排序。

## 应用思路

先扩大候选，再精排到较小上下文，可分开调节召回数量与最终段落数。

## 代码解析

### RRF 候选接入 BGE Reranker v2 M3

混合检索 RAG 使用固定修订的 `BAAI/bge-reranker-v2-m3` 对原查询和 RRF 候选正文联合打分，关闭分数归一化。Java 校验候选 ID 的完整性，通过 ID 重新关联分数与原候选 payload，再执行稳定降序排序，最后截取 `topK`。模型超时和结果校验失败时，保留 RRF 的排序和评分类型。阈值若依赖分数绝对值，需要对目标语料单独标定。[Python 打分](../../incubator/hybrid-rag/encoder/rag_models/models.py#L103-L114) · [Java 重排](../../incubator/hybrid-rag/rag-api/src/main/java/dev/agent/rag/SearchService.java#L65-L83) · [评估入口](../../incubator/hybrid-rag/sample/evaluate.py)

### 联合编码打分

[BGE交叉编码重排](../../application/模型与服务示例/BGE交叉编码重排/案例说明.md) · [beg-reranker.py，18–26行](../../application/模型与服务示例/BGE交叉编码重排/beg-reranker.py#L18-L26)

```python
tokenizer = AutoTokenizer.from_pretrained('/root/autodl-tmp/models/BAAI/bge-reranker-large')
model = AutoModelForSequenceClassification.from_pretrained('/root/autodl-tmp/models/BAAI/bge-reranker-large')
model.eval()

pairs = [['what is panda?', 'The giant panda is a bear species endemic to China.']]
inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors='pt')
scores = model(**inputs).logits.view(-1).float()
print(scores)  # 输出相关性分数
```

pairs包含问题与文档，padding对齐批次，truncation限制长度，logits是重排相关性分数。

### 候选合并后重排

[多查询混合检索与重排问答](../../application/知识问答与文档处理/多查询混合检索与重排问答/案例说明.md) · [4-chatpdf-faiss-HybridSearch-Rerank.py，264–284行](../../application/知识问答与文档处理/多查询混合检索与重排问答/4-chatpdf-faiss-HybridSearch-Rerank.py#L264-L284)

```python
queries = generate_multi_queries(query, llm)
print(f"生成的查询变体: {queries}")

# 第一阶段: 多查询混合检索，获取更多候选
seen_contents = set()
candidate_docs = []

for q in queries:
    docs = hybrid_retriever.search(q, k=initial_k)
    for doc in docs:
        if doc.page_content not in seen_contents:
            seen_contents.add(doc.page_content)
            candidate_docs.append(doc)

print(f"初步召回 {len(candidate_docs)} 个候选文档")

# 第二阶段: Rerank精排
reranked_docs = reranker.rerank(query, candidate_docs, top_k=final_k)
print(f"Rerank后保留 {len(reranked_docs)} 个文档")

return reranked_docs
```

initial_k用于每个查询变体的召回数；按page_content去重，最终用原query重排到final_k，避免仅按改写问题解释用户意图。

