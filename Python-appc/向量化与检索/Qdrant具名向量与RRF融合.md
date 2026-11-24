# Qdrant 具名向量与 RRF 融合

## 实现机制

一个切片通过稳定 UUID 写入一个 point。`vector.dense` 保存 1024 维余弦向量，`vector.sparse` 保存 BGE-M3 token ID 与词项权重，`payload` 保存正文、文档 ID、页码和切片序号。无稀疏词项时仅提交 `dense`。检索结果用 point ID 关联整份 payload，重排也按同一 ID 连接分数与出处。[项目入口](../../incubator/hybrid-rag/README.md)

## 代码解析

`QdrantIndex.upsert` 将向量与 `Source` 写在同一条 `Point` 中，并用 `wait=true` 等待。`search` 对 `dense` 与 `sparse` 分别提交带 `using`、`filter` 和 `limit` 的 `prefetch`。根 `query` 设置 `fusion: rrf`，只投影引用字段与正文。每路默认候选上限 30，融合保留 20。RRF 按候选的各路名次贡献排序分，可结合余弦相似度与稀疏点积产生的排名。[写入适配器](../../incubator/hybrid-rag/rag-api/src/main/java/dev/agent/rag/QdrantIndex.java#L97-L109) · [查询适配器](../../incubator/hybrid-rag/rag-api/src/main/java/dev/agent/rag/QdrantIndex.java#L117-L150) · [Qdrant 混合查询](https://qdrant.tech/documentation/hybrid-queries/)

`documentId` 以 `keyword` 类型建立 payload 索引，查询把相同过滤放进两条召回支路。过滤索引用于定位候选并估算过滤后的数量。dense 路可使用 HNSW 搜索，Qdrant 可在小 segment 或高选择性过滤下直接计算候选的相似度。sparse 路使用倒排索引计算共享词项的点积。首版示例数据适合验证请求和结果契约，索引性能需用更大的语料衡量。[索引创建](../../incubator/hybrid-rag/rag-api/src/main/java/dev/agent/rag/QdrantIndex.java#L79-L82) · [Qdrant 索引](https://qdrant.tech/documentation/manage-data/indexing/)

## 适用边界

collection metadata 保存语料指纹、模型签名、切片策略和导入状态。查询须使用与入库相同的模型、词表与输出约定。需要 IDF 时应重新验证 BGE 权重和排名效果。使用同一组标注查询对照每路召回和重排，分别记录质量与延迟。[真实 Qdrant 集成测试](../../incubator/hybrid-rag/rag-api/src/test/java/dev/agent/rag/QdrantIntegrationTest.java) · [评估入口](../../incubator/hybrid-rag/sample/evaluate.py)
