# DashScope多模态检索

## 技术实现

文档、图片、视频分别编码到统一Embedding空间，FAISS保存向量，元数据标识类型和原始资源。查询先检索，再按媒体意图筛选。

## 应用思路

回答文本和展示媒体可以分开处理：文本作为生成依据，图片视频作为相关附件；必须让资源路径在运行环境可解析。

## 代码解析

### 统一入库并保存元数据

[主题乐园多模态知识问答](../../应用侧/知识问答与文档处理/主题乐园多模态知识问答/案例说明.md) · [4-disney_build_index.py，204–217行](../../应用侧/知识问答与文档处理/主题乐园多模态知识问答/4-disney_build_index.py#L204-L217)

```python
# 创建FAISS索引
if all_vectors:
    dim = len(all_vectors[0])
    print(f"\n向量维度: {dim}")

    index = faiss.IndexFlatL2(dim)
    index.add(np.array(all_vectors).astype('float32'))

    # 保存索引
    faiss.write_index(index, INDEX_FILE)
    print(f"索引已保存: {INDEX_FILE}")

    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata_store, f, ensure_ascii=False, indent=2)
```

维度来自第一条向量；IndexFlatL2保存float32向量，JSON元数据与向量插入顺序一一对应。

### 按内容类型筛选

[主题乐园多模态知识问答](../../应用侧/知识问答与文档处理/主题乐园多模态知识问答/案例说明.md) · [5-disney_query.py，115–126行](../../应用侧/知识问答与文档处理/主题乐园多模态知识问答/5-disney_query.py#L115-L126)

```python
# 取top-k文本结果
top_results = [r for r in results if r["metadata"]["type"] == "text"][:k]

# 如果需要图片，找距离<3的图片中距离最小的Top1
matched_image = None
if want_image:
    image_results = [r for r in results if r["metadata"]["type"] == "image" and r["distance"] < MEDIA_DISTANCE_THRESHOLD]
    if image_results:
        # 按距离排序，取距离最小的Top1
        image_results.sort(key=lambda x: x["distance"])
        matched_image = image_results[0]
        print(f"  -> 匹配到图片: {matched_image['metadata']['path']} (距离: {matched_image['distance']:.4f}, 相似度: {matched_image['similarity']:.4f})")
```

k控制文本段落数；媒体另用距离阈值筛选后选最接近的一条。阈值针对当前向量距离设置，不是概率。

