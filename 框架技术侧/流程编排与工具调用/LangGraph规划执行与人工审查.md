# LangGraph规划执行与人工审查

## 技术实现

图将规划、人工审查、执行和结果审查分成节点，条件路由决定是否经过人工确认，以及是否继续下一轮。

## 应用思路

适合需要明确区分规划与执行的任务。风险标记来源和人工审查后的状态必须与执行节点一起检查，不能只看到human_review节点就认定所有执行均已获准。

## 代码解析

### 风险与完成条件

[LangGraph规划执行与人工审查](../../应用侧/自动化与工具助手/LangGraph规划执行与人工审查/案例说明.md) · [langgraph_agent_manus.py，224–235行](../../应用侧/自动化与工具助手/LangGraph规划执行与人工审查/langgraph_agent_manus.py#L224-L235)

```python
def route_after_plan(state: AgentState) -> Literal["human_review", "executor"]:
    """规划后路由：高风险操作需人工确认"""
    if state.get("is_high_risk", False):
        return "human_review"
    return "executor"


def route_after_review(state: AgentState) -> Literal["planner", "__end__"]:
    """审查后路由：未完成则继续循环"""
    if state.get("is_complete", False):
        return END
    return "planner"
```

is_high_risk决定是否进入人工审查，is_complete决定结束还是回到planner；标记来自节点更新的状态。

### 声明执行节点和分支

[LangGraph规划执行与人工审查](../../应用侧/自动化与工具助手/LangGraph规划执行与人工审查/案例说明.md) · [langgraph_agent_manus.py，246–262行](../../应用侧/自动化与工具助手/LangGraph规划执行与人工审查/langgraph_agent_manus.py#L246-L262)

```python
graph.add_node("planner", planner_node)
graph.add_node("human_review", human_review_node)
graph.add_node("executor", executor_node)
graph.add_node("reviewer", reviewer_node)

# 设置入口
graph.set_entry_point("planner")

# 添加条件边：规划后判断是否需要人工审核
graph.add_conditional_edges(
    "planner",
    route_after_plan,
    {
        "human_review": "human_review",
        "executor": "executor",
    }
)
```

节点各自承担单一阶段，条件边根据路由输出选择目标，人工审查之后仍进入executor，因此需核对拒绝状态如何阻止执行。

