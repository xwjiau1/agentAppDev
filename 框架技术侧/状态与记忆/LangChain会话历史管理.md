# LangChain会话历史管理

## 技术实现

RunnableWithMessageHistory把当前输入与会话历史注入提示词，应用使用session_id隔离消息。

## 应用思路

多轮应用可按会话保存上下文；进程内字典不会跨重启保留，也不提供分布式会话一致性。

## 代码解析

### 按会话读取历史

[LangChain模型工具与会话基础](../../应用侧/基础技术示例/LangChain模型工具与会话基础/案例说明.md) · [4-ConversationChain.py，28–39行](../../应用侧/基础技术示例/LangChain模型工具与会话基础/4-ConversationChain.py#L28-L39)

```python
def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# 创建带记忆的对话链
conversation = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)
```

不存在的session_id创建InMemoryChatMessageHistory；input_messages_key和history_messages_key必须对应提示词输入与MessagesPlaceholder名称。

