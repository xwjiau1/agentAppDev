# 真值判断与and或or短路

> 复习优先级：必背。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

None、False、数值0和空容器等为假。and/or从左到右短路，返回某个操作数本身，不保证返回bool。

## 面试问答

**问：为什么`response and response[-1]...`能防止空列表索引？** response为空时后半段不执行。

**问：`x or {}`何时不保留x？** x为任意假值时；不只在x为None时。

## 实际案例与代码

[Qwen投顾助手与Langfuse追踪](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/案例说明.md) · [1-hybrid_wealth_advisor_qwen_agent_langfuse.py，241–241行](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/1-hybrid_wealth_advisor_qwen_agent_langfuse.py#L241-L241)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
self.customer_profile = customer_profile or {}
```

customer_profile非空时保留原字典，缺省或空字典时创建新空字典；对非空输入仍共享对象引用。

## 易错点与追问

需要只处理None时用`x is None`。自定义类可通过__bool__或__len__影响真值；不要把and/or简单理解为布尔值计算。
