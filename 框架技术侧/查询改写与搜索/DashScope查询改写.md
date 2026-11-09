# DashScope查询改写

## 技术实现

模型先识别上下文依赖、对比、指代、多意图等类型，再将原问题改写为可独立检索的表达。联网版识别检索需求，并输出查询与搜索策略。

## 应用思路

改写层位于检索之前，用于补全指代或分拆意图。应保留原始问题，以便比较改写是否改变用户意图。

## 代码解析

### 按类型分派

[查询改写与搜索策略](../../应用侧/搜索与研究助手/查询改写与搜索策略/案例说明.md) · [1-Query改写.py，183–204行](../../应用侧/搜索与研究助手/查询改写与搜索策略/1-Query改写.py#L183-L204)

```python
def auto_rewrite_and_execute(self, query, conversation_history="", context_info=""):
    """自动识别Query类型并进行改写，然后根据类型调用相应的改写方法"""
    # 首先进行自动识别
    result = self.auto_rewrite_query(query, conversation_history, context_info)

    # 根据识别结果调用相应的改写方法
    query_type = result.get('query_type', '')

    if '上下文依赖' in query_type:
        final_result = self.rewrite_context_dependent_query(query, conversation_history)
    elif '对比' in query_type:
        final_result = self.rewrite_comparative_query(query, context_info or conversation_history)
    elif '模糊指代' in query_type:
        final_result = self.rewrite_ambiguous_reference_query(query, conversation_history)
    elif '多意图' in query_type:
        final_result = self.rewrite_multi_intent_query(query)
    elif '反问' in query_type:
        final_result = self.rewrite_rhetorical_query(query, conversation_history)
    else:
        # 对于其他类型，返回自动识别的改写结果
        final_result = result.get('rewritten_query', query)
```

query_type是模型生成的文本，代码以包含匹配选择具体方法；不匹配时使用初次改写结果。此结构没有强类型枚举校验。

### 识别后生成检索策略

[查询改写与搜索策略](../../应用侧/搜索与研究助手/查询改写与搜索策略/案例说明.md) · [2-Query联网搜索改写.py，166–194行](../../应用侧/搜索与研究助手/查询改写与搜索策略/2-Query联网搜索改写.py#L166-L194)

```python
def auto_web_search_rewrite(self, query, conversation_history=""):
    """自动识别并改写为联网搜索查询"""
    # 第一步：识别是否需要联网搜索
    search_analysis = self.identify_web_search_needs(query, conversation_history)

    if not search_analysis.get('need_web_search', False):
        return {
            "need_web_search": False,
            "reason": "查询不需要联网搜索",
            "original_query": query
        }

    # 第二步：改写查询
    rewritten_result = self.rewrite_for_web_search(query)

    # 第三步：生成搜索策略
    search_strategy = self.generate_search_strategy(query)

    return {
        "need_web_search": True,
        "search_reason": search_analysis.get('search_reason', ''),
        "confidence": search_analysis.get('confidence', 0.5),
        "original_query": query,
        "rewritten_query": rewritten_result.get('rewritten_query', query),
        "search_keywords": rewritten_result.get('search_keywords', []),
        "search_intent": rewritten_result.get('search_intent', ''),
        "suggested_sources": rewritten_result.get('suggested_sources', []),
        "search_strategy": search_strategy
    }
```

先判断need_web_search，为false时提前返回；否则依次生成改写词和策略。字段来自模型JSON，失败时采用原查询回退，不会自动访问网页。

