# LangGraph工具循环与失败重试

## 技术实现

工具循环根据消息是否含工具调用决定继续执行ToolNode或结束；阶段重试根据状态中的error与retry_count决定重做或终止。

## 应用思路

适合需要明确控制执行次数和流程路径的应用，模型选择工具与程序限制循环应分开处理。

## 代码解析

### 决定工具循环是否继续

[工具循环与混合式投顾](../../应用侧/金融投研与投顾/工具循环与混合式投顾/案例说明.md) · [hybrid_wealth_advisor_langgraph.py，267–279行](../../应用侧/金融投研与投顾/工具循环与混合式投顾/hybrid_wealth_advisor_langgraph.py#L267-L279)

```python
def should_continue_tools(state: WealthAdvisorState) -> str:
    messages = state.get("messages", [])
    if not messages:
        return "end"

    last_message = messages[-1]

    # 检查是否有工具调用
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print(f"[DEBUG] 检测到工具调用: {last_message.tool_calls}")
        return "tools"

    return "end"
```

读取最后一条消息的tool_calls，有调用时进入tools，否则进入响应提取；ToolNode完成后回到agent继续推理。

### 阶段推进与有限重试

[多阶段智能投研助手](../../应用侧/金融投研与投顾/多阶段智能投研助手/案例说明.md) · [deliberative_research_langgraph.py，452–478行](../../应用侧/金融投研与投顾/多阶段智能投研助手/deliberative_research_langgraph.py#L452-L478)

```python
def router(state: ResearchAgentState) -> str:
    """根据当前阶段路由到下一步或结束"""

    # 如果有错误，检查是否超过最大重试次数
    if state.get("error"):
        retry_count = state.get("retry_count", 0)
        if retry_count >= MAX_RETRIES:
            print(f"\n超过最大重试次数({MAX_RETRIES})，流程终止")
            return END
        # 未超过重试上限，回到当前阶段重试
        return state["current_phase"]

    # 根据当前阶段决定下一步
    current = state["current_phase"]

    if current == "perception":
        return "modeling"
    elif current == "modeling":
        return "reasoning"
    elif current == "reasoning":
        return "decision"
    elif current == "decision":
        return "report"
    elif current == "report":
        return END
    else:
        return END
```

有error时检查MAX_RETRIES，未超过上限回到current_phase；成功时依阶段映射推进。节点需正确维护error和retry_count，路由本身不会自动计数。

