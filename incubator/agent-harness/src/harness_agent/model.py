"""离线模型替身只演示工具协议，不代表大模型的理解或推理能力。"""

import json

from harness_agent.contracts import Message, ModelResponse, ToolCall


class DemoModel:
    """固定演示：读 brief.txt，解析键值行，写 result.json，再回答。"""

    async def complete(self, messages: tuple[Message, ...]) -> ModelResponse:
        results = [message.tool_result for message in messages if message.tool_result is not None]
        if not results:
            return ModelResponse(
                tool_calls=(ToolCall("read-1", "read_file", {"path": "brief.txt"}),)
            )
        if not results[-1].ok:
            raise ValueError(f"演示工具失败：{results[-1].error_code}")
        if len(results) == 1:
            fields = dict(line.split(": ", 1) for line in results[0].content.splitlines() if line)
            return ModelResponse(
                tool_calls=(
                    ToolCall(
                        "write-1",
                        "write_file",
                        {"path": "result.json", "content": json.dumps(fields, ensure_ascii=False)},
                    ),
                )
            )
        return ModelResponse(text="已根据输入文件生成 result.json。")

    async def aclose(self) -> None:
        """替身没有外部资源，仍遵循模型生命周期契约。"""
