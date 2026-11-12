# Harness工作流日志缓存与恢复

## 技术实现

WorkflowTool先校验元信息和权限，分配或恢复run_id，在锁下执行脚本。ExecutionState通过journal键复用已完成步骤，限制预算与并发。

## 应用思路

需要可恢复多步骤任务时，持久化输入、运行ID与步骤结果；恢复前检查任务名称和参数一致性。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 入口与运行锁

[s16_workflow_runtime/code.py，559–570行](../../应用侧/自动化与工具助手/通用AgentHarness/s16_workflow_runtime/code.py#L559-L570)

```python
async def call(self, meta, script_fn, args=None, resume_from_run_id=None):
    validate_meta(meta)
    check_permission(meta)
    resuming = resume_from_run_id is not None
    if resuming:
        run_id = validate_run_id(resume_from_run_id)
    else:
        run_id = reserve_run_id(meta)
    with workflow_run_lock(run_id):
        return await self._call_locked(
            meta, script_fn, args, run_id, resuming
        )
```

validate_meta与check_permission先于执行；resume沿用已有run_id，否则排他预留新身份，再进入run级锁。

### 缓存与并发边界

[s16_workflow_runtime/code.py，471–487行](../../应用侧/自动化与工具助手/通用AgentHarness/s16_workflow_runtime/code.py#L471-L487)

```python
key = self.journal.key("agent", label, prompt, schema)
cached = self.journal.cached(key)
if cached is not MISS:
    if schema is not None:
        ok, err = SimpleJsonSchema(schema).validate(cached)
        if not ok:
            raise WorkflowInputError(
                f"cached agent output failed schema validation: {err}"
            )
    self.task.progress_event("workflow_agent", label=label,
                             phase=phase or self._phase, status="cached")
    return cached

async with self._limits.semaphore:
    run = await asyncio.to_thread(
        self.runner.run, prompt, schema, label
    )
```

MISS哨兵区分未命中与合法None等结果；缓存仍按schema验证；未命中时semaphore限制进入runner的数量，to_thread承接同步调用。

## 实现差异与边界

复用已记录步骤不等于外部副作用exactly-once；崩溃发生在操作完成但日志未写入时仍可能重做。模拟Runner不代表真实模型执行。
