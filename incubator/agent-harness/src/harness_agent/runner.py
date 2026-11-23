"""D1 的最短控制流；只有 Runner 能决定是否发起下一次模型调用。"""

# 从 harness_agent.contracts 显式导入 Message, ModelClient, RunResult，声明本模块所需的依赖。
from harness_agent.contracts import Message, ModelClient, RunResult

# 从 harness_agent.tools 显式导入 ToolRegistry，声明本模块所需的依赖。
from harness_agent.tools import ToolRegistry


# 异步 Agent 主循环；模型只决策，工具由宿主执行。
async def run_agent(task: str, model: ModelClient, tools: ToolRegistry) -> RunResult:
    """串行执行工具并回填结果；D2 再增加可配置预算和取消收尾。"""
    # 设置 messages：本次运行的消息历史，从用户任务开始逐轮追加。
    messages = [Message("user", task)]
    # 设置 tool_count：工具尝试计数，成功和预期失败均计入。
    tool_count = 0
    # 开始可能返回或抛异常的一组操作；后面的异常处理或清理分支负责收尾。
    try:
        # D1 保留保守保险上限，防止开发中的替身错误造成无限循环。
        # 依次执行第 1 到第 8 次模型调用；range 的上界 9 不包含在内。
        for step in range(1, 9):
            # 设置 response：等待得到的模型响应，含文本或工具请求。
            response = await model.complete(tuple(messages))
            # 追加模型文本；D1 的工具请求本体另由 response.tool_calls 处理。
            messages.append(Message("assistant", response.text))
            # 模型没有请求工具，准备检查最终回答并结束循环。
            if not response.tool_calls:
                # 去掉空白后仍无文本时，不允许把空响应当成成功。
                if not response.text.strip():
                    # 拒绝当前错误输入或状态，并通过异常保留具体原因。
                    raise ValueError("模型没有返回工具调用或最终回答")
                # 返回运行摘要，区分正常结束与额度用尽；这不是自动验收结论。
                return RunResult("completed", response.text, step, tool_count)
            # 设置 ids：本批工具调用标识，用于检查重复 ID。
            ids = [call.call_id for call in response.tool_calls]
            # 集合去重后数量减少，说明这一批调用有重复 ID，不能安全关联结果。
            if len(set(ids)) != len(ids):
                # 拒绝当前错误输入或状态，并通过异常保留具体原因。
                raise ValueError("同一次响应存在重复 call_id")
            # 按模型给出的顺序执行工具，上一项结束后才执行下一项。
            for call in response.tool_calls:
                # 设置 result：调用返回的实际结果，供程序继续处理或测试断言。
                result = tools.execute(call)
                # 每次工具尝试计数加一，包括未知工具或参数错误。
                tool_count += 1
                # 回填工具文本与含 call_id 的结构化结果，供下一次模型调用读取。
                messages.append(Message("tool", result.content, result))
        # 返回运行摘要，区分正常结束与额度用尽；这不是自动验收结论。
        return RunResult("limited", "达到 D1 的 8 次调用保险上限", 8, tool_count)
    # 不论正常返回或抛出异常，都执行以下清理步骤。
    finally:
        # 工具或模型失败时也释放资源；取消异常不在这里吞掉。
        # 无论正常返回还是异常退出，都等待模型资源释放；不吞掉取消异常。
        await model.aclose()
