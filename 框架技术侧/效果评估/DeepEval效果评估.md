# DeepEval效果评估

## 技术实现

DeepEval把问题、实际输出和上下文封装为 LLMTestCase，再对测试对象运行多个指标。现有代码定义相关性、幻觉与GEval自定义风险偏好评分，裁判模型均指定为 gpt-4o-mini。

## 应用思路

需要把若干质量条件组织为测试对象与指标时，可以按业务维度定义阈值和评价依据。投顾的风险偏好指标希望检查建议是否考虑客户特征，但模型需要充分的客户信息才能判断是否匹配。

## 代码解析

### 构建测试对象

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [deepeval_wealth_advisor.py，108–118行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/deepeval_wealth_advisor.py#L108-L118)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
def create_test_case(
    test_data: Dict[str, Any],
    actual_output: str,
    retrieval_context: List[str]
) -> LLMTestCase:
    """创建 DeepEval 测试用例"""
    return LLMTestCase(
        input=test_data["input"],
        actual_output=actual_output,
        retrieval_context=retrieval_context
    )
```

`input` 是问题，`actual_output` 是Agent实际回答，`retrieval_context` 是参考检索材料列表。这里未传 expected_output。上下文参数与具体幻觉指标所需字段是否一致仍待版本核验，不能只凭定义认定评估可运行。

### 配置相关性指标

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [deepeval_wealth_advisor.py，126–131行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/deepeval_wealth_advisor.py#L126-L131)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
# 1. 答案相关性：评估回答是否与问题相关
relevancy_metric = AnswerRelevancyMetric(
    threshold=0.6,
    model="gpt-4o-mini",
    include_reason=True
)
```

`threshold=0.6` 为相关性指标设置通过阈值，`model` 指定评分模型，`include_reason=True` 请求附带评分理由。阈值只对当前指标解释，不应直接套到所有指标。

### 定义业务评分标准

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [deepeval_wealth_advisor.py，140–155行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/deepeval_wealth_advisor.py#L140-L155)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
# 3. 自定义评估：是否考虑客户风险偏好
risk_consideration_metric = GEval(
    name="RiskConsideration",
    criteria="评估投资建议是否考虑了客户的风险承受能力和投资偏好",
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT
    ],
    evaluation_steps=[
        "检查回答是否提及风险相关内容",
        "评估建议是否与客户风险等级匹配",
        "判断是否有个性化的考虑"
    ],
    threshold=0.5,
    model="gpt-4o-mini"
)
```

`criteria` 描述要评估的业务要求；`evaluation_params` 指定读取问题与实际回答；`evaluation_steps` 把检查要求展开；`threshold` 为该项阈值。这里没有把独立的客户风险字段列为评价参数，判断匹配程度取决于问题或回答是否已包含足够背景。

## 应用方式差异

相关性和幻觉使用内置指标，客户风险偏好使用GEval标准，两者在评分要求的表达方式上不同。该案例主程序调用DashScope，而这些裁判调用OpenAI，运行需要分别配置服务；原 requirements.txt 未列DeepEval，尚未运行验证。
