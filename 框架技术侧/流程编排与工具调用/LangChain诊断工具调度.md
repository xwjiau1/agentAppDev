# LangChain诊断工具调度

## 技术实现

诊断函数通过tool暴露能力，再将工具列表交给create_agent，让模型按问题选择调用。

## 应用思路

工具应返回可核实的诊断证据，模型负责解释与建议。新增工具时需要同步核对参数、超时和运行权限。

## 代码解析

### 构造诊断Agent

[网络故障诊断Agent](../../应用侧/自动化与工具助手/网络故障诊断Agent/案例说明.md) · [2-network_diagnosis_agent.py，241–255行](../../应用侧/自动化与工具助手/网络故障诊断Agent/2-network_diagnosis_agent.py#L241-L255)

```python
tools = [

    ping_tool,

    dns_tool,

    interface_check_tool,

    log_analysis_tool

    # 如果有更多工具（如 Traceroute, Get Config等），在这里添加

]
```

tools列出四类诊断能力，ChatTongyi提供工具调用模型，create_agent组合两者。该函数只是配置入口，并不证明每个诊断已执行。

