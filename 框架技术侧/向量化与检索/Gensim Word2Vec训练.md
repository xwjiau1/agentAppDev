# Gensim Word2Vec训练

## 技术实现

Word2Vec从分词后的句子学习词级向量，使用wv接口比较词语与组合向量。它与整段文本embedding API的输入粒度不同。

## 应用思路

可用于词相似检索和语料表征基线；训练语料需与目标语言和业务词汇相符。

## 代码解析

### 训练与比较

[Word2Vec词向量训练](../../应用侧/模型与服务示例/Word2Vec词向量训练/案例说明.md) · [word_similarity.py，13–24行](../../应用侧/模型与服务示例/Word2Vec词向量训练/word_similarity.py#L13-L24)

```python
model = word2vec.Word2Vec(sentences, vector_size=100, window=3, min_count=1)
#print(model.wv['孙悟空'])
print(model.wv.similarity('孙悟空', '猪八戒'))
print(model.wv.similarity('孙悟空', '孙行者'))
print(model.wv.most_similar(positive=['孙悟空', '唐僧'], negative=['孙行者']))
# 设置模型参数，进行训练
model2 = word2vec.Word2Vec(sentences, vector_size=128, window=5, min_count=5, workers=multiprocessing.cpu_count())
# 保存模型
model2.save('./models/word2Vec.model')
print(model2.wv.similarity('孙悟空', '猪八戒'))
print(model2.wv.similarity('孙悟空', '孙行者'))
print(model2.wv.most_similar(positive=['孙悟空', '唐僧'], negative=['孙行者']))
```

vector_size是词向量维度，window为上下文窗口，min_count过滤低频词；workers影响训练并行度。save保存模型，不代表部署了在线服务。

