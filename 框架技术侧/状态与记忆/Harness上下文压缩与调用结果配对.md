# Harness上下文压缩与调用结果配对

## 技术实现

ContextCompactor先约束工具结果，再裁剪旧历史、缩小大结果，仍超限时生成摘要。完整transcript落盘供追溯。

## 应用思路

长任务要同时保护当前请求、工具调用结果配对和恢复信息，不能只取消息列表最后N项。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 压缩入口

[s08_context_compact/code.py，518–541行](../../应用侧/自动化与工具助手/通用AgentHarness/s08_context_compact/code.py#L518-L541)

```python
def prepare(self, messages: list, active_request: str) -> list:
    messages = self.tool_result_budget(messages)
    before_snip = messages
    messages = self.snip_compact(messages)
    active_request_marker = (
        f"Current user request:\n{active_request}\n\n"
        "Conversation summary (reference only):"
    )
    if (messages is not before_snip
            and not any(
                message.get("role") == "user"
                and isinstance(message.get("content"), str)
                and (message["content"] == active_request
                     or active_request_marker in message["content"])
                for message in messages)):
        messages.append({"role": "user", "content": active_request})
    if self.estimate_chars(messages) > self.CONTEXT_CHAR_LIMIT:
        target = int(self.CONTEXT_CHAR_LIMIT * 0.8)
        messages = self.micro_compact(messages, target)
        if self.estimate_chars(messages) > self.CONTEXT_CHAR_LIMIT:
            messages = self.fit_tool_results(messages, target)
        if self.estimate_chars(messages) > self.CONTEXT_CHAR_LIMIT:
            print("[auto compact]")
            messages = self.compact_history(messages, active_request)
```

先处理结果预算与snip，再确保当前请求没有被剪掉；根据字符估计依次采用micro、fit和摘要压缩。

### 保护工具配对

[s08_context_compact/code.py，506–516行](../../应用侧/自动化与工具助手/通用AgentHarness/s08_context_compact/code.py#L506-L516)

```python
def reactive_compact(self, messages: list, active_request: str) -> list:
    transcript = self.write_transcript(messages)
    print(f"[transcript saved: {transcript}]")
    tail_start = max(0, len(messages) - self.KEEP_RECENT_MESSAGES)
    if (tail_start > 0 and self.is_tool_result(messages[tail_start])
            and self.has_tool_use(messages[tail_start - 1])):
        tail_start -= 1
    old_history = messages[:tail_start] if tail_start else messages
    summary = self.summarize_history(old_history)
    message = self.summary_message("Reactive compact", active_request, summary, transcript)
    return [message, *messages[tail_start:]] if tail_start else [message]
```

如果保留片段以tool_result开头且前一条有tool_use，向前多保留一条，避免留下孤立结果。

## 实现差异与边界

这里用字符数估计预算，不是精确token计数。摘要可能丢信息，完整transcript只是补救手段，不保证模型自动恢复全部细节。
