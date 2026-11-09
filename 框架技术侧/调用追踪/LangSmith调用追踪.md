# LangSmith调用追踪

## 技术实现

LangGraph案例通过 RunnableConfig 把标签、元数据与运行名称传给 invoke，并使用环境变量控制追踪开关。追踪用于关联一次请求及其内部调用，评分则由独立评估器完成。

## 应用思路

把业务分类放入 tags，把需要筛选的请求属性放入 metadata，再为运行设置可识别名称，可以按客户、任务类型或实验定位调用。这里记录的是静态客户样例和当前问题，不能由追踪配置推断已经完成性能优化。

## 代码解析

### 配置标签和请求属性

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [1-hybrid_wealth_advisor_langgraph_langsmith.py，573–591行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/1-hybrid_wealth_advisor_langgraph_langsmith.py#L573-L591)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
if LANGSMITH_ENABLED:
    # 添加 LangSmith 配置：标签和元数据
    config = RunnableConfig(
        tags=[
            "wealth-advisor",
            "hybrid-agent",
            f"customer-{customer_id}",
            customer_profile.get("risk_tolerance", "unknown")
        ],
        metadata={
            "customer_id": customer_id,
            "risk_tolerance": customer_profile.get("risk_tolerance", "unknown"),
            "investment_horizon": customer_profile.get("investment_horizon", "unknown"),
            "portfolio_value": customer_profile.get("portfolio_value", 0),
            "user_query": user_query[:100],  # 只记录前100个字符
            "timestamp": datetime.now().isoformat()
        },
        run_name=f"wealth-advisor-{customer_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
```

`tags` 是用于筛选分组的字符串列表；`metadata` 存放客户与请求属性；`run_name` 设置运行名称。`user_query[:100]` 仅截断这个元数据字段，不意味着所有追踪输入都会被截断。`LANGSMITH_ENABLED` 在67行读取环境开关。

### 将配置传递到实际执行

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [1-hybrid_wealth_advisor_langgraph_langsmith.py，593–597行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/1-hybrid_wealth_advisor_langgraph_langsmith.py#L593-L597)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
# 运行智能体并捕获可能的异常
if config:
    result = agent.invoke(initial_state, config=config)
else:
    result = agent.invoke(initial_state)
```

只有把配置传给 `agent.invoke` 才能把本次调用与标签、元数据关联。关闭追踪时仍调用同一Agent图。服务凭据使用环境变量，真实上传结果与节点追踪完整性本轮未验证。

## 应用方式差异

现有案例组各目录中的同名LangGraph主程序完全一致，因此追踪方式只说明一次。LangSmith批量效果评估另有数据集与评分器流程；调用追踪本身不会自动判定业务结果正确。
