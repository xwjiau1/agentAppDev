# subprocess.run超时输出与退出码

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

subprocess.run启动子进程并等待完成，返回CompletedProcess。capture_output收集输出，timeout限制等待，check控制非零退出码是否抛异常。

## 面试问答

**问：stderr有内容就表示失败吗？** 不一定，通常结合returncode与工具约定判断。

**问：shell=False就自动安全了吗？** 只能避免部分Shell解释，程序参数、路径与权限仍需校验。

## 实际案例与代码

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 显式参数调用Git

[s13_agent_teams/code.py，370–380行](../../应用侧/自动化与工具助手/通用AgentHarness/s13_agent_teams/code.py#L370-L380)

```python
def _run_git(args: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    """Run Git without shell interpolation and preserve machine output."""
    try:
        result = subprocess.run(
            ["git", *args], cwd=cwd or WORKDIR,
            capture_output=True, text=True, errors="replace", timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"{type(exc).__name__}: {exc}"
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output or "(no output)"
```

参数列表把git和实参分开；根据实际returncode判断并记录stdout/stderr，具体超时与编码选项见原调用。

## 易错点与追问

字符串shell命令与参数列表行为不同，不要用简单拼接处理不受信任输入。也不要把cwd理解成进程权限沙箱。
