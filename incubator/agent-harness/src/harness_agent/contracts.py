"""共享契约只描述数据，不读取环境或执行任何任务。"""

# 从 dataclasses 显式导入 dataclass，声明本模块所需的依赖。
from dataclasses import dataclass

# 从 typing 显式导入 Protocol，声明本模块所需的依赖。
from typing import Protocol


# 自动生成初始化等方法；frozen 阻止字段重新赋值，但不会深度冻结字典。
@dataclass(frozen=True)
# 定义 ToolCall，将相关数据或操作组织在同一类型内。
class ToolCall:
    # 声明 call_id 字段及其类型：调用标识，用来把工具结果关联回原始请求。
    call_id: str
    # 声明 name 字段及其类型：工具名称，用于查找允许执行的处理函数。
    name: str
    # 声明工具参数字典；当前仅允许字符串值，实际执行前还会校验。
    arguments: dict[str, str]


# 自动生成初始化等方法；frozen 阻止字段重新赋值，但不会深度冻结字典。
@dataclass(frozen=True)
# 定义 ToolResult，将相关数据或操作组织在同一类型内。
class ToolResult:
    # 声明 call_id 字段及其类型：调用标识，用来把工具结果关联回原始请求。
    call_id: str
    # 声明 ok 字段及其类型：工具执行是否成功，与任务是否验收通过相互独立。
    ok: bool
    # 声明 content 字段及其类型：消息正文或工具结果文本。
    content: str
    # 设置 error_code：可选的稳定错误码，成功时通常为 None。
    error_code: str | None = None


# 自动生成初始化等方法；frozen 阻止字段重新赋值，但不会深度冻结字典。
@dataclass(frozen=True)
# 定义 Message，将相关数据或操作组织在同一类型内。
class Message:
    # 声明 role 字段及其类型：消息来源，例如 user、assistant 或 tool。
    role: str
    # 声明 content 字段及其类型：消息正文或工具结果文本。
    content: str
    # 设置 tool_result：可选的结构化工具结果，含原调用标识。
    tool_result: ToolResult | None = None


# 自动生成初始化等方法；frozen 阻止字段重新赋值，但不会深度冻结字典。
@dataclass(frozen=True)
# 定义 ModelResponse，将相关数据或操作组织在同一类型内。
class ModelResponse:
    # 设置 text：模型文本；只有工具请求时可以为空。
    text: str = ""
    # 保存工具请求元组；默认空元组表示没有工具调用。
    tool_calls: tuple[ToolCall, ...] = ()


# 定义结构化模型接口，实现类只需提供约定的方法，无须显式继承。
class ModelClient(Protocol):
    """D1 只需要消息输入；实际请求体快照在 D3/D4 增加。"""

    # 异步返回模型响应；此方法不在模型内部执行文件工具。
    async def complete(self, messages: tuple[Message, ...]) -> ModelResponse: ...

    # 异步释放模型资源，模拟器也保留该统一生命周期接口。
    async def aclose(self) -> None: ...


# 自动生成初始化等方法；frozen 阻止字段重新赋值，但不会深度冻结字典。
@dataclass(frozen=True)
# 定义 RunResult，将相关数据或操作组织在同一类型内。
class RunResult:
    # 声明 status 字段及其类型：运行终态；completed 只表示循环结束。
    status: str
    # 声明 answer 字段及其类型：最终回答或停止原因。
    answer: str
    # 声明 model_calls 字段及其类型：模型调用次数，包括最终回答所在的一次调用。
    model_calls: int
    # 保存本次运行累计的工具尝试次数。
    tool_calls: int
