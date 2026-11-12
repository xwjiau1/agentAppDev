# Harness定时任务队列与投递确认

## 技术实现

定时器检查cron表达式，把到期工作放入队列，并用pending_delivery和分钟标记避免重复入队；消费与确认分开处理。

## 应用思路

把定时触发与模型执行分离，避免调度线程直接承担完整对话循环。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 到期检查与去重

[s12_cron_scheduler/code.py，497–508行](../../应用侧/自动化与工具助手/通用AgentHarness/s12_cron_scheduler/code.py#L497-L508)

```python
def poll_due_jobs(moment: datetime):
    minute_marker = moment.strftime("%Y-%m-%d %H:%M")
    with cron_lock:
        for job in list(scheduled_jobs.values()):
            try:
                if job.pending_delivery or job.last_fired == minute_marker:
                    continue
                if cron_matches(job.cron, moment):
                    _enqueue_due_job(job, minute_marker)
                    print(f"  [cron] due {job.id}: {job.prompt[:60]}")
            except Exception as error:
                print(f"  [cron] could not enqueue {job.id}: {error}")
```

同一分钟已触发或尚待投递的job跳过；命中cron后调用_enqueue_due_job。

## 实现差异与边界

该实现有自己的cron字段验证与时区假设，不应当成完整系统cron替代品。持久任务恢复和确认失败需一起核对。
