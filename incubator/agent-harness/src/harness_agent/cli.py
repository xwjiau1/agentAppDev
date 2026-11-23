"""D1 入口只公开已经实现的 run 命令，不伪装支持 show/verify/API。"""

import argparse
import asyncio
import json
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from harness_agent.model import DemoModel
from harness_agent.runner import run_agent
from harness_agent.tools import MAX_FILE_BYTES, ToolRegistry


def read_task(case: Path) -> str:
    """任务文件也限长，避免在进入循环前无限读取。"""
    with (case / "task.txt").open("rb") as stream:
        data = stream.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES or not data.strip():
        raise ValueError("任务为空或超过 16 KiB")
    return data.decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent Harness D1 离线工具循环")
    subcommands = parser.add_subparsers(dest="command", required=True)
    run = subcommands.add_parser("run", help="执行固定的离线文件演示")
    run.add_argument("--case", type=Path, required=True)
    arguments = parser.parse_args()
    case = Path(arguments.case).resolve()
    try:
        task = read_task(case)
        if not (case / "input").is_dir():
            raise ValueError("案例缺少 input 目录")
        run_id = uuid4().hex
        output = Path(".runs") / run_id / "output"
        output.mkdir(parents=True)
        tools = ToolRegistry(case / "input", output)
        result = asyncio.run(run_agent(task, DemoModel(), tools))
        print(
            json.dumps(
                {"run_id": run_id, "output": str(output), **asdict(result)},
                ensure_ascii=False,
                indent=2,
            )
        )
        print("D1：循环已结束，自动验收与持久轨迹尚未实现。")
        return 0 if result.status == "completed" else 1
    except KeyboardInterrupt:
        print("D1：已中断；取消记录与收尾保证将在 D2/D3 实现。")
        return 130
    except (OSError, ValueError) as error:
        print(f"运行失败：{error}")
        return 1
