"""离线模型替身只演示工具协议，不代表大模型的理解或推理能力。"""

# 导入 json，用于JSON 编解码。
import json

# 从 harness_agent.contracts 显式导入 Message, ModelResponse, ToolCall，声明本模块所需的依赖。
from harness_agent.contracts import Message, ModelResponse, ToolCall


# 定义 DemoModel，将相关数据或操作组织在同一类型内。
class DemoModel:
    """固定演示：读 brief.txt，解析键值行，写 result.json，再回答。"""

    # 异步返回模型响应；此方法不在模型内部执行文件工具。
    async def complete(self, messages: tuple[Message, ...]) -> ModelResponse:
        # 设置 results：历史消息中的结构化工具结果，替身据此决定下一步。
        results = [message.tool_result for message in messages if message.tool_result is not None]
        # 尚无工具结果，固定演示的下一步是读取 brief.txt。
        if not results:
            # 构造模型响应；本方法只表达下一步请求，不直接执行文件工具。
            return ModelResponse(
                # 设置工具请求元组；单元素元组的末尾逗号不能省略。
                tool_calls=(ToolCall("read-1", "read_file", {"path": "brief.txt"}),)
                # 结束当前这一层函数调用或容器声明，回到外层表达式。
            )
        # 最后一项工具结果失败，不能继续声称已生成文件。
        if not results[-1].ok:
            # 拒绝当前错误输入或状态，并通过异常保留具体原因。
            raise ValueError(f"演示工具失败：{results[-1].error_code}")
        # 此时只有读取结果，固定演示的下一步是写入 JSON。
        if len(results) == 1:
            # 设置 fields：从实际读取文本按每行第一个冒号加空格拆出的字段字典。
            fields = dict(line.split(": ", 1) for line in results[0].content.splitlines() if line)
            # 构造模型响应；本方法只表达下一步请求，不直接执行文件工具。
            return ModelResponse(
                # 设置工具请求元组；单元素元组的末尾逗号不能省略。
                tool_calls=(
                    # 开始构造工具调用，依次指定调用 ID、工具名称与参数。
                    ToolCall(
                        # 为写入调用分配 ID，方便与工具结果对应。
                        "write-1",
                        # 选择受限写入工具。
                        "write_file",
                        # 将实际输入解析出的字段编码为 JSON，交给工具写入 result.json。
                        {"path": "result.json", "content": json.dumps(fields, ensure_ascii=False)},
                        # 结束当前这一层函数调用或容器，并用逗号与后面的项目分隔。
                    ),
                    # 结束当前这一层函数调用或容器声明，回到外层表达式。
                )
                # 结束当前这一层函数调用或容器声明，回到外层表达式。
            )
        # 构造模型响应；本方法只表达下一步请求，不直接执行文件工具。
        return ModelResponse(text="已根据输入文件生成 result.json。")

    # 异步释放模型资源，模拟器也保留该统一生命周期接口。
    async def aclose(self) -> None:
        """替身没有外部资源，仍遵循模型生命周期契约。"""
