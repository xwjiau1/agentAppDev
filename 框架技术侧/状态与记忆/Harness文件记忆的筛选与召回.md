# Harness文件记忆的筛选与召回

## 技术实现

记忆先验证持久scope、类型和内容，过滤临时信息与重复记录，再以文件保存。召回按相关性选择并受总字符预算限制。

## 应用思路

记忆应记录能跨任务复用的信息，避免把单次进度、失败日志等全部写成长期知识。

## 实际代码与解析

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。下面是仓库源码摘录，仅去除外层缩进，省略的上下文可在链接中查看。

### 持久记忆候选校验

[s09_memory/code.py，114–131行](../../应用侧/自动化与工具助手/通用AgentHarness/s09_memory/code.py#L114-L131)

```python
def should_store_memory(candidate: dict, existing: list[dict]) -> bool:
    """Accept durable records that are not temporary or already stored."""
    if not isinstance(candidate, dict):
        return False
    if candidate.get("scope") != "persistent":
        return False
    if candidate.get("type") not in MEMORY_TYPES:
        return False

    name = str(candidate.get("name", "")).strip()
    description = str(candidate.get("description", "")).strip()
    body = str(candidate.get("body", "")).strip()
    if not name or not description or not body:
        return False

    candidate_text = _normalized_memory_text(f"{name}\n{description}\n{body}")
    if any(marker in candidate_text for marker in TEMPORARY_MEMORY_MARKERS):
        return False
```

字段校验与临时标记过滤先于写入；后续还按slug、描述和正文检查重复。

### 预算内召回

[s09_memory/code.py，325–335行](../../应用侧/自动化与工具助手/通用AgentHarness/s09_memory/code.py#L325-L335)

```python
def load_memories(messages: list) -> str:
    loaded = []
    remaining = RECALL_CHAR_LIMIT
    for filename in select_relevant_memories(messages):
        content = read_memory_file(filename)
        if not content or remaining <= 0:
            continue
        recalled = content[:remaining]
        loaded.append({"source": filename, "content": recalled})
        remaining -= len(recalled)
    return json.dumps(loaded, ensure_ascii=False, indent=2) if loaded else ""
```

按剩余预算截取每份内容，附source后序列化；当前实现可能在文本中途截断。

## 实现差异与边界

文件记忆不是模型参数学习，也不同于工作流恢复日志。相关性选择与自动抽取仍需核对，不保证存入内容均正确。
