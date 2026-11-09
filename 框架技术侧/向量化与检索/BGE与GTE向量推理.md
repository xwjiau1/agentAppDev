# BGE与GTE向量推理

## 技术实现

BGE-M3通过dense_vecs取密集向量，GTE通过查询指令区分查询与文档编码；低层GTE实现显式处理最后有效token池化与归一化。

## 应用思路

检索时必须对查询与语料使用匹配的编码模型和维度，避免不同模型的向量混用。

## 代码解析

### 批量编码

[BGE与GTE文本向量推理](../../应用侧/模型与服务示例/BGE与GTE文本向量推理/案例说明.md) · [bge-m3使用.py，24–30行](../../应用侧/模型与服务示例/BGE与GTE文本向量推理/bge-m3使用.py#L24-L30)

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

[BGE与GTE文本向量推理](../../应用侧/模型与服务示例/BGE与GTE文本向量推理/案例说明.md) · [gte-qwen2-使用1.py，32–37行](../../应用侧/模型与服务示例/BGE与GTE文本向量推理/gte-qwen2-使用1.py#L32-L37)

```python
query_embeddings = model.encode(queries, prompt_name="query")
document_embeddings = model.encode(documents)

scores = (query_embeddings @ document_embeddings.T) * 100
print(scores.tolist())
# [[70.00668334960938, 8.184843063354492], [14.62419319152832, 77.71407318115234]]
```

prompt_name="query"只用于查询端，文档直接encode。乘100只缩放数值，不代表经过概率校准。

### 池化有效token

[BGE与GTE文本向量推理](../../应用侧/模型与服务示例/BGE与GTE文本向量推理/案例说明.md) · [gte-qwen2-使用2.py，17–29行](../../应用侧/模型与服务示例/BGE与GTE文本向量推理/gte-qwen2-使用2.py#L17-L29)

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

