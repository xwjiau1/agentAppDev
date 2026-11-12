# Harness事件钩子与短路处理

## 技术实现

钩子表按事件组织回调，触发时逐个执行；非None返回值可阻断当前工具调用，Stop钩子还可要求继续处理。

## 应用思路

将权限、日志、输出裁剪等横切机制从主循环中抽离。需定义回调顺序和返回值契约。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 触发回调

[s04_hooks/code.py，142–147行](../../应用侧/自动化与工具助手/通用AgentHarness/s04_hooks/code.py#L142-L147)

```python
def trigger_hooks(event: str, *args):
    for callback in HOOKS[event]:
        result = callback(*args)
        if result is not None:  # A hook result blocks this tool call.
            return result
    return None
```

按注册顺序调用；is not None允许空字符串或False也作为阻断结果，不能改写成if result而不改变语义。

## 实现差异与边界

Hook是应用扩展协议，不是Python内置事件系统；回调抛异常如何传播需和调用点一起检查。
