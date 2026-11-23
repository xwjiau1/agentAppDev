"""D1 的最短控制流；只有 Runner 能决定是否发起下一次模型调用。"""

from harness_agent.contracts import Message, ModelClient, RunResult
from harness_agent.tools import ToolRegistry


async def run_agent(task: str, model: ModelClient, tools: ToolRegistry) -> RunResult:
    """串行执行工具并回填结果；D2 再增加可配置预算和取消收尾。"""
    messages = [Message("user", task)]
    tool_count = 0
    try:
        # D1 保留保守保险上限，防止开发中的替身错误造成无限循环。
        for step in range(1, 9):
            response = await model.complete(tuple(messages))
            messages.append(Message("assistant", response.text))
            if not response.tool_calls:
                if not response.text.strip():
                    raise ValueError("模型没有返回工具调用或最终回答")
                return RunResult("completed", response.text, step, tool_count)
            ids = [call.call_id for call in response.tool_calls]
            if len(set(ids)) != len(ids):
                raise ValueError("同一次响应存在重复 call_id")
            for call in response.tool_calls:
                result = tools.execute(call)
                tool_count += 1
                messages.append(Message("tool", result.content, result))
        return RunResult("limited", "达到 D1 的 8 次调用保险上限", 8, tool_count)
    finally:
        # 工具或模型失败时也释放资源；取消异常不在这里吞掉。
        await model.aclose()
