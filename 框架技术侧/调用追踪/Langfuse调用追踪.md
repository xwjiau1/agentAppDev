# Langfuse调用追踪

## 技术实现

追踪版继承 Qwen-Agent Assistant，重写 run 并通过 observe 包装执行。代码在当前观察记录上更新查询、客户属性、最终输出，再调用flush提交。此处主要记录整体请求，没有逐个包装所有工具与模型调用。

## 应用思路

无法直接沿用LangChain调用配置时，可以在应用实际执行入口建立观察记录，将请求输入和最终输出放在同一次调用内。GUI和函数接口可能经过不同入口，应分别确认追踪覆盖范围。

## 代码解析

### 建立GUI观察记录

[Qwen投顾助手与Langfuse追踪](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/案例说明.md) · [1-hybrid_wealth_advisor_qwen_agent_langfuse.py，265–270行](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/1-hybrid_wealth_advisor_qwen_agent_langfuse.py#L265-L270)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
@observe(name="gui_query", as_type="generation")
def _traced_run():
    print("[DEBUG] _traced_run() 函数开始执行")

    # 设置 input 和 metadata
    input_set = False
```

`name="gui_query"` 命名观察记录；`as_type="generation"` 选择记录类型。内部函数放在observe作用域中执行后，再更新当前记录；具体SDK参数兼容性尚未运行确认。

### 补充输入与客户属性

[Qwen投顾助手与Langfuse追踪](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/案例说明.md) · [1-hybrid_wealth_advisor_qwen_agent_langfuse.py，275–289行](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/1-hybrid_wealth_advisor_qwen_agent_langfuse.py#L275-L289)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
if langfuse:
    input_value = user_query if user_query else str(messages)[:500]
    print(f"[DEBUG] 准备设置 input: {input_value[:100]}")
    langfuse.update_current_span(
        input=input_value,
        model="qwen-turbo-latest",
        metadata={
            "customer_id": self.customer_id,
            "risk_tolerance": self.customer_profile.get("risk_tolerance", "unknown"),
            "investment_horizon": self.customer_profile.get("investment_horizon", "unknown"),
            "portfolio_value": self.customer_profile.get("portfolio_value", 0),
            "query_length": len(user_query) if user_query else 0,
            "mode": "gui"
        }
    )
```

`input` 记录提取出的用户查询；没有查询时使用消息字符串截断值。`metadata` 附带客户、风险偏好和查询长度。代码把 `model` 传给 update_current_span，是否适用于当前SDK方法应运行核验，不能把捕获异常后的继续执行当作上传成功。

### 写入输出并提交

[Qwen投顾助手与Langfuse追踪](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/案例说明.md) · [1-hybrid_wealth_advisor_qwen_agent_langfuse.py，364–375行](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/1-hybrid_wealth_advisor_qwen_agent_langfuse.py#L364-L375)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
output_value = final_output if final_output else "响应已生成"
print(f"[DEBUG] 准备设置 output: {output_value[:100]}")
langfuse.update_current_span(
    output=output_value,
    metadata={
        "response_length": len(final_output),
        "response_count": len(all_responses)
    }
)
output_set = True
print("[DEBUG] output 设置成功")
langfuse.flush()
```

`output` 保存最终文本，metadata补充响应长度与批次数，`flush()` 请求提交缓冲记录。303–309行先把所有响应收集到列表，388–393行再yield回放，因此这条GUI路径并非边生成边展示。

### 函数接口的追踪入口

[Qwen投顾助手与Langfuse追踪](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/案例说明.md) · [1-hybrid_wealth_advisor_qwen_agent_langfuse.py，495–499行](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/1-hybrid_wealth_advisor_qwen_agent_langfuse.py#L495-L499)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
if langfuse_client and observe:
    try:
        @observe(name="wealth_advisor_query")
        def _traced_run():
            # 更新 metadata
```

函数调用路径使用独立名称 wealth_advisor_query，内部执行 `_run_agent_internal`；GUI路径则经过TracedAssistant.run，两个入口不能只验证其中一个就认定全部覆盖。

## 应用方式差异

基础Qwen版没有追踪包装，追踪版增加了GUI和函数接口两种接入。TracedAssistant.run是生成器，400、403行用 `return super().run(...)` 回退时不会自动迭代父生成器，存在无响应风险；这是保留原代码的静态问题，尚未修复或实测。
