# BM25与FAISS混合召回

## 技术实现

BM25利用词项匹配，向量检索利用语义距离。示例把两类分数归一化后按权重相加，再统一排序。

## 应用思路

专有名词和语义改写并存的知识库可以组合召回；权重和归一化方式应以标注查询验证。

## 代码解析

### 两路分数归一化

[多查询混合检索与重排问答](../../应用侧/知识问答与文档处理/多查询混合检索与重排问答/案例说明.md) · [3-chatpdf-faiss-HybridSearch.py，67–85行](../../应用侧/知识问答与文档处理/多查询混合检索与重排问答/3-chatpdf-faiss-HybridSearch.py#L67-L85)

```python
# BM25检索
tokenized_query = tokenize_chinese(query)
bm25_scores = self.bm25.get_scores(tokenized_query)

# 归一化BM25分数
max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
bm25_scores_normalized = [s / max_bm25 for s in bm25_scores]

# 向量检索 (获取更多结果用于融合)
vector_results = self.vectorstore.similarity_search_with_score(query, k=len(self.chunks))

# 构建向量分数字典 (距离越小越好，转换为分数)
vector_scores = {}
max_distance = max(score for _, score in vector_results) if vector_results else 1
for doc, distance in vector_results:
    idx = self.chunk_to_idx.get(doc.page_content)
    if idx is not None:
        # 距离转分数: 1 - (distance / max_distance)
        vector_scores[idx] = 1 - (distance / max_distance) if max_distance > 0 else 0
```

jieba分词后计算BM25分数；BM25除以最大值，向量距离通过1-distance/max_distance转换为大分更优。不同查询的分数不适合直接横向比较。

### 加权排序

[多查询混合检索与重排问答](../../应用侧/知识问答与文档处理/多查询混合检索与重排问答/案例说明.md) · [3-chatpdf-faiss-HybridSearch.py，87–97行](../../应用侧/知识问答与文档处理/多查询混合检索与重排问答/3-chatpdf-faiss-HybridSearch.py#L87-L97)

```python
# 融合分数
hybrid_scores = []
for idx in range(len(self.chunks)):
    bm25_score = bm25_scores_normalized[idx]
    vector_score = vector_scores.get(idx, 0)
    combined = self.alpha * vector_score + (1 - self.alpha) * bm25_score
    hybrid_scores.append((idx, combined))

# 排序并返回top-k
hybrid_scores.sort(key=lambda x: x[1], reverse=True)
top_k = hybrid_scores[:k]
```

alpha控制向量权重，1-alpha控制BM25权重；k决定保留数量。代码遍历全部切片，只适合作为小规模实现参考。

