# finally清理与状态恢复

> 复习优先级：必背。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

finally在正常退出或异常传播时执行，适合恢复状态与释放资源。return、break等控制转移通常也会经过finally；进程强制终止等情况不能依赖它完成清理。

## 面试问答

**问：finally里return有什么风险？** 可能覆盖try中的返回值，或压制待传播异常；一般避免。

**问：清理操作也抛异常怎么办？** 新异常可能遮蔽原问题，需要明确清理失败的处理策略。

## 实际案例与代码

[OpenManus通用任务助手](../../应用侧/自动化与工具助手/OpenManus通用任务助手/案例说明.md) · [base.py，79–83行](../../应用侧/自动化与工具助手/OpenManus通用任务助手/app/agent/base.py#L79-L83)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
    self.state = AgentState.ERROR  # 失败时转换到 ERROR 状态
    raise e
finally:
    self.state = previous_state  # 恢复到之前的状态
```

代码先设置错误状态并抛出异常，finally随后恢复进入前状态。异常继续传播，但对象最终状态可能不是ERROR。

## 易错点与追问

本例except写入ERROR后finally又恢复previous_state；理解最终状态要按真实执行顺序判断，不能只看except一行。
