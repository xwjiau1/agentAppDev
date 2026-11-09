# Qwen-Agent MCP服务接入

## 技术实现

MCP客户端配置描述服务进程如何启动，Qwen-Agent使用服务暴露的工具。FastMCP通过装饰器把Python函数导出为工具。

## 应用思路

适合把本地文件能力或已有服务接入不同Agent；服务进程和模型调用是独立依赖。

## 代码解析

### 启动本地服务

[MCP地图搜索与文件助手](../../应用侧/自动化与工具助手/MCP地图搜索与文件助手/案例说明.md) · [assistant_mcp_txt_bot.py，43–54行](../../应用侧/自动化与工具助手/MCP地图搜索与文件助手/assistant_mcp_txt_bot.py#L43-L54)

```python
    "mcpServers": {
        "txt-counter": {
            "command": "python",
            "args": ["txt_counter.py"],
            "port": 6277
        }
    }
}]

try:
    # 创建助手实例
    bot = Assistant(
```

command指定解释器，args指定服务脚本；相对脚本依赖cwd。服务名称用于区分连接，不是模型名称。

### 导出文件统计函数

[MCP地图搜索与文件助手](../../应用侧/自动化与工具助手/MCP地图搜索与文件助手/案例说明.md) · [txt_counter.py，6–18行](../../应用侧/自动化与工具助手/MCP地图搜索与文件助手/txt_counter.py#L6-L18)

```python
mcp = FastMCP("桌面 TXT 文件统计器")

@mcp.tool()
def count_desktop_txt_files() -> int:
    """统计桌面上 .txt 文件的数量"""
    # 获取桌面路径
    desktop_path = Path(os.path.expanduser("~/Desktop"))

    # 统计 .txt 文件
    txt_files = list(desktop_path.glob("*.txt"))
    return len(txt_files)

@mcp.tool()
```

mcp.tool将类型注解和函数说明作为工具定义；glob仅枚举桌面顶层txt文件，并非递归扫描。

## 应用方式差异

文本服务由Python启动，地图与Tavily服务由npx启动；差异在进程参数与凭据，不重复展示相同Assistant初始化代码。
