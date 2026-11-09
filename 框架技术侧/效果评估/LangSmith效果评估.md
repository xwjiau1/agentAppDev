# LangSmith效果评估

## 技术实现

LangSmith评估连接数据集、被测函数和评估器。数据集保存输入与参考输出；被测函数执行Agent；RunEvaluator读取运行结果与样本期望，返回 key、score 和 comment。本案例用确定性规则判断处理模式和关键词覆盖。

## 应用思路

把可明确判断的业务约束写成规则，把不同难度的问题放入测试集。对新旧提示词或模型运行同一数据集，按独立指标比较结果；关键词覆盖只表示出现比例，不能证明回答事实正确。

## 代码解析

### 定义输入与期望

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [2-langsmith_testing_evaluation.py，62–72行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/2-langsmith_testing_evaluation.py#L62-L72)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
REACTIVE_TEST_CASES = [
    {
        "inputs": {
            "user_query": "今天上证指数的表现如何？",
            "customer_id": "customer1"
        },
        "expected_outputs": {
            "processing_mode": "reactive",
            "should_contain": ["上证指数", "点位", "涨跌"]
        }
    },
```

`inputs` 是被测应用的入参；`expected_outputs` 为本地用例约定，不是模型实际回答。创建数据集时，318–321行把它写入 LangSmith Example 的 `outputs`，作为评分参考。模式用于路径校验，关键词用于完整性评分。

### 读取并比较实际模式

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [2-langsmith_testing_evaluation.py，205–227行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/2-langsmith_testing_evaluation.py#L205-L227)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
example_outputs = _get_example_outputs(example)
expected_mode = example_outputs.get("processing_mode")

if not expected_mode:
    return {
        "key": "processing_mode",
        "score": None,
        "comment": "未指定期望的处理模式"
    }

actual_mode = run.outputs.get("processing_mode") if run.outputs else None

if actual_mode == expected_mode:
    return {
        "key": "processing_mode",
        "score": 1.0,
        "comment": f"处理模式正确: {actual_mode}"
    }
else:
    return {
        "key": "processing_mode",
        "score": 0.0,
        "comment": f"处理模式不匹配: 期望 {expected_mode}, 实际 {actual_mode}"
```

`example_outputs` 来自参考样本，`run.outputs` 来自实际运行。模式完全相等返回1，否则返回0。缺少期望模式时返回 `score=None`，表示没有可评分依据，不应合并为0分。外层 `ProcessingModeEvaluator` 继承 RunEvaluator。

### 计算关键词覆盖

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [2-langsmith_testing_evaluation.py，249–268行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/2-langsmith_testing_evaluation.py#L249-L268)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
response = run.outputs.get("final_response", "")
example_outputs = _get_example_outputs(example)
expected_keywords = example_outputs.get("should_contain", [])

if not expected_keywords:
    return {
        "key": "response_completeness",
        "score": None,
        "comment": "未指定期望的关键词"
    }

# 检查是否包含期望的关键词
response_lower = response.lower()
found_keywords = [kw for kw in expected_keywords if kw.lower() in response_lower]
completeness = len(found_keywords) / len(expected_keywords) if expected_keywords else 0

return {
    "key": "response_completeness",
    "score": completeness,
    "comment": f"找到 {len(found_keywords)}/{len(expected_keywords)} 个期望关键词"
```

先将实际回答转小写，再逐项检查期望关键词是否出现。`completeness` 是命中数除以期望词数；没有关键词则返回None。这里只计算字面匹配，没有验证词语之间的含义关系。

### 运行批量实验

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [2-langsmith_testing_evaluation.py，434–440行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/2-langsmith_testing_evaluation.py#L434-L440)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
results = evaluate(
    test_function,
    data=dataset_name,
    evaluators=evaluators,
    experiment_prefix=experiment_name,
    max_concurrency=1  # 串行执行，避免API限流
)
```

第一个参数是被测函数；`data` 指定数据集；`evaluators` 是评分器列表；`experiment_prefix` 区分实验；`max_concurrency=1` 串行执行以减少限流。数据集包含边界用例，但当前两个规则评分器没有单独评估 `should_handle_error`。

## 应用方式差异

投顾与OpenEvals目录中的规则评估脚本完全相同，合并说明。OpenEvals集成版仍使用LangSmith组织实验，但将模式和关键词评分也改为模型提示词判断，具体差异在OpenEvals效果评估中说明。
