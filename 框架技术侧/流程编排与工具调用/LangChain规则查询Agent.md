# LangChain规则查询Agent

## 技术实现

通过tool装饰器导出带说明的函数，将工具列表与模型交给create_agent形成对话执行入口。

## 应用思路

小型规则库可先以确定性查询工具支持模型回答，再按需要替换为数据库检索；固定样例内容不能当作最新业务规则。

## 代码解析

### 关键词规则检索

[基金规则工具问答](../../应用侧/金融投研与投顾/基金规则工具问答/案例说明.md) · [fund_qa_langchain.py，45–66行](../../应用侧/金融投研与投顾/基金规则工具问答/fund_qa_langchain.py#L45-L66)

```python
@tool
def search_rules_by_keywords(keywords: str) -> str:
    """通过关键词搜索相关私募基金规则。输入应为相关关键词，多个关键词用逗号或空格分隔。"""
    keywords = keywords.strip().lower()
    keyword_list = re.split(r'[,，\s]+', keywords)

    matched_rules = []
    for rule in FUND_RULES_DB:
        rule_text = (rule["category"] + " " + rule["question"]).lower()
        match_count = sum(1 for kw in keyword_list if kw in rule_text)
        if match_count > 0:
            matched_rules.append((rule, match_count))

    matched_rules.sort(key=lambda x: x[1], reverse=True)

    if not matched_rules:
        return "未找到与关键词相关的规则。"

    result = []
    for rule, _ in matched_rules[:2]:
        result.append(f"类别: {rule['category']}\n问题: {rule['question']}\n答案: {rule['answer']}")
```

keywords按逗号或空格拆分，命中类别或问题后按匹配个数排序，最多返回两条。这里不是向量召回。

### 组合模型与工具

[基金规则工具问答](../../应用侧/金融投研与投顾/基金规则工具问答/案例说明.md) · [fund_qa_langchain.py，131–133行](../../应用侧/金融投研与投顾/基金规则工具问答/fund_qa_langchain.py#L131-L133)

```python
agent = create_agent(llm, tools, system_prompt=system_prompt)

return agent
```

system_prompt约束无证据时的表达，工具承担实际检索。应用侧仍需核实返回的规则来源和有效期。

