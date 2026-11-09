# DashScope知识抽取与健康检查

## 技术实现

知识维护示例将对话抽取、相似合并、缺失检查、过期检查和冲突检查写成独立处理阶段。

## 应用思路

模型负责提取和判断，业务侧仍需审核后再写入正式知识库，尤其是带有效期或相互冲突的规则。

## 代码解析

### 批量对话抽取

[知识库维护与检索评估](../../应用侧/知识问答与文档处理/知识库维护与检索评估/案例说明.md) · [2-对话知识沉淀.py，100–116行](../../应用侧/知识问答与文档处理/知识库维护与检索评估/2-对话知识沉淀.py#L100-L116)

```python
def batch_extract_knowledge(self, conversations):
    """批量提取知识"""
    all_knowledge = []

    for i, conversation in enumerate(conversations):
        print(f"正在处理对话 {i+1}/{len(conversations)}...")

        result = self.extract_knowledge_from_conversation(conversation)
        all_knowledge.extend(result.get('extracted_knowledge', []))

        # 更新频率统计
        for knowledge in result.get('extracted_knowledge', []):
            key = f"{knowledge['knowledge_type']}:{knowledge['content'][:50]}"
            self.knowledge_frequency[key] += 1

    return all_knowledge
```

逐段调用知识抽取逻辑并汇集结果；后续合并阶段再处理重复知识，不是模型在对话后自动更新参数。

### 汇总健康维度

[知识库维护与检索评估](../../应用侧/知识问答与文档处理/知识库维护与检索评估/案例说明.md) · [3-知识库健康度检查.py，253–272行](../../应用侧/知识问答与文档处理/知识库维护与检索评估/3-知识库健康度检查.py#L253-L272)

```python
def generate_health_report(self, knowledge_base, test_queries):
    """生成完整的健康度报告"""
    print("正在检查知识库健康度...")

    # 1. 检查缺少的知识
    print("1. 检查缺少的知识...")
    missing_result = self.check_missing_knowledge(knowledge_base, test_queries)

    # 2. 检查过期的知识
    print("2. 检查过期的知识...")
    outdated_result = self.check_outdated_knowledge(knowledge_base)

    # 3. 检查冲突的知识
    print("3. 检查冲突的知识...")
    conflicting_result = self.check_conflicting_knowledge(knowledge_base)

    # 4. 计算整体健康度
    overall_score = self.calculate_overall_health_score(missing_result, outdated_result, conflicting_result)

    # 5. 生成报告
```

分别调用缺失、过期和冲突检测，再综合评分和建议。各阶段依赖提示词判断，报告可用于排查，不能视为事实审计结论。

