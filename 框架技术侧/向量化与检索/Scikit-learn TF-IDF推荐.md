# Scikit-learn TF-IDF推荐

## 技术实现

TF-IDF把酒店描述转为稀疏词项向量，再计算向量相似度进行内容推荐。

## 应用思路

适合无用户行为数据时建立可解释的推荐基线；本例全量相似矩阵随数据量平方增长。

## 代码解析

### 向量化与相似矩阵

[酒店文本相似推荐](../../应用侧/搜索与推荐/酒店文本相似推荐/案例说明.md) · [hotel_rec.py，85–99行](../../应用侧/搜索与推荐/酒店文本相似推荐/hotel_rec.py#L85-L99)

```python
tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 3), min_df=0.01, stop_words=list(ENGLISH_STOPWORDS))
# 针对desc_clean提取tfidf
tfidf_matrix = tf.fit_transform(df['desc_clean'])
print('TFIDF feature names:')
#print(tf.get_feature_names_out())
print(len(tf.get_feature_names_out()))
#print('tfidf_matrix:')
#print(tfidf_matrix)
#print(tfidf_matrix.shape)
# 计算酒店之间的余弦相似度（线性核函数）
cosine_similarities = linear_kernel(tfidf_matrix, tfidf_matrix)
#print(cosine_similarities)
print(cosine_similarities.shape)
indices = pd.Series(df.index) #df.index是酒店名称
```

ngram_range=(1,3)覆盖一到三元词组；min_df过滤罕见词；linear_kernel计算归一化TF-IDF向量的点积。

### 按目标酒店排序

[酒店文本相似推荐](../../应用侧/搜索与推荐/酒店文本相似推荐/案例说明.md) · [hotel_rec.py，101–113行](../../应用侧/搜索与推荐/酒店文本相似推荐/hotel_rec.py#L101-L113)

```python
def recommendations(name, cosine_similarities = cosine_similarities):
    recommended_hotels = []
    # 找到想要查询酒店名称的idx
    idx = indices[indices == name].index[0]
    print('idx=', idx)
    # 对于idx酒店的余弦相似度向量按照从大到小进行排序
    score_series = pd.Series(cosine_similarities[idx]).sort_values(ascending = False)
    # 取相似度最大的前10个（除了自己以外）
    top_10_indexes = list(score_series.iloc[1:11].index)
    # 放到推荐列表中
    for i in top_10_indexes:
        recommended_hotels.append(list(df.index)[i])
    return recommended_hotels
```

先定位酒店行，再排序该行相似度，排除自身后输出候选；同名酒店和索引唯一性需按真实数据校验。

