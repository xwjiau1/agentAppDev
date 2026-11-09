# Qwen-Agent工具调用与提示词编排

## 技术实现

Qwen-Agent版将客户画像与处理策略写入 system_message，将工具名放入 function_list，由 Assistant 在对话中选择是否调用工具。它没有显式创建状态图，也没有产出与LangGraph版等价的结构化模式状态。

## 应用思路

对话助手可把稳定规则与用户背景放入系统提示词，把需要外部计算或数据访问的能力注册为工具。当前投顾用一项行情工具配合客户画像提供问答；复杂分析步骤主要由提示词约束。

## 代码解析

### 注册行情工具

[Qwen投顾助手与Langfuse追踪](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/案例说明.md) · [1-hybrid_wealth_advisor_qwen_agent.py，64–89行](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/1-hybrid_wealth_advisor_qwen_agent.py#L64-L89)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
@register_tool('query_shanghai_index')
class QueryShanghaiIndexTool(BaseTool):
    """
    上证指数实时查询工具（模拟版），返回固定的行情数据
    """
    description = '查询上证指数的最新行情数据，包括当前点位、涨跌和涨跌幅'
    parameters = []

    def call(self, params: str, **kwargs) -> str:
        """执行上证指数查询"""
        # 解析参数（即使没有参数也需要处理）
        try:
            if params:
                import json
                args = json.loads(params)
        except:
            pass

        # 直接返回模拟数据，避免外部API不可用导致报错
        name = "上证指数"
        price = "3125.62"
        change = "6.32"
        pct = "0.20"
        result = f"{name} 当前点位: {price}，涨跌: {change}，涨跌幅: {pct}%"
        print('工具调用结果:', result)
        return result
```

`register_tool` 的名称是工具注册标识；工具类继承 `BaseTool`。`description` 帮助模型理解用途，`parameters=[]` 表示没有必填业务参数。框架把调用参数交给 `call`，该函数返回字符串供模型生成回答。这里返回固定行情，并未查询真实市场。

### 组合模型、系统提示词与工具

[Qwen投顾助手与Langfuse追踪](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/案例说明.md) · [1-hybrid_wealth_advisor_qwen_agent.py，175–190行](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/1-hybrid_wealth_advisor_qwen_agent.py#L175-L190)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
def init_wealth_advisor_agent(customer_profile: Dict[str, Any]) -> Assistant:
    """初始化财富顾问智能体"""
    llm_cfg = {
        'model': 'qwen-turbo-latest',
        'timeout': 30,
        'retry_count': 3,
    }

    try:
        agent = Assistant(
            llm=llm_cfg,
            name='财富管理投顾AI助手',
            description='混合智能体财富管理咨询服务',
            system_message=get_system_prompt(customer_profile),
            function_list=['query_shanghai_index'],
        )
```

`llm_cfg` 指定模型名以及超时和重试配置；具体生效行为取决于所用版本。`get_system_prompt(customer_profile)` 把客户信息和两种处理策略写入提示词。`function_list` 引用已经注册的工具，`name` 和 `description` 为助手身份描述。

### 维护多轮对话

[Qwen投顾助手与Langfuse追踪](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/案例说明.md) · [1-hybrid_wealth_advisor_qwen_agent.py，328–338行](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/1-hybrid_wealth_advisor_qwen_agent.py#L328-L338)

以下为案例原代码摘录，统一去除外层缩进；省略的上下文可在源文件中查看。

```python
# 构建消息
messages.append({'role': 'user', 'content': query})

print("正在处理您的请求...")

# 运行助手并处理响应
response = []
for response in agent.run(messages):
    print('助手回复:', response)

messages.extend(response)
```

先追加用户消息，再迭代 `agent.run(messages)` 获取响应。循环结束后把最后一组响应追加到消息历史，供下一轮继续使用。这里的历史由调用方维护，不等于自动持久化记忆。

## 应用方式差异

基础投顾和追踪版的助手配置、行情工具用法相同，不重复展开。追踪版另外继承 Assistant 包装 run，详见Langfuse调用追踪。门票参考使用同样的工具注册方式，但 `ExcSQLTool.call` 执行SQL并返回表格与图片；差异在工具内部业务逻辑，而非编排机制。
