# Harness子代理上下文隔离

## 技术实现

run_subagent为子任务新建消息列表，使用受限工具集合，在限定轮数内运行并只返回摘要文本。

## 应用思路

将检索或分析子任务放入独立上下文，减少主对话历史膨胀；主代理应保存子任务的结果与限制。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 新上下文与工具集合

[s06_subagent/code.py，276–288行](../../应用侧/自动化与工具助手/通用AgentHarness/s06_subagent/code.py#L276-L288)

```python
def run_subagent(prompt: str) -> str:
    print("\n\033[35m[Subagent started]\033[0m")
    messages = [{"role": "user", "content": prompt}]

    for _ in range(30):
        response = client.messages.create(
            model=MODEL,
            system=SUB_SYSTEM,
            messages=messages,
            tools=SUB_TOOLS,
            max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})
```

消息列表只含本次子任务，SUB_SYSTEM与SUB_TOOLS单独配置；range(30)限制最大迭代。

### 返回摘要

[s06_subagent/code.py，293–299行](../../应用侧/自动化与工具助手/通用AgentHarness/s06_subagent/code.py#L293-L299)

```python
if not tool_calls:
    force = trigger_hooks("Stop", messages)
    if force:
        messages.append({"role": "user", "content": force})
        continue
    print("\033[35m[Subagent done]\033[0m")
    return extract_text(response.content) or "(no summary)"
```

没有工具调用时仍先经过Stop钩子；需要补充工作时注入消息继续，否则提取文本返回。

## 实现差异与边界

独立消息列表不是进程、文件系统或权限隔离。子任务仍由同一宿主执行，不能自动假定拥有独立安全边界。
