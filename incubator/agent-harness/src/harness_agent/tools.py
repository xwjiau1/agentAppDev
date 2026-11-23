"""两个受限文件工具：模型只能读 input，并向本次 output 写入。"""

# 导入 os，用于底层文件操作。
import os

# 导入 stat，用于文件属性标志。
import stat

# 导入 tempfile，用于临时文件和目录。
import tempfile

# 从 collections.abc 显式导入 Callable，声明本模块所需的依赖。
from collections.abc import Callable

# 从 pathlib 显式导入 Path, PureWindowsPath，声明本模块所需的依赖。
from pathlib import Path, PureWindowsPath

# 从 harness_agent.contracts 显式导入 ToolCall, ToolResult，声明本模块所需的依赖。
from harness_agent.contracts import ToolCall, ToolResult

# 设置 MAX_FILE_BYTES：16 KiB 文件字节上限，中文字符可能占多个字节。
MAX_FILE_BYTES = 16 * 1024


# 校验模型给出的相对路径，返回允许根目录内的目标。
def checked_path(root: Path, relative: str) -> Path:
    """先检查原路径组件，再 resolve；否则 resolve 会隐藏符号链接。"""
    # 设置 windows：按 Windows 语法检查路径，从而跨平台识别盘符与 UNC。
    windows = PureWindowsPath(relative)
    # 设置 normalized：把反斜杠统一成斜杠，便于逐段检查路径。
    normalized = relative.replace("\\", "/")
    # 检查条件 if (；满足时进入下面的分支。
    if (
        # 拒绝空路径，防止根目录被当成文件目标。
        not relative
        # 拒绝盘符或 UNC 驱动部分，也拒绝 C:relative 这种盘符相对路径。
        or windows.drive
        # 拒绝根目录标记，例如 /absolute。
        or windows.root
        # 拒绝冒号，阻止 Windows 备用数据流等特殊路径。
        or ":" in relative
        # 拒绝空段、当前目录和上级目录跳转。
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
        # 结束上面的多行条件或上下文头，后续缩进属于该分支。
    ):
        # 拒绝当前错误输入或状态，并通过异常保留具体原因。
        raise ValueError("只接受不含盘符或跳转的相对路径")
    # 设置 current：正在逐段校验的路径。
    current = root
    # 按顺序遍历 part in normalized.split("/")，逐项执行下面的操作。
    for part in normalized.split("/"):
        # 设置 current：正在逐段校验的路径。
        current = current / part
        # lstat 不跟随链接；拒绝 Windows reparse point，包含 junction。
        # 拒绝符号链接；必须在 resolve 之前检查原始路径组件。
        if current.is_symlink():
            # 拒绝当前错误输入或状态，并通过异常保留具体原因。
            raise ValueError("不允许符号链接")
        # 开始可能返回或抛异常的一组操作；后面的异常处理或清理分支负责收尾。
        try:
            # 设置 attributes：组件自身的文件属性，lstat 不跟随符号链接。
            attributes = current.lstat()
        # 捕获 FileNotFoundError，执行下面的错误反馈或恢复逻辑。
        except FileNotFoundError:
            # 当前组件尚不存在，跳过属性检查，继续检查剩余路径组件。
            continue
        # 检查 Windows reparse 标志，包括 junction；其他平台无该属性时使用零。
        if getattr(attributes, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            # 拒绝当前错误输入或状态，并通过异常保留具体原因。
            raise ValueError("不允许 reparse point")
    # 设置 target：规范化绝对路径，用于最终检查是否仍在允许根目录内。
    target = current.resolve()
    # 最终绝对路径必须仍属于允许根目录，不能逃逸到其他目录。
    if not target.is_relative_to(root):
        # 拒绝当前错误输入或状态，并通过异常保留具体原因。
        raise ValueError("路径越界")
    # 只把经过校验的目标路径交给后面的文件操作。
    return target


# 定义 ToolRegistry，将相关数据或操作组织在同一类型内。
class ToolRegistry:
    """显式注册，不加载插件，也不允许模型选择任意 Python 函数。"""

    # 初始化工具实例，为本次运行固定可读和可写根目录。
    def __init__(self, input_root: Path, output_root: Path) -> None:
        # 设置 self.input_root：工具可读的真实输入根目录，strict=True 要求它已经存在。
        self.input_root = input_root.resolve(strict=True)
        # 设置 self.output_root：本次运行可写的真实输出根目录。
        self.output_root = output_root.resolve(strict=True)
        # 检查条件 if not self.input_root.is_dir() or not self.output_root.is_dir()；满足时进入下面的分支。
        if not self.input_root.is_dir() or not self.output_root.is_dir():
            # 拒绝当前错误输入或状态，并通过异常保留具体原因。
            raise ValueError("工具根路径必须是目录")
        # 设置 self.handlers：工具名称到处理函数的显式注册表，不允许任意 Python 函数。
        self.handlers: dict[str, Callable[[dict[str, str]], str]] = {
            # 只把 read_file 这个公开名称映射到受限读取方法。
            "read_file": self._read,
            # 只把 write_file 这个公开名称映射到受限写入方法。
            "write_file": self._write,
            # 结束当前这一层函数调用或容器声明，回到外层表达式。
        }

    # 统一校验工具名称与参数，再执行处理函数并包装结果。
    def execute(self, call: ToolCall) -> ToolResult:
        """预期错误返回给模型；意外的程序错误继续向宿主传播。"""
        # 设置 handler：当前工具对应的处理函数，未知名称时为 None。
        handler = self.handlers.get(call.name)
        # 名称未注册，不运行处理函数，返回 unknown_tool 错误。
        if handler is None:
            # 把执行状态、内容和原调用 ID 包装为工具结果，供模型或宿主消费。
            return ToolResult(call.call_id, False, "未知工具", "unknown_tool")
        # 设置 expected：该工具允许的参数名集合，拒绝缺参和额外参数。
        expected = {"path"} if call.name == "read_file" else {"path", "content"}
        # 检查条件 if set(call.arguments) != expected or not all(；满足时进入下面的分支。
        if set(call.arguments) != expected or not all(
            # 逐个检查参数值确实是字符串；类型标注不能替代运行时校验。
            isinstance(value, str)
            # 遍历每个参数值，让 all 判断这些类型检查是否全部成立。
            for value in call.arguments.values()
            # 结束上面的多行条件或上下文头，后续缩进属于该分支。
        ):
            # 把执行状态、内容和原调用 ID 包装为工具结果，供模型或宿主消费。
            return ToolResult(call.call_id, False, "参数不符合工具定义", "invalid_arguments")
        # 开始可能返回或抛异常的一组操作；后面的异常处理或清理分支负责收尾。
        try:
            # 把执行状态、内容和原调用 ID 包装为工具结果，供模型或宿主消费。
            return ToolResult(call.call_id, True, handler(call.arguments))
        # 捕获 (OSError, ValueError, UnicodeError) as error，执行下面的错误反馈或恢复逻辑。
        except (OSError, ValueError, UnicodeError) as error:
            # 把执行状态、内容和原调用 ID 包装为工具结果，供模型或宿主消费。
            return ToolResult(call.call_id, False, str(error), "file_error")

    # 读取受大小限制的 UTF-8 普通文件。
    def _read(self, arguments: dict[str, str]) -> str:
        # 将读取路径限制在 input 根目录，先校验再打开文件。
        path = checked_path(self.input_root, arguments["path"])
        # 只读取普通文件，拒绝目录和特殊文件。
        if not path.is_file():
            # 拒绝当前错误输入或状态，并通过异常保留具体原因。
            raise ValueError("只能读取普通文件")
        # 进入下述资源或测试上下文；离开作用域时自动关闭文件或恢复测试环境。
        with path.open("rb") as stream:
            # 最多读取限额加一字节，用额外一个字节判断是否超限。
            data = stream.read(MAX_FILE_BYTES + 1)
        # 按实际字节数检查大小，超出 16 KiB 就拒绝。
        if len(data) > MAX_FILE_BYTES:
            # 拒绝当前错误输入或状态，并通过异常保留具体原因。
            raise ValueError("文件超过 16 KiB")
        # 按 UTF-8 解码小文件；编码无效时抛出异常。
        return data.decode("utf-8")

    # 通过同目录临时文件安全替换输出文件。
    def _write(self, arguments: dict[str, str]) -> str:
        # 将写入路径限制在本次 output 根目录，先校验再写入。
        path = checked_path(self.output_root, arguments["path"])
        # 先按 UTF-8 编码；中文字符数不能直接当作文件字节数。
        data = arguments["content"].encode("utf-8")
        # 按实际字节数检查大小，超出 16 KiB 就拒绝。
        if len(data) > MAX_FILE_BYTES:
            # 拒绝当前错误输入或状态，并通过异常保留具体原因。
            raise ValueError("文件超过 16 KiB")
        # 创建缺失的父目录，已存在时不报错。
        path.parent.mkdir(parents=True, exist_ok=True)
        # 设置 temporary：临时文件路径；创建前为 None，供 finally 清理。
        temporary: str | None = None
        # 开始可能返回或抛异常的一组操作；后面的异常处理或清理分支负责收尾。
        try:
            # 同目录临时文件使 replace 不跨文件系统；先关闭再替换以兼容 Windows。
            # 进入下述资源或测试上下文；离开作用域时自动关闭文件或恢复测试环境。
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                # 设置 temporary：临时文件路径；创建前为 None，供 finally 清理。
                temporary = stream.name
                # 把完整字节写入临时文件，暂不覆盖目标文件。
                stream.write(data)
            # 文件已关闭后再替换目标，兼容 Windows；同文件系统替换是原子的。
            os.replace(temporary, path)
        # 不论正常返回或抛出异常，都执行以下清理步骤。
        finally:
            # 确实创建过临时文件时，才进入残留文件清理。
            if temporary is not None:
                # 清理残留临时文件；replace 已移走文件时不报错。
                Path(temporary).unlink(missing_ok=True)
        # 返回写入文件的相对路径与实际字节数，供后续模型步骤读取。
        return f"已写入 {arguments['path']}（{len(data)} 字节）"
