"""两个受限文件工具：模型只能读 input，并向本次 output 写入。"""

import os
import stat
import tempfile
from collections.abc import Callable
from pathlib import Path, PureWindowsPath

from harness_agent.contracts import ToolCall, ToolResult

MAX_FILE_BYTES = 16 * 1024


def checked_path(root: Path, relative: str) -> Path:
    """先检查原路径组件，再 resolve；否则 resolve 会隐藏符号链接。"""
    windows = PureWindowsPath(relative)
    normalized = relative.replace("\\", "/")
    if (
        not relative
        or windows.drive
        or windows.root
        or ":" in relative
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
    ):
        raise ValueError("只接受不含盘符或跳转的相对路径")
    current = root
    for part in normalized.split("/"):
        current = current / part
        # lstat 不跟随链接；拒绝 Windows reparse point，包含 junction。
        if current.is_symlink():
            raise ValueError("不允许符号链接")
        try:
            attributes = current.lstat()
        except FileNotFoundError:
            continue
        if getattr(attributes, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError("不允许 reparse point")
    target = current.resolve()
    if not target.is_relative_to(root):
        raise ValueError("路径越界")
    return target


class ToolRegistry:
    """显式注册，不加载插件，也不允许模型选择任意 Python 函数。"""

    def __init__(self, input_root: Path, output_root: Path) -> None:
        self.input_root = input_root.resolve(strict=True)
        self.output_root = output_root.resolve(strict=True)
        if not self.input_root.is_dir() or not self.output_root.is_dir():
            raise ValueError("工具根路径必须是目录")
        self.handlers: dict[str, Callable[[dict[str, str]], str]] = {
            "read_file": self._read,
            "write_file": self._write,
        }

    def execute(self, call: ToolCall) -> ToolResult:
        """预期错误返回给模型；意外的程序错误继续向宿主传播。"""
        handler = self.handlers.get(call.name)
        if handler is None:
            return ToolResult(call.call_id, False, "未知工具", "unknown_tool")
        expected = {"path"} if call.name == "read_file" else {"path", "content"}
        if set(call.arguments) != expected or not all(
            isinstance(value, str) for value in call.arguments.values()
        ):
            return ToolResult(call.call_id, False, "参数不符合工具定义", "invalid_arguments")
        try:
            return ToolResult(call.call_id, True, handler(call.arguments))
        except (OSError, ValueError, UnicodeError) as error:
            return ToolResult(call.call_id, False, str(error), "file_error")

    def _read(self, arguments: dict[str, str]) -> str:
        path = checked_path(self.input_root, arguments["path"])
        if not path.is_file():
            raise ValueError("只能读取普通文件")
        with path.open("rb") as stream:
            data = stream.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise ValueError("文件超过 16 KiB")
        return data.decode("utf-8")

    def _write(self, arguments: dict[str, str]) -> str:
        path = checked_path(self.output_root, arguments["path"])
        data = arguments["content"].encode("utf-8")
        if len(data) > MAX_FILE_BYTES:
            raise ValueError("文件超过 16 KiB")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary: str | None = None
        try:
            # 同目录临时文件使 replace 不跨文件系统；先关闭再替换以兼容 Windows。
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                temporary = stream.name
                stream.write(data)
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                Path(temporary).unlink(missing_ok=True)
        return f"已写入 {arguments['path']}（{len(data)} 字节）"
