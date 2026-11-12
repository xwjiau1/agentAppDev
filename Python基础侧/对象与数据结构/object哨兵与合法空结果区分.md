# object哨兵与合法空结果区分

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

用唯一object实例表示缺失状态，可将“没有缓存”与缓存结果为None、False、0、空容器区分。比较应使用is或is not。

## 面试问答

**问：为什么不直接if cached？** 合法假值会被误当作未命中。

**问：为什么不用字符串"MISS"？** 真实业务数据可能恰好相同；专用对象可避免值冲突。

## 实际案例与代码

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 唯一哨兵

[s16_workflow_runtime/code.py，47–47行](../../应用侧/自动化与工具助手/通用AgentHarness/s16_workflow_runtime/code.py#L47-L47)

```python
MISS = object()                        # journal cache miss sentinel
```

模块创建唯一哨兵对象；读取缓存时返回它代表未命中。

### 按身份判断

[s16_workflow_runtime/code.py，472–478行](../../应用侧/自动化与工具助手/通用AgentHarness/s16_workflow_runtime/code.py#L472-L478)

```python
cached = self.journal.cached(key)
if cached is not MISS:
    if schema is not None:
        ok, err = SimpleJsonSchema(schema).validate(cached)
        if not ok:
            raise WorkflowInputError(
                f"cached agent output failed schema validation: {err}"
```

只有与MISS不是同一对象才命中，即使cached为None也会继续验证并返回。

## 易错点与追问

哨兵通过JSON或进程间传输后不会自然保持同一身份，持久化层应使用清晰协议重新映射。
