# 生成器函数yield与return的区别

> 复习优先级：必背。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

含yield的普通函数调用后返回生成器，迭代时执行并暂停在yield处；return结束生成器，返回值可成为StopIteration.value。

## 面试问答

**问：生成器里`return other_generator`会转发元素吗？** 不会，它结束当前生成器；转发可用yield from或显式for-yield。

**问：yield后局部变量还在吗？** 会保留，下一次迭代从暂停位置继续。

## 实际案例与代码

[Elasticsearch保险问答与会话界面](../../应用侧/搜索与研究助手/Elasticsearch保险问答与会话界面/案例说明.md) · [ai_bot-7.py，205–211行](../../应用侧/搜索与研究助手/Elasticsearch保险问答与会话界面/ai_bot-7.py#L205-L211)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
            yield history



messages.append({'role': 'assistant', 'content': full_response})

session_histories[session_id] = messages
```

每次yield把当前history交给界面消费者；函数尚未结束。全部响应结束后才执行后面的消息保存。同一history对象被多次产出，消费者若要快照需自行复制。

## 易错点与追问

原追踪版run在回退分支return super().run(...)，不会自动迭代父生成器；这是具体代码风险。
