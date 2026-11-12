# Harness MCP式插件命名与分派

## 技术实现

示例用进程内MCPClient模拟工具注册与调用，宿主统一命名、检查冲突和schema，再把函数加入分派表。

## 应用思路

外部能力应先变为宿主可审计的工具定义与权限策略，避免插件自行决定授权。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 规范化工具名称

[s14_mcp_plugin/code.py，339–350行](../../应用侧/自动化与工具助手/通用AgentHarness/s14_mcp_plugin/code.py#L339-L350)

```python
prefixed = f"mcp__{safe_server}__{safe_tool}"
if len(prefixed) > 64:
    raise ValueError(f"MCP tool name is longer than 64 characters: {prefixed}")
origin = f"MCP tool {server_name!r}/{raw_name!r}"
if prefixed in origins:
    raise ValueError(
        "MCP tool name collision after normalization: "
        f"{prefixed!r} maps both {origins[prefixed]} and {origin}"
    )
schema = tool_def.get("inputSchema", {})
if not isinstance(schema, dict) or schema.get("type", "object") != "object":
    raise ValueError(f"Invalid input schema for {origin}")
```

服务器和工具名组成命名空间，并校验长度与冲突。只规范化名称可能合并不同原名，因此必须检测碰撞。

### 固定循环中的绑定

[s14_mcp_plugin/code.py，357–363行](../../应用侧/自动化与工具助手/通用AgentHarness/s14_mcp_plugin/code.py#L357-L363)

```python
handlers[prefixed] = (
    lambda *, client=server, tool=raw_name, **kwargs:
    client.call_tool(tool, kwargs)
)
policies[prefixed] = MCP_HOST_POLICY.get(
    (server_name, raw_name), "confirm"
)
```

lambda默认参数固定本轮server与raw_name，避免闭包都指向最后一个工具；未知策略默认confirm。

## 实现差异与边界

这是协议替身，不包含真实MCP传输握手。旧Qwen MCP案例演示npx或Python服务进程接入，二者不能声称已经同样连通。
