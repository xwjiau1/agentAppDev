# Elasticsearch检索工具与联网补充

## 技术实现

自定义retrieval工具负责文件切块与ES索引，Agent同时配置Tavily MCP服务，通过提示词描述本地检索优先策略。

## 应用思路

可以将企业内部文档查询与外部时效信息查询组合。这里的优先顺序由提示词指导，并非程序保证的硬路由。

## 代码解析

### 全文检索请求

[Elasticsearch保险问答与会话界面](../../应用侧/搜索与研究助手/Elasticsearch保险问答与会话界面/案例说明.md) · [es_retrieval_tool.py，217–230行](../../应用侧/搜索与研究助手/Elasticsearch保险问答与会话界面/es_retrieval_tool.py#L217-L230)

```python
search_body = {

    "query": {

        "match": {

            "content": query

        }

    },

    "size": 5 # 返回最相关的5个块
```

match对content执行词项检索，size=5限制返回条数。结果格式化携带来源、内容与ES得分；这条工具不是向量KNN。

### 配置检索后端

[Elasticsearch保险问答与会话界面](../../应用侧/搜索与研究助手/Elasticsearch保险问答与会话界面/案例说明.md) · [ai_bot-4.py，47–59行](../../应用侧/搜索与研究助手/Elasticsearch保险问答与会话界面/ai_bot-4.py#L47-L59)

```python
rag_cfg = {

    "rag_backend": "elasticsearch",  # 关键：指定使用 ES 后端

    "es": {

        "host": "https://localhost",

        "port": 9200,

        "user": "elastic",

        "password": "YOUR_CREDENTIAL",  # 您的 Elasticsearch 密码
```

rag_backend和es配置只在支持它们的Qwen-Agent实现中生效；附带源码需与安装包版本区分，不能只因传入配置就认定已接入成功。

### 会话历史与流式界面

[Elasticsearch保险问答与会话界面](../../应用侧/搜索与研究助手/Elasticsearch保险问答与会话界面/案例说明.md) · [ai_bot-7.py，169–188行](../../应用侧/搜索与研究助手/Elasticsearch保险问答与会话界面/ai_bot-7.py#L169-L188)

```python
def stream_predict(query: str, history: list, session_id: str) -> Generator:

    """Gradio 的核心预测函数 - 支持流式响应"""

    if session_id not in session_histories:

        session_histories[session_id] = []



    messages = session_histories[session_id]

    messages.append({'role': 'user', 'content': query})



    history[-1][1] = ""

    full_response = ""
```

session_id区分内存中的messages，逐步响应更新界面。该历史仅存于进程字典，没有跨进程持久化。

