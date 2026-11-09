# OpenManus工具执行循环

## 技术实现

Manus继承ToolCallAgent，组合浏览器、Python执行、搜索、编辑、人工询问与终止工具。think请求带工具schema的模型输出，执行阶段将结果加入消息。

## 应用思路

适合研究多工具任务执行框架。模型的工具选择与程序的步数、停止状态和资源清理由不同层控制。

## 代码解析

### 声明可用工具集合

[OpenManus通用任务助手](../../应用侧/自动化与工具助手/OpenManus通用任务助手/案例说明.md) · [app/agent/manus.py，37–48行](../../应用侧/自动化与工具助手/OpenManus通用任务助手/app/agent/manus.py#L37-L48)

```python
available_tools: ToolCollection = Field(
    default_factory=lambda: ToolCollection(
        PythonExecute(),
        BrowserUseTool(),
        WebSearch(),
        StrReplaceEditor(),
        AskHuman(),
        Terminate(),
    )
)

special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])
```

default_factory为实例构建工具对象，避免共享可变状态；Terminate是显式停止工具，max_steps另行限制循环。

### 模型选择工具

[OpenManus通用任务助手](../../应用侧/自动化与工具助手/OpenManus通用任务助手/案例说明.md) · [app/agent/toolcall.py，47–57行](../../应用侧/自动化与工具助手/OpenManus通用任务助手/app/agent/toolcall.py#L47-L57)

```python
    response = await self.llm.ask_tool(
        messages=self.messages,
        system_msgs=(
            [Message.system_message(self.system_prompt)]
            if self.system_prompt
            else None
        ),
        tools=self.available_tools.to_params(),
        tool_choice=self.tool_choices,
    )
except ValueError:
```

messages携带当前过程，system_msgs提供约束，tools传入schema，tool_choice影响是否允许自动选择。外层处理token上限等异常。

## 应用方式差异

浏览器视觉版和文档检索扩展版保留完整项目，便于对照本地模块差异。相同工具循环只解释一次，不因项目名推断所有能力已可运行。
