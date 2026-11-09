# FAISS向量与元数据检索

## 技术实现

文本向量进入FAISS索引，搜索返回向量ID，再用ID取回原文与业务字段。当前实现采用L2距离，数值越小表示越接近。

## 应用思路

适合把语义搜索结果与文档来源、分类等结构化字段关联。向量ID与元数据位置必须保持一致。

## 代码解析

### 构造带ID索引

[Embedding与FAISS元数据检索](../../应用侧/基础技术示例/Embedding与FAISS元数据检索/案例说明.md) · [2-embedding-faiss-元数据.py，80–98行](../../应用侧/基础技术示例/Embedding与FAISS元数据检索/2-embedding-faiss-元数据.py#L80-L98)

```python
dimension = 1024  # 向量维度
k = 3             # 查找最近的3个邻居

# 创建一个基础的L2距离索引
index_flat_l2 = faiss.IndexFlatL2(dimension)

# 使用IndexIDMap来包装基础索引，能够映射我们自定义的ID
# 这就是关联向量和元数据的关键！
index = faiss.IndexIDMap(index_flat_l2)

# 将向量和它们对应的ID添加到索引中
index.add_with_ids(vectors_np, vector_ids_np)

print(f"\nFAISS 索引已成功创建，共包含 {index.ntotal} 个向量。")


# Step5. 执行搜索并检索元数据
query_text = "我想了解一下迪士尼门票的退款流程"
print(f"\n正在为查询文本生成向量: '{query_text}'")
```

dimension要与embedding输出维度一致；IndexIDMap保留自定义ID，add_with_ids一次加入向量与ID。float32转换满足FAISS输入要求。

### 检索并还原来源

[Embedding与FAISS元数据检索](../../应用侧/基础技术示例/Embedding与FAISS元数据检索/案例说明.md) · [2-embedding-faiss-元数据.py，114–131行](../../应用侧/基础技术示例/Embedding与FAISS元数据检索/2-embedding-faiss-元数据.py#L114-L131)

```python
distances, retrieved_ids = index.search(query_vector, k)

# Step6. 展示结果
print("\n--- 搜索结果 ---")
# `retrieved_ids[0]` 包含与查询最相似的k个向量的ID
for i in range(k):
    doc_id = retrieved_ids[0][i]

    # 检查ID是否有效
    if doc_id == -1:
        print(f"\n排名 {i+1}: 未找到更多结果。")
        continue

    # 使用ID从我们的元数据存储中检索信息
    retrieved_doc = metadata_store[doc_id]

    print(f"\n--- 排名 {i+1} (相似度得分/距离: {distances[0][i]:.4f}) ---")
    print(f"ID: {doc_id}")
```

k控制返回条数；返回的-1表示没有对应邻居。代码以ID作列表下标取回文档，若向量生成中途失败，原循环ID与metadata_store追加位置可能不一致，运行前应核查。

