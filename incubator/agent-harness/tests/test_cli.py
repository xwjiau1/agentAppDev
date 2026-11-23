"""CLI 使用临时工作目录，检查实际落地文件和明确的失败反馈。"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness_agent.cli import main, read_task


class CliTests(unittest.TestCase):
    def test_run_command_creates_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            case = Path("demo")
            (case / "input").mkdir(parents=True)
            (case / "task.txt").write_text("extract", encoding="utf-8")
            (case / "input/brief.txt").write_text("owner: cli-test", encoding="utf-8")
            output = io.StringIO()
            with (
                patch("sys.argv", ["harness", "run", "--case", "demo"]),
                contextlib.redirect_stdout(output),
            ):
                self.assertEqual(main(), 0)
            artifact = next(Path(".runs").glob("*/output/result.json"))
            self.assertEqual(json.loads(artifact.read_text()), {"owner": "cli-test"})
            self.assertIn('"model_calls": 3', output.getvalue())

    def test_missing_case_fails_without_creating_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            with (
                patch("sys.argv", ["harness", "run", "--case", "missing"]),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(main(), 1)
            self.assertFalse(Path(".runs").exists())

    def test_task_size_and_empty_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = Path(directory)
            for data in [b"", b"x" * 16385]:
                (case / "task.txt").write_bytes(data)
                with self.assertRaises(ValueError):
                    read_task(case)

    def test_keyboard_interrupt_has_explicit_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            with (
                patch("sys.argv", ["harness", "run", "--case", "demo"]),
                patch("harness_agent.cli.read_task", side_effect=KeyboardInterrupt),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(main(), 130)
