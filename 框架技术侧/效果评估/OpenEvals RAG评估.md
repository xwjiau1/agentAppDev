# OpenEvals RAG评估

## 技术实现

RAG评估涉及三个对象：查询、上下文、生成回答。检索相关性比较查询与材料；忠实度比较回答与材料；帮助性关注回答是否对问题有用。此案例用手写字符串展示评分机制，没有实际向量检索过程。

## 应用思路

先判断检索资料是否相关，再判断回答是否有资料支撑，有助于区分检索问题与生成问题。两个评估都低时不能只调整生成提示词；资料相关但回答无依据时，应关注生成约束与证据使用。

## 代码解析

### 忠实度裁判的配置

[OpenEvals评估与自动化测试](../../应用侧/基础技术示例/OpenEvals评估与自动化测试/案例说明.md) · [5-rag_groundedness.py，20–26行](../../应用侧/基础技术示例/OpenEvals评估与自动化测试/5-rag_groundedness.py#L20-L26)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
evaluator = create_llm_as_judge(
    prompt=RAG_GROUNDEDNESS_PROMPT,
    feedback_key="groundedness",
    judge=eval_llm,
    continuous=True,
    use_reasoning=False,
)
```

`RAG_GROUNDEDNESS_PROMPT` 定义回答受上下文支持的评分任务；评分键为 groundedness。其余参数与通用OpenEvals裁判一致。

### 比较回答与上下文

[OpenEvals评估与自动化测试](../../应用侧/基础技术示例/OpenEvals评估与自动化测试/案例说明.md) · [5-rag_groundedness.py，56–59行](../../应用侧/基础技术示例/OpenEvals评估与自动化测试/5-rag_groundedness.py#L56-L59)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
result = evaluator(
    context=test_case['context'],
    outputs=test_case['outputs'],
)
```

此调用不传用户查询，重点是 `outputs` 的断言能否由 `context` 支持。示例上下文由32–48行人工定义，不是检索器结果。

### 比较查询与检索材料

[OpenEvals评估与自动化测试](../../应用侧/基础技术示例/OpenEvals评估与自动化测试/案例说明.md) · [6-rag_retrieval_relevance.py，56–59行](../../应用侧/基础技术示例/OpenEvals评估与自动化测试/6-rag_retrieval_relevance.py#L56-L59)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
result = evaluator(
    inputs=test_case['inputs'],
    context=test_case['context'],
)
```

检索相关性传 `inputs` 和 `context`，不传生成回答；它评估材料对问题的相关程度。帮助性示例则用问题和回答评判是否有用，因此与忠实度不是可互换的指标。

## 应用方式差异

RAG单项示例使用相同裁判创建方式，只需掌握对象组合差异。投顾OpenEvals集成版虽然加入帮助性与幻觉评分器，但 predict 未返回真实检索上下文，不能把该集成称为完整RAG评估。
