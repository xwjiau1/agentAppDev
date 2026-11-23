"""D1 契约测试：从真实临时文件核对行为，而非复刻实现。"""

import json
import tempfile
import unittest
from pathlib import Path

from harness_agent.contracts import Message, ModelResponse, ToolCall
from harness_agent.model import DemoModel
from harness_agent.runner import run_agent
from harness_agent.tools import MAX_FILE_BYTES, ToolRegistry


class CoreTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.input = self.root / "input"
        self.output = self.root / "output"
        self.input.mkdir()
        self.output.mkdir()
        self.tools = ToolRegistry(self.input, self.output)

    async def test_demo_reads_actual_input_without_expected_file(self) -> None:
        (self.input / "brief.txt").write_text("owner: different\nproject: 测试\n", encoding="utf-8")
        result = await run_agent("生成 JSON", DemoModel(), self.tools)
        self.assertEqual(
            (result.status, result.model_calls, result.tool_calls), ("completed", 3, 2)
        )
        actual = json.loads((self.output / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(actual, {"owner": "different", "project": "测试"})

    async def test_limit_and_client_cleanup(self) -> None:
        class RepeatingModel:
            closed = False

            async def complete(self, messages: tuple[Message, ...]) -> ModelResponse:
                return ModelResponse(tool_calls=(ToolCall("bad", "unknown", {}),))

            async def aclose(self) -> None:
                self.closed = True

        model = RepeatingModel()
        result = await run_agent("continue", model, self.tools)
        self.assertEqual((result.status, result.model_calls), ("limited", 8))
        self.assertTrue(model.closed)

    async def test_model_failure_still_closes_client(self) -> None:
        class BrokenModel:
            closed = False

            async def complete(self, messages: tuple[Message, ...]) -> ModelResponse:
                raise ValueError("broken")

            async def aclose(self) -> None:
                self.closed = True

        model = BrokenModel()
        with self.assertRaisesRegex(ValueError, "broken"):
            await run_agent("task", model, self.tools)
        self.assertTrue(model.closed)

    def test_path_escape_is_rejected(self) -> None:
        for path in ["../outside", "/absolute", "C:relative", "\\\\host\\share", "x:stream"]:
            with self.subTest(path=path):
                result = self.tools.execute(
                    ToolCall("1", "write_file", {"path": path, "content": "x"})
                )
                self.assertFalse(result.ok)
        self.assertFalse((self.root / "outside").exists())

    def test_tool_validation(self) -> None:
        for call in [
            ToolCall("1", "unknown", {}),
            ToolCall("2", "read_file", {}),
            ToolCall("3", "read_file", {"path": "x", "extra": "x"}),
        ]:
            with self.subTest(call=call):
                self.assertFalse(self.tools.execute(call).ok)

    def test_size_limit_and_utf8(self) -> None:
        (self.input / "large").write_bytes(b"x" * (MAX_FILE_BYTES + 1))
        (self.input / "invalid").write_bytes(b"\xff")
        for path in ["large", "invalid", "missing"]:
            self.assertFalse(self.tools.execute(ToolCall("1", "read_file", {"path": path})).ok)
        result = self.tools.execute(
            ToolCall(
                "2",
                "write_file",
                {
                    "path": "large",
                    "content": "中" * MAX_FILE_BYTES,
                },
            )
        )
        self.assertFalse(result.ok)
        self.assertFalse((self.output / "large").exists())

    def test_atomic_overwrite_cleans_temporary_file(self) -> None:
        for text in ["before", "after"]:
            result = self.tools.execute(
                ToolCall("1", "write_file", {"path": "nested/a", "content": text})
            )
            self.assertTrue(result.ok)
        self.assertEqual((self.output / "nested/a").read_text(), "after")
        self.assertEqual([p.name for p in (self.output / "nested").iterdir()], ["a"])
