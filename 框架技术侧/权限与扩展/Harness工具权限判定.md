# Harness工具权限判定

## 技术实现

工具调用在执行前先检查禁止规则，再按工具与参数判断是否需要确认；拒绝后不执行。

## 应用思路

对同一类工具使用统一入口检查，避免某一工具分支绕过判断。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 判定入口

[s03_permission/main.py，203–214行](../../应用侧/自动化与工具助手/通用AgentHarness/s03_permission/main.py#L203-L214)

```python
def check_permission(block) -> bool:
    if block.name == "bash":
        reason = check_deny_list(block.input.get("command", ""))
        if reason:
            print(f"\n\033[31m[blocked] {reason}\033[0m")
            return False
    reason = check_rules(block.name, block.input)
    if reason:
        decision = ask_user(block.name, block.input, reason)
        if decision == "deny":
            return False
    return True
```

bash先检查deny list；其他规则命中时由ask_user得到决定。函数只返回是否允许，实际工具执行还在后续循环。

## 实现差异与边界

当前工作副本使用main.py；关键词策略不是完整命令解析或OS沙箱，实际拒绝范围以代码为准。不要据此承诺可抵御所有复杂Shell组合。
