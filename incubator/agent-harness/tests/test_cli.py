"""CLI 使用临时工作目录，检查实际落地文件和明确的失败反馈。"""

# 导入 contextlib，用于上下文管理辅助。
import contextlib

# 导入 io，用于内存文本流。
import io

# 导入 json，用于JSON 编解码。
import json

# 导入 tempfile，用于临时文件和目录。
import tempfile

# 导入 unittest，用于自动测试框架。
import unittest

# 从 pathlib 显式导入 Path，声明本模块所需的依赖。
from pathlib import Path

# 从 unittest.mock 显式导入 patch，声明本模块所需的依赖。
from unittest.mock import patch

# 从 harness_agent.cli 显式导入 main, read_task，声明本模块所需的依赖。
from harness_agent.cli import main, read_task


# 定义 CliTests，将相关数据或操作组织在同一类型内。
class CliTests(unittest.TestCase):
    # 验证 CLI 真正生成结果文件，并显示三次模型调用。
    def test_run_command_creates_artifact(self) -> None:
        # 进入下述资源或测试上下文；离开作用域时自动关闭文件或恢复测试环境。
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            # 设置 case：当前案例目录，用 Path 处理文件路径。
            case = Path("demo")
            # 建立本测试需要的独立目录。
            (case / "input").mkdir(parents=True)
            # 准备本测试独立的输入文件，避免依赖仓库共享状态。
            (case / "task.txt").write_text("extract", encoding="utf-8")
            # 准备本测试独立的输入文件，避免依赖仓库共享状态。
            (case / "input/brief.txt").write_text("owner: cli-test", encoding="utf-8")
            # 设置 output：本次输出位置；测试中也用于捕获终端文本。
            output = io.StringIO()
            # 进入下述资源或测试上下文；离开作用域时自动关闭文件或恢复测试环境。
            with (
                # 临时替换指定参数或函数，测试作用域结束后自动恢复原值。
                patch("sys.argv", ["harness", "run", "--case", "demo"]),
                # 把终端输出重定向到内存，供断言检查并保持测试报告清晰。
                contextlib.redirect_stdout(output),
                # 结束上面的多行条件或上下文头，后续缩进属于该分支。
            ):
                # 断言 D1 正常循环的 CLI 退出码为零；不代表完整自动验收。
                self.assertEqual(main(), 0)
            # 设置 artifact：在临时工作区中找到的实际结果文件。
            artifact = next(Path(".runs").glob("*/output/result.json"))
            # 断言下列实际值满足预期；不满足时让当前测试失败并显示差异。
            self.assertEqual(json.loads(artifact.read_text()), {"owner": "cli-test"})
            # 断言下列实际值满足预期；不满足时让当前测试失败并显示差异。
            self.assertIn('"model_calls": 3', output.getvalue())

    # 验证案例不存在时返回失败，且不创建运行输出目录。
    def test_missing_case_fails_without_creating_run(self) -> None:
        # 进入下述资源或测试上下文；离开作用域时自动关闭文件或恢复测试环境。
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            # 进入下述资源或测试上下文；离开作用域时自动关闭文件或恢复测试环境。
            with (
                # 临时替换指定参数或函数，测试作用域结束后自动恢复原值。
                patch("sys.argv", ["harness", "run", "--case", "missing"]),
                # 把终端输出重定向到内存，供断言检查并保持测试报告清晰。
                contextlib.redirect_stdout(io.StringIO()),
                # 结束上面的多行条件或上下文头，后续缩进属于该分支。
            ):
                # 断言缺失案例返回运行失败码，而非正常退出。
                self.assertEqual(main(), 1)
            # 断言下列实际值满足预期；不满足时让当前测试失败并显示差异。
            self.assertFalse(Path(".runs").exists())

    # 验证任务文件为空或超过大小上限时被拒绝。
    def test_task_size_and_empty_input(self) -> None:
        # 进入下述资源或测试上下文；离开作用域时自动关闭文件或恢复测试环境。
        with tempfile.TemporaryDirectory() as directory:
            # 设置 case：当前案例目录，用 Path 处理文件路径。
            case = Path(directory)
            # 按顺序遍历 data in [b"", b"x" * 16385]，逐项执行下面的操作。
            for data in [b"", b"x" * 16385]:
                # 准备本测试独立的输入文件，避免依赖仓库共享状态。
                (case / "task.txt").write_bytes(data)
                # 预期下面的读取会抛出 ValueError，没有抛出则测试失败。
                with self.assertRaises(ValueError):
                    # 调用真实任务读取函数，核对空内容或超大文件会被拒绝。
                    read_task(case)

    # 通过异常替身验证 CLI 中断退出码；不代替真实控制台验证。
    def test_keyboard_interrupt_has_explicit_exit_code(self) -> None:
        # 进入下述资源或测试上下文；离开作用域时自动关闭文件或恢复测试环境。
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            # 进入下述资源或测试上下文；离开作用域时自动关闭文件或恢复测试环境。
            with (
                # 临时替换指定参数或函数，测试作用域结束后自动恢复原值。
                patch("sys.argv", ["harness", "run", "--case", "demo"]),
                # 临时替换指定参数或函数，测试作用域结束后自动恢复原值。
                patch("harness_agent.cli.read_task", side_effect=KeyboardInterrupt),
                # 把终端输出重定向到内存，供断言检查并保持测试报告清晰。
                contextlib.redirect_stdout(io.StringIO()),
                # 结束上面的多行条件或上下文头，后续缩进属于该分支。
            ):
                # 断言捕获模拟 KeyboardInterrupt 后返回约定中断码；这不是实际键盘测试。
                self.assertEqual(main(), 130)
