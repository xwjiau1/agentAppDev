# TypedDict与字典字段类型

> 复习优先级：常考。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

TypedDict描述字典有哪些键以及值的类型，主要服务静态检查；运行时实例仍是普通dict。默认必需键与Optional值的含义不同。

## 面试问答

**问：Optional字段能省略键吗？** 不能由Optional直接推出；它表示值允许None。键可缺省需使用适当的可选键声明。

**问：TypedDict会自动补默认值吗？** 不会，也不自动解析外部JSON。

## 实际案例与代码

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [1-hybrid_wealth_advisor_langgraph_langsmith.py，103–121行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/1-hybrid_wealth_advisor_langgraph_langsmith.py#L103-L121)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
class WealthAdvisorState(TypedDict):
    """财富顾问智能体的状态"""
    # 输入
    user_query: str  # 用户查询
    customer_profile: Optional[Dict[str, Any]]  # 客户画像

    # 处理状态
    query_type: Optional[Literal["emergency", "informational", "analytical"]]  # 查询类型
    processing_mode: Optional[Literal["reactive", "deliberative"]]  # 处理模式
    emergency_response: Optional[Dict[str, Any]]  # 紧急响应结果
    market_data: Optional[Dict[str, Any]]  # 市场数据
    analysis_results: Optional[Dict[str, Any]]  # 分析结果

    # 输出
    final_response: Optional[str]  # 最终响应

    # 控制流
    current_phase: Optional[str]
    error: Optional[str]  # 错误信息
```

状态定义描述user_query、客户画像和过程字段；运行时创建的initial_state仍需自行填充字段。注解帮助读懂数据流，不等于自动验证模型输出。

## 易错点与追问

读取不存在的键仍可能KeyError；状态框架可能额外约定更新方式，但不是TypedDict自带机制。
