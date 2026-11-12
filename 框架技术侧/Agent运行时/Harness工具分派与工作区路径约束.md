# Harness工具分派与工作区路径约束

## 技术实现

工具schema描述模型输入，分派表将工具名映射到Python函数。文件路径在访问前解析并检查是否仍位于工作区。

## 应用思路

将读、写、编辑、glob封装为小接口，统一转换成功和失败结果，便于审计。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 检查路径边界

[s02_tool_use/code.py，81–85行](../../应用侧/自动化与工具助手/通用AgentHarness/s02_tool_use/code.py#L81-L85)

```python
def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path
```

resolve规范化路径，再用is_relative_to限制在WORKDIR内，越界时抛异常。调用方仍需处理软链接竞争和文件权限。

## 实现差异与边界

文件路径约束不等于Shell沙箱；Shell命令仍可能访问其他资源。不能把一个safe_path函数当作完整隔离系统。
