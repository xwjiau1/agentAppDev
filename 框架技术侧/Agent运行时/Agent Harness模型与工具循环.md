# Agent Harness模型与工具循环

## 技术实现

Harness维持消息列表，将工具定义发送模型，收集tool_use并执行，将tool_result关联回调用ID，继续下一轮。模型负责选择，程序负责执行与记录。

## 应用思路

业务系统可替换工具集合而保留循环。需要明确正常结束、工具失败、输出长度与最大轮数。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 最小循环

[s01_agent_loop/code.py，96–111行](../../应用侧/自动化与工具助手/通用AgentHarness/s01_agent_loop/code.py#L96-L111)

```python
def agent_loop(messages: list):
    while True:
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )

        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})

        # If the model didn't call a tool, we're done
        tool_calls = [
            block for block in response.content if block.type == "tool_use"
        ]
        if not tool_calls:
            return
```

每轮先保存assistant内容；筛选tool_use后判断是否继续。没有工具调用就返回，不等于外部业务目标已独立验证。

### 回填执行结果

[s01_agent_loop/code.py，114–126行](../../应用侧/自动化与工具助手/通用AgentHarness/s01_agent_loop/code.py#L114-L126)

```python
results = []
for block in tool_calls:
    print(f"\033[33m$ {block.input['command']}\033[0m")
    output = run_bash(block.input["command"])
    print(output[:200])
    results.append({
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": output,
    })

# Feed tool results back, loop continues
messages.append({"role": "user", "content": results})
```

tool_use_id对应模型块ID，多个结果聚合后以user消息回传，形成调用与观察闭环。

## 实现差异与边界

s01只提供基本循环；工具扩展、权限、停止判定在后续模块增加。max_tokens=8000限制一次响应输出，不是全任务预算。
