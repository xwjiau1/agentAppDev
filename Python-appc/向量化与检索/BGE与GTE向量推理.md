# BGE与GTE向量推理

## 技术实现

BGE-M3通过dense_vecs取密集向量，GTE通过查询指令区分查询与文档编码；低层GTE实现显式处理最后有效token池化与归一化。

## 应用思路

检索时必须对查询与语料使用匹配的编码模型和维度，避免不同模型的向量混用。

## 代码解析

### BGE-M3 联合编码

混合检索 RAG 的 `/encode` 在单次前向中打开 `return_dense` 与 `return_sparse`，得到 `dense_vecs` 和 `lexical_weights`。模型 tokenizer 在前向前检查含特殊 token 的输入长度。服务按输入顺序组装返回，将词权重字典的键化为整数 token ID，按 ID 排序并拆为等长的 `indices` 和 `values`。空词权重保留为空数组，由检索端决定如何处理。`zip(..., strict=True)` 会在模型输出掉项时抛出异常，防止批次向量和出处错位。[联合编码源码](../../incubator/hybrid-rag/encoder/rag_models/models.py#L75-L91) · [稀疏向量序列化](../../incubator/hybrid-rag/encoder/rag_models/models.py#L40-L44)

### 批量编码

[BGE与GTE文本向量推理](../../application/模型与服务示例/BGE与GTE文本向量推理/案例说明.md) · [bge-m3使用.py，24–30行](../../application/模型与服务示例/BGE与GTE文本向量推理/bge-m3使用.py#L24-L30)

```python
embeddings_1 = model.encode(sentences_1, 
                            batch_size=12, 
                            max_length=8192, # If you don't need such a long length, you can set a smaller value to speed up the encoding process.
                            )['dense_vecs']
embeddings_2 = model.encode(sentences_2)['dense_vecs']
similarity = embeddings_1 @ embeddings_2.T
print(similarity)
```

batch_size决定批次大小，max_length限制输入长度，dense_vecs选择密集向量；矩阵乘法得到查询与文档两两分数。

### 查询指令

[BGE与GTE文本向量推理](../../application/模型与服务示例/BGE与GTE文本向量推理/案例说明.md) · [gte-qwen2-使用1.py，32–37行](../../application/模型与服务示例/BGE与GTE文本向量推理/gte-qwen2-使用1.py#L32-L37)

```python
query_embeddings = model.encode(queries, prompt_name="query")
document_embeddings = model.encode(documents)

scores = (query_embeddings @ document_embeddings.T) * 100
print(scores.tolist())
# [[70.00668334960938, 8.184843063354492], [14.62419319152832, 77.71407318115234]]
```

prompt_name="query"只用于查询端，文档直接encode。乘100只缩放数值，不代表经过概率校准。

### 池化有效token

[BGE与GTE文本向量推理](../../application/模型与服务示例/BGE与GTE文本向量推理/案例说明.md) · [gte-qwen2-使用2.py，17–29行](../../application/模型与服务示例/BGE与GTE文本向量推理/gte-qwen2-使用2.py#L17-L29)

```python
def last_token_pool(last_hidden_states: Tensor,
                 attention_mask: Tensor) -> Tensor:
    # 检查是否为左侧填充（即所有序列最后一个位置都有效）
    left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
    if left_padding:
        # 如果是左侧填充，直接返回最后一个位置的隐藏状态
        return last_hidden_states[:, -1]
    else:
        # 如果是右侧填充，计算每个序列的实际长度（减1是因为索引从0开始）
        sequence_lengths = attention_mask.sum(dim=1) - 1
        batch_size = last_hidden_states.shape[0]
        # 返回每个序列最后一个有效token的隐藏状态
        return last_hidden_states[torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths]
```

attention_mask确定padding方式；右padding时按每行有效长度取最后一个token，避免拿到填充表示。

