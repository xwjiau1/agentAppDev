# OpenEvals效果评估

## 技术实现

OpenEvals用评分提示词与judge模型构造可调用的裁判。调用方传入问题、回答及参考输出，裁判返回评分结果。这里展示的是现有依赖版本下的用法，尚未实际调用验证。

## 应用思路

语义相关性、简洁性等难以只靠规则判断的维度，可分别配置裁判。先用单项脚本观察评分含义，再组合为批量实验。不同指标应分别解释方向，例如有害性高分表示更有害。

## 代码解析

### 创建裁判并提交评分对象

[OpenEvals评估与自动化测试](../../应用侧/基础技术示例/OpenEvals评估与自动化测试/案例说明.md) · [1-correctness.py，44–50行](../../应用侧/基础技术示例/OpenEvals评估与自动化测试/1-correctness.py#L44-L50)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
evaluator = create_llm_as_judge(
    prompt=CORRECTNESS_PROMPT,
    feedback_key="correctness",
    judge=eval_llm,
    continuous=True,
    use_reasoning=False,
)
```

`prompt` 指定正确性标准；`feedback_key` 命名评分项；`judge` 是前面创建的 ChatTongyi 模型；`continuous=True` 请求连续评分；`use_reasoning=False` 控制裁判推理输出选项，不等于证明模型没有内部推理。

### 区分问题、实际回答和参考答案

[OpenEvals评估与自动化测试](../../应用侧/基础技术示例/OpenEvals评估与自动化测试/案例说明.md) · [1-correctness.py，73–77行](../../应用侧/基础技术示例/OpenEvals评估与自动化测试/1-correctness.py#L73-L77)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
result_1 = evaluator(
    inputs=inputs_1,
    outputs=outputs_1,
    reference_outputs=reference_outputs_1,
)
```

`inputs` 表示问题，`outputs` 表示待评回答，`reference_outputs` 表示参考答案。参考答案须由样本提供，不能用待评回答替代。2–11号脚本复用此创建和调用方式，只调整提示词与所需字段，因此不逐个重复相同代码。

### 让裁判能识别业务模式

[OpenEvals评估与自动化测试](../../应用侧/基础技术示例/OpenEvals评估与自动化测试/案例说明.md) · [12-openevals_evaluators.py，79–91行](../../应用侧/基础技术示例/OpenEvals评估与自动化测试/12-openevals_evaluators.py#L79-L91)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
# 返回格式化的输出
# 为了支持评估器，将 processing_mode 信息包含在输出中
final_response = result.get("final_response", "")
processing_mode = result.get("processing_mode", "unknown")

# 将 processing_mode 信息添加到输出文本中（用于评估器提取）
output_text = f"[处理模式: {processing_mode}]\n\n{final_response}"

return {
    "output": output_text,
    "final_response": final_response,
    "processing_mode": processing_mode,
    "query_type": result.get("query_type", "unknown")
```

集成版把 `processing_mode` 写入 output 文本前缀，方便自定义评分提示词提取，同时保留独立的原始回答和模式字段。该处理属于评估适配，未改变投顾工作流本身。

### 将业务规则改为提示词评分

[OpenEvals评估与自动化测试](../../应用侧/基础技术示例/OpenEvals评估与自动化测试/案例说明.md) · [12-openevals_evaluators.py，198–211行](../../应用侧/基础技术示例/OpenEvals评估与自动化测试/12-openevals_evaluators.py#L198-L211)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
create_llm_as_judge(
    prompt=PROCESSING_MODE_PROMPT,
    feedback_key="processing_mode",
    judge=eval_llm,
    continuous=True,
    use_reasoning=False,
),
create_llm_as_judge(
    prompt=RESPONSE_COMPLETENESS_PROMPT,
    feedback_key="response_completeness",
    judge=eval_llm,
    continuous=True,
    use_reasoning=False,
),
```

两个自定义提示词分别判断模式匹配与关键词覆盖。与LangSmith规则版相比，这里由模型解释输出和参考数据，带来额外调用与评分波动；能直接程序比较的字段无需为了统一形式而改用模型。集成版还配置5项预定义指标，330–337行提交LangSmith实验。

## 应用方式差异

单项正确性、简洁性、相关性、代码评分和计划遵循度采用相同裁判构造方式，按不同提示词理解即可；代码评分没有执行待评代码。RAG维度因评估对象不同，另文解释。集成脚本294–314行会删除并重建同名远端数据集，本次未执行。
