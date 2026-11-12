# 位置参数关键字参数与args和kwargs

> 复习优先级：必背。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

定义中的*args收集多余位置实参为tuple，**kwargs收集多余关键字实参为dict；调用中的*、**执行展开。*args后面的命名参数是仅限关键字参数。

## 面试问答

**问：本例customer_id能用普通位置实参传入吗？** 不能，它位于*args后，需使用customer_id=...。

**问：重复传入同一个形参会怎样？** 如显式关键字与**mapping撞名，调用时报TypeError；不是后者覆盖。

## 实际案例与代码

[Qwen投顾助手与Langfuse追踪](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/案例说明.md) · [1-hybrid_wealth_advisor_qwen_agent_langfuse.py，237–241行](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/1-hybrid_wealth_advisor_qwen_agent_langfuse.py#L237-L241)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
def __init__(self, *args, customer_id: str = "customer1", 
             customer_profile: Dict[str, Any] = None, **kwargs):
    super().__init__(*args, **kwargs)
    self.customer_id = customer_id
    self.customer_profile = customer_profile or {}
```

包装类截取customer_id与customer_profile，再把其他参数原样转发父类初始化；super接收到的是剩余实参。

## 易错点与追问

kwargs不是任意框架都会接受的“万能参数”，最终仍受目标签名约束。不要把字典合并的后值覆盖规则套到函数调用上。
