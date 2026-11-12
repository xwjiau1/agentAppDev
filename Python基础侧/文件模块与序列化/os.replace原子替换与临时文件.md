# os.replace原子替换与临时文件

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

先写临时文件，再replace到目标路径，可以减少读者读到半个JSON文件的机会。替换成功后目标路径指向新内容。

## 面试问答

**问：原子替换等于数据已经可靠落盘吗？** 不等于，抗断电持久性可能还需要flush/fsync及目录处理。

**问：能跨任意文件系统替换吗？** 不保证，通常应把临时文件放在同一文件系统。

## 实际案例与代码

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 先写后替换

[s13_agent_teams/code.py，212–217行](../../应用侧/自动化与工具助手/通用AgentHarness/s13_agent_teams/code.py#L212-L217)

```python
    temporary.write_text(
        json.dumps(asdict(task), indent=2), encoding="utf-8"
    )
    os.replace(temporary, path)
finally:
    temporary.unlink(missing_ok=True)
```

把完整JSON写到临时路径，再os.replace；finally清理遗留临时文件，missing_ok允许它已在替换后不存在。

## 易错点与追问

原子替换不能阻止两个写者最后写入覆盖；跨参与者锁与版本判断仍然必要。
