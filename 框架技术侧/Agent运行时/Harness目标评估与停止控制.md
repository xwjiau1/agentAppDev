# Harness目标评估与停止控制

## 技术实现

GoalController在一轮结束后评估目标完成条件，给出allow、defer、achieved、failed、block、limit或error等停止决定，驱动宿主继续或交还控制。

## 应用思路

把正常输出结束与业务目标完成分开判断；后台仍在工作时先defer，评估失败则保留错误证据。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 评估前的停止边界

[s17_goal_loop/code.py，322–333行](../../应用侧/自动化与工具助手/通用AgentHarness/s17_goal_loop/code.py#L322-L333)

```python
if self.active is None:
    return "No goal set"
condition = self.active.condition
self._record(
    active=False,
    met=False,
    failed=False,
    reason=reason,
)
self.active = None
self.consecutive_blocks = 0
return f"Goal cleared: {condition}"
```

无目标直接allow；后台工作未完成时defer，不贸然宣布目标达成。

### 完成与阻断上限

[s17_goal_loop/code.py，413–428行](../../应用侧/自动化与工具助手/通用AgentHarness/s17_goal_loop/code.py#L413-L428)

```python
self.consecutive_blocks += 1
self._record(
    active=True,
    met=False,
    failed=False,
    reason=evaluation.reason,
)
if self.consecutive_blocks > self.block_cap:
    return StopDecision(
        "limit",
        (
            f"goal remains active, but the Stop hook blocked "
            f"{self.block_cap} consecutive turns"
        ),
    )
return StopDecision("block", evaluation.reason)
```

未完成时累积连续阻断次数；超过上限返回limit，但目标仍active，不能把预算或阻断用尽当成成功。

## 实现差异与边界

目标评估由可替换evaluator实现；模型判断有误差。restore重建活跃目标时重置部分计数，不能称为完整重放所有历史执行。
