# os.open排他创建与文件权限位

> 面试复习：先讲机制，再用Harness代码解释状态、边界和失败处理。

## 面试速记

os.open用标志位控制低层文件创建。O_CREAT加O_EXCL让“文件已存在时失败”与创建合并，避免先exists再写的竞争窗口。

## 面试问答

**问：为什么先检查exists再创建不够？** 检查和创建之间别的执行者可能创建同名文件，即TOCTOU。

**问：返回的是文件对象吗？** 返回整数文件描述符，使用完需os.close。

## 实际案例与代码

关联应用：[通用AgentHarness](../../应用侧/自动化与工具助手/通用AgentHarness/案例说明.md)。源码节选仅去除外层缩进。

### 预留唯一运行身份

[s16_workflow_runtime/code.py，69–73行](../../应用侧/自动化与工具助手/通用AgentHarness/s16_workflow_runtime/code.py#L69-L73)

```python
    fd = os.open(snapshot_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
except FileExistsError:
    continue
os.close(fd)
return run_id
```

O_WRONLY指定写模式，0o600请求仅所有者读写，实际权限还受平台和umask等影响。FileExistsError时重试新ID，成功后关闭描述符。

## 易错点与追问

权限位不能跨平台机械等同；Windows行为需单独验证。排他创建解决名称占用，不代表整次工作流事务原子化。
