"""D1 契约测试：从真实临时文件核对行为，而非复刻实现。"""

# 导入 json，用于JSON 编解码。
import json

# 导入 tempfile，用于临时文件和目录。
import tempfile

# 导入 unittest，用于自动测试框架。
import unittest

# 从 pathlib 显式导入 Path，声明本模块所需的依赖。
from pathlib import Path

# 从 harness_agent.contracts 显式导入 Message, ModelResponse, ToolCall，声明本模块所需的依赖。
from harness_agent.contracts import Message, ModelResponse, ToolCall

# 从 harness_agent.model 显式导入 DemoModel，声明本模块所需的依赖。
from harness_agent.model import DemoModel

# 从 harness_agent.runner 显式导入 run_agent，声明本模块所需的依赖。
from harness_agent.runner import run_agent

# 从 harness_agent.tools 显式导入 MAX_FILE_BYTES, ToolRegistry，声明本模块所需的依赖。
from harness_agent.tools import MAX_FILE_BYTES, ToolRegistry


# 定义 CoreTests，将相关数据或操作组织在同一类型内。
class CoreTests(unittest.IsolatedAsyncioTestCase):
    # 每项测试运行前创建独立的输入、输出目录和工具实例。
    def setUp(self) -> None:
        # 设置 self.temporary：本测试独占的临时目录，防止污染项目与其他测试。
        self.temporary = tempfile.TemporaryDirectory()
        # 注册测试结束时的清理回调，即使断言失败也释放临时目录。
        self.addCleanup(self.temporary.cleanup)
        # 设置 self.root：临时目录对应的 Path 对象。
        self.root = Path(self.temporary.name)
        # 设置 self.input：测试用的可读输入根目录。
        self.input = self.root / "input"
        # 设置 self.output：测试用的可写输出根目录。
        self.output = self.root / "output"
        # 建立本测试需要的独立目录。
        self.input.mkdir()
        # 建立本测试需要的独立目录。
        self.output.mkdir()
        # 设置 self.tools：使用临时根目录的真实工具注册表。
        self.tools = ToolRegistry(self.input, self.output)

    # 用与演示不同的输入验证输出来自读取结果，而非硬编码验收答案。
    async def test_demo_reads_actual_input_without_expected_file(self) -> None:
        # 准备本测试独立的输入文件，避免依赖仓库共享状态。
        (self.input / "brief.txt").write_text("owner: different\nproject: 测试\n", encoding="utf-8")
        # 设置 result：调用返回的实际结果，供程序继续处理或测试断言。
        result = await run_agent("生成 JSON", DemoModel(), self.tools)
        # 断言下列实际值满足预期；不满足时让当前测试失败并显示差异。
        self.assertEqual(
            # 给上面的断言传入实际字段元组与预期元组，按相同顺序比较。
            (result.status, result.model_calls, result.tool_calls),
            # 预期循环正常结束，并使用三次模型调用和两次工具调用。
            ("completed", 3, 2),
            # 结束当前这一层函数调用或容器声明，回到外层表达式。
        )
        # 设置 actual：从真实输出文件解析出的 JSON，而非仅检查模型回答。
        actual = json.loads((self.output / "result.json").read_text(encoding="utf-8"))
        # 断言下列实际值满足预期；不满足时让当前测试失败并显示差异。
        self.assertEqual(actual, {"owner": "different", "project": "测试"})

    # 验证反复请求工具的模型在八次调用后停止，并释放模型资源。
    async def test_limit_and_client_cleanup(self) -> None:
        # 定义 RepeatingModel，将相关数据或操作组织在同一类型内。
        class RepeatingModel:
            # 类属性提供默认未关闭状态；aclose 随后在实例上写入 self.closed。
            closed = False

            # 异步返回模型响应；此方法不在模型内部执行文件工具。
            async def complete(self, messages: tuple[Message, ...]) -> ModelResponse:
                # 构造模型响应；本方法只表达下一步请求，不直接执行文件工具。
                return ModelResponse(tool_calls=(ToolCall("bad", "unknown", {}),))

            # 异步释放模型资源，模拟器也保留该统一生命周期接口。
            async def aclose(self) -> None:
                # 设置 self.closed：标记替身已经收到关闭请求，供测试断言。
                self.closed = True

        # 设置 model：本用例的模型替身，用于观察循环或清理行为。
        model = RepeatingModel()
        # 设置 result：调用返回的实际结果，供程序继续处理或测试断言。
        result = await run_agent("continue", model, self.tools)
        # 断言下列实际值满足预期；不满足时让当前测试失败并显示差异。
        self.assertEqual((result.status, result.model_calls), ("limited", 8))
        # 确认正常达限或模型失败后，Runner 都调用了模型关闭方法。
        self.assertTrue(model.closed)

    # 验证模型抛出异常时，finally 仍关闭客户端。
    async def test_model_failure_still_closes_client(self) -> None:
        # 定义 BrokenModel，将相关数据或操作组织在同一类型内。
        class BrokenModel:
            # 类属性提供默认未关闭状态；aclose 随后在实例上写入 self.closed。
            closed = False

            # 异步返回模型响应；此方法不在模型内部执行文件工具。
            async def complete(self, messages: tuple[Message, ...]) -> ModelResponse:
                # 拒绝当前错误输入或状态，并通过异常保留具体原因。
                raise ValueError("broken")

            # 异步释放模型资源，模拟器也保留该统一生命周期接口。
            async def aclose(self) -> None:
                # 设置 self.closed：标记替身已经收到关闭请求，供测试断言。
                self.closed = True

        # 设置 model：本用例的模型替身，用于观察循环或清理行为。
        model = BrokenModel()
        # 要求同时匹配异常类型和 broken 信息，确认模型错误向外传播。
        with self.assertRaisesRegex(ValueError, "broken"):
            # 等待异步运行；外层异常断言验证这次失败不会被静默吞掉。
            await run_agent("task", model, self.tools)
        # 确认正常达限或模型失败后，Runner 都调用了模型关闭方法。
        self.assertTrue(model.closed)

    # 验证多种越界路径均被拒绝，且外部文件未被写入。
    def test_path_escape_is_rejected(self) -> None:
        # 按顺序遍历 path in ["../outside", "/absolute", "C:relative", "\\\\host\\share", "x:stream"]，逐项执行下面的操作。
        for path in ["../outside", "/absolute", "C:relative", "\\\\host\\share", "x:stream"]:
            # 进入下述资源或测试上下文；离开作用域时自动关闭文件或恢复测试环境。
            with self.subTest(path=path):
                # 设置 result：调用返回的实际结果，供程序继续处理或测试断言。
                result = self.tools.execute(
                    # 补全上面 Assign 语句的测试输入，交给对应操作或断言。
                    ToolCall("1", "write_file", {"path": path, "content": "x"})
                    # 结束当前这一层函数调用或容器声明，回到外层表达式。
                )
                # 确认被拒绝的输入返回失败，不能伪装为工具成功。
                self.assertFalse(result.ok)
        # 断言下列实际值满足预期；不满足时让当前测试失败并显示差异。
        self.assertFalse((self.root / "outside").exists())

    # 验证未知工具、缺少参数和额外参数都会返回失败。
    def test_tool_validation(self) -> None:
        # 按顺序遍历 call in [，逐项执行下面的操作。
        for call in [
            # 补全上面 For 语句的测试输入，交给对应操作或断言。
            ToolCall("1", "unknown", {}),
            # 补全上面 For 语句的测试输入，交给对应操作或断言。
            ToolCall("2", "read_file", {}),
            # 补全上面 For 语句的测试输入，交给对应操作或断言。
            ToolCall("3", "read_file", {"path": "x", "extra": "x"}),
            # 结束上面的多行条件或上下文头，后续缩进属于该分支。
        ]:
            # 进入下述资源或测试上下文；离开作用域时自动关闭文件或恢复测试环境。
            with self.subTest(call=call):
                # 断言下列实际值满足预期；不满足时让当前测试失败并显示差异。
                self.assertFalse(self.tools.execute(call).ok)

    # 验证超长文件、无效 UTF-8、缺失文件与中文超限写入。
    def test_size_limit_and_utf8(self) -> None:
        # 准备本测试独立的输入文件，避免依赖仓库共享状态。
        (self.input / "large").write_bytes(b"x" * (MAX_FILE_BYTES + 1))
        # 准备本测试独立的输入文件，避免依赖仓库共享状态。
        (self.input / "invalid").write_bytes(b"\xff")
        # 按顺序遍历 path in ["large", "invalid", "missing"]，逐项执行下面的操作。
        for path in ["large", "invalid", "missing"]:
            # 断言下列实际值满足预期；不满足时让当前测试失败并显示差异。
            self.assertFalse(self.tools.execute(ToolCall("1", "read_file", {"path": path})).ok)
        # 设置 result：调用返回的实际结果，供程序继续处理或测试断言。
        result = self.tools.execute(
            # 开始构造工具调用，依次指定调用 ID、工具名称与参数。
            ToolCall(
                # 指定这项工具测试使用的调用标识或字符串参数。
                "2",
                # 选择受限写入工具。
                "write_file",
                # 补全上面 Assign 语句的测试输入，交给对应操作或断言。
                {
                    # 指定测试写入目标的相对名称。
                    "path": "large",
                    # 使用多字节中文构造超限内容，检验限制按字节而不是字符数计算。
                    "content": "中" * MAX_FILE_BYTES,
                    # 结束当前这一层函数调用或容器，并用逗号与后面的项目分隔。
                },
                # 结束当前这一层函数调用或容器声明，回到外层表达式。
            )
            # 结束当前这一层函数调用或容器声明，回到外层表达式。
        )
        # 确认被拒绝的输入返回失败，不能伪装为工具成功。
        self.assertFalse(result.ok)
        # 断言下列实际值满足预期；不满足时让当前测试失败并显示差异。
        self.assertFalse((self.output / "large").exists())

    # 验证覆盖后保存新内容，且目录中不残留临时文件。
    def test_atomic_overwrite_cleans_temporary_file(self) -> None:
        # 按顺序遍历 text in ["before", "after"]，逐项执行下面的操作。
        for text in ["before", "after"]:
            # 设置 result：调用返回的实际结果，供程序继续处理或测试断言。
            result = self.tools.execute(
                # 补全上面 Assign 语句的测试输入，交给对应操作或断言。
                ToolCall("1", "write_file", {"path": "nested/a", "content": text})
                # 结束当前这一层函数调用或容器声明，回到外层表达式。
            )
            # 断言下列实际值满足预期；不满足时让当前测试失败并显示差异。
            self.assertTrue(result.ok)
        # 断言下列实际值满足预期；不满足时让当前测试失败并显示差异。
        self.assertEqual((self.output / "nested/a").read_text(), "after")
        # 断言下列实际值满足预期；不满足时让当前测试失败并显示差异。
        self.assertEqual([p.name for p in (self.output / "nested").iterdir()], ["a"])
