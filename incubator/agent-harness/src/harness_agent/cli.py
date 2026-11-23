"""D1 入口只公开已经实现的 run 命令，不伪装支持 show/verify/API。"""

# 导入 argparse，用于命令行解析。
import argparse

# 导入 asyncio，用于异步事件循环。
import asyncio

# 导入 json，用于JSON 编解码。
import json

# 从 dataclasses 显式导入 asdict，声明本模块所需的依赖。
from dataclasses import asdict

# 从 pathlib 显式导入 Path，声明本模块所需的依赖。
from pathlib import Path

# 从 uuid 显式导入 uuid4，声明本模块所需的依赖。
from uuid import uuid4

# 从 harness_agent.model 显式导入 DemoModel，声明本模块所需的依赖。
from harness_agent.model import DemoModel

# 从 harness_agent.runner 显式导入 run_agent，声明本模块所需的依赖。
from harness_agent.runner import run_agent

# 从 harness_agent.tools 显式导入 MAX_FILE_BYTES, ToolRegistry，声明本模块所需的依赖。
from harness_agent.tools import MAX_FILE_BYTES, ToolRegistry


# 读取任务文件并限制大小，返回 UTF-8 文本。
def read_task(case: Path) -> str:
    """任务文件也限长，避免在进入循环前无限读取。"""
    # 进入下述资源或测试上下文；离开作用域时自动关闭文件或恢复测试环境。
    with (case / "task.txt").open("rb") as stream:
        # 最多读取限额加一字节，用额外一个字节判断是否超限。
        data = stream.read(MAX_FILE_BYTES + 1)
    # 检查条件 if len(data) > MAX_FILE_BYTES or not data.strip()；满足时进入下面的分支。
    if len(data) > MAX_FILE_BYTES or not data.strip():
        # 拒绝当前错误输入或状态，并通过异常保留具体原因。
        raise ValueError("任务为空或超过 16 KiB")
    # 按 UTF-8 解码小文件；编码无效时抛出异常。
    return data.decode("utf-8")


# CLI 主入口；返回整数退出码，负责参数、装配和终端展示。
def main() -> int:
    # 设置 parser：CLI 参数解析器，负责帮助信息与参数检查。
    parser = argparse.ArgumentParser(description="Agent Harness D1 离线工具循环")
    # 设置 subcommands：必选子命令集合，命令名保存到 command。
    subcommands = parser.add_subparsers(dest="command", required=True)
    # 设置 run：当前唯一实现的 run 子命令。
    run = subcommands.add_parser("run", help="执行固定的离线文件演示")
    # 要求提供案例目录，并将命令行字符串转换为 Path。
    run.add_argument("--case", type=Path, required=True)
    # 设置 arguments：参数数据：在 CLI 中来自命令行，在工具契约中是字符串字典。
    arguments = parser.parse_args()
    # 设置 case：当前案例目录，用 Path 处理文件路径。
    case = Path(arguments.case).resolve()
    # 开始可能返回或抛异常的一组操作；后面的异常处理或清理分支负责收尾。
    try:
        # 设置 task：经过限长和编码检查的用户任务文本。
        task = read_task(case)
        # 检查条件 if not (case / "input").is_dir()；满足时进入下面的分支。
        if not (case / "input").is_dir():
            # 拒绝当前错误输入或状态，并通过异常保留具体原因。
            raise ValueError("案例缺少 input 目录")
        # 设置 run_id：随机运行标识，用于隔离不同运行的输出。
        run_id = uuid4().hex
        # 设置 output：本次输出位置；测试中也用于捕获终端文本。
        output = Path(".runs") / run_id / "output"
        # 创建运行目录及父目录，不覆盖同名已有目录。
        output.mkdir(parents=True)
        # 设置 tools：绑定输入和输出根目录的工具注册表。
        tools = ToolRegistry(case / "input", output)
        # 设置 result：调用返回的实际结果，供程序继续处理或测试断言。
        result = asyncio.run(run_agent(task, DemoModel(), tools))
        # 向终端显示运行摘要或当前阶段的明确提示。
        print(
            # 将下面的运行摘要转换为 JSON 文本。
            json.dumps(
                # 合并运行标识、输出路径和 dataclass 摘要；双星号展开摘要字典。
                {"run_id": run_id, "output": str(output), **asdict(result)},
                # JSON 保留中文字符，便于直接阅读。
                ensure_ascii=False,
                # 用两格缩进展示 JSON 的层次。
                indent=2,
                # 结束当前这一层函数调用或容器声明，回到外层表达式。
            )
            # 结束当前这一层函数调用或容器声明，回到外层表达式。
        )
        # 向终端显示运行摘要或当前阶段的明确提示。
        print("D1：循环已结束，自动验收与持久轨迹尚未实现。")
        # D1 循环正常结束返回零，否则返回一；后续阶段再增加完整验收语义。
        return 0 if result.status == "completed" else 1
    # 捕获 KeyboardInterrupt，执行下面的错误反馈或恢复逻辑。
    except KeyboardInterrupt:
        # 向终端显示运行摘要或当前阶段的明确提示。
        print("D1：已中断；取消记录与收尾保证将在 D2/D3 实现。")
        # 返回约定的用户中断退出码。
        return 130
    # 捕获 (OSError, ValueError) as error，执行下面的错误反馈或恢复逻辑。
    except (OSError, ValueError) as error:
        # 向终端显示运行摘要或当前阶段的明确提示。
        print(f"运行失败：{error}")
        # 返回非零退出码，告知调用方运行失败。
        return 1
