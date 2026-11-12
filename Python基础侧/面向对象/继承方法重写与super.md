# 继承方法重写与super

> 复习优先级：必背。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

继承复用父类接口与实现；子类同名方法可覆盖父类行为。super按方法解析顺序MRO继续查找，不简单等于“直接父类对象”。

## 面试问答

**问：为什么重写__init__常调用super？** 保留父类初始化契约，尤其是框架或协作式多继承。

**问：多继承如何确定查找顺序？** Python使用C3线性化，可通过类.__mro__查看。

## 实际案例与代码

[Qwen投顾助手与Langfuse追踪](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/案例说明.md) · [1-hybrid_wealth_advisor_qwen_agent_langfuse.py，234–241行](../../应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/1-hybrid_wealth_advisor_qwen_agent_langfuse.py#L234-L241)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
class TracedAssistant(Assistant):
    """带 LangFuse 追踪的 Assistant 包装类"""

    def __init__(self, *args, customer_id: str = "customer1", 
                 customer_profile: Dict[str, Any] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.customer_id = customer_id
        self.customer_profile = customer_profile or {}
```

TracedAssistant继承Assistant，先转发父类构造，再增加客户属性；其run还改变了生成器行为，需同时核对协议。

## 易错点与追问

子类覆写要保留调用方预期的参数、返回与迭代协议；普通函数、生成器、协程不能只因同名就当作等价。
