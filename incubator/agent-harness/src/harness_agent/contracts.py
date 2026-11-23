"""共享契约只描述数据，不读取环境或执行任何任务。"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: dict[str, str]


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    ok: bool
    content: str
    error_code: str | None = None


@dataclass(frozen=True)
class Message:
    role: str
    content: str
    tool_result: ToolResult | None = None


@dataclass(frozen=True)
class ModelResponse:
    text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()


class ModelClient(Protocol):
    """D1 只需要消息输入；实际请求体快照在 D3/D4 增加。"""

    async def complete(self, messages: tuple[Message, ...]) -> ModelResponse: ...

    async def aclose(self) -> None: ...


@dataclass(frozen=True)
class RunResult:
    status: str
    answer: str
    model_calls: int
    tool_calls: int
