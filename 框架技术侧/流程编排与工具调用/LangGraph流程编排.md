# LangGraph流程编排

## 技术实现

LangGraph版投顾把处理过程拆成状态、节点和边。每个节点读取状态并返回更新后的字段，条件边读取 processing_mode 决定执行路径。模型只负责判断查询类型和生成内容，执行顺序由图控制。

## 应用思路

需要固定步骤、明确分支和中间结果时，可将业务阶段对应到节点。此案例把简单查询直接回答，把复杂分析拆成收集、分析、建议三个阶段，两条路径汇合到 respond。

## 代码解析

### 注册状态和节点

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [1-hybrid_wealth_advisor_langgraph_langsmith.py，464–472行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/1-hybrid_wealth_advisor_langgraph_langsmith.py#L464-L472)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
# 创建状态图
workflow = StateGraph(WealthAdvisorState)

# 添加节点，每个节点都确保返回完整的状态
workflow.add_node("assess", assess_query)
workflow.add_node("reactive", reactive_processing)
workflow.add_node("collect_data", collect_data)
workflow.add_node("analyze", analyze_data)
workflow.add_node("recommend", generate_recommendations)
```

`StateGraph(WealthAdvisorState)` 使用状态类型描述字段；节点名是图中的标识，第二个参数是执行函数。`assess` 写入模式字段，其他节点消费该结果。状态类型在同文件103–121行，包含输入、客户画像、分析结果、最终回答和错误。

### 按状态分支并汇合

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [1-hybrid_wealth_advisor_langgraph_langsmith.py，488–509行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/1-hybrid_wealth_advisor_langgraph_langsmith.py#L488-L509)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
# 设置入口点
workflow.set_entry_point("assess")

# 添加分支路由
workflow.add_conditional_edges(
    "assess",
    lambda x: "reactive" if x.get("processing_mode") == "reactive" else "collect_data",
    {
        "reactive": "reactive",
        "collect_data": "collect_data"
    }
)

# 添加固定路径边
workflow.add_edge("reactive", "respond")
workflow.add_edge("collect_data", "analyze")
workflow.add_edge("analyze", "recommend")
workflow.add_edge("recommend", "respond")
workflow.add_edge("respond", END)

# 编译工作流
return workflow.compile()
```

`set_entry_point` 指定入口；条件函数返回的字符串通过映射选择目标节点。`reactive` 路径直接进入 respond；另一路依次执行 collect_data、analyze、recommend。`END` 结束图执行，`compile()` 生成可调用工作流。模式字段由244–283行的 `assess_query` 调用模型产生，并对未知值回退到 reactive。

## 应用方式差异

投顾目录和OpenEvals目录的同名主程序完全相同，只解释一次。OpenEvals将该应用作为被测函数调用，没有改变图的编排方式。Qwen版采用提示词指导策略，不具备这份代码中的显式条件边。
