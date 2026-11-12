# is身份比较与相等运算符

> 复习优先级：必背。

## 面试速记

`==`比较相等关系，可由__eq__定义；`is`比较是否为同一个对象，不会调用__eq__。判断缺省标记None通常写`x is None`。

## 面试问答

**问：为什么不能用is比较两个字符串的内容？** 字符串驻留等优化可能让部分值恰好共享对象，不能作为业务语义依赖。

**问：`a == b`为True是否意味着`a is b`？** 不意味着；两个不同列表可以内容相等。

## 实际案例与代码

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [2-langsmith_testing_evaluation.py，389–392行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/2-langsmith_testing_evaluation.py#L389-L392)

以下为源码节选，统一去除外层缩进。

```python
if example_inputs is None:
    example_inputs = {}
elif hasattr(example_inputs, '__dict__'):
    example_inputs = example_inputs.__dict__
```

这里区分真正缺少对象与其他值；None身份判断不依赖example_inputs自定义的相等比较。它与此前`if not example_inputs`的假值判断语义不同。

## 易错点与追问

不要用id或小整数缓存推断一般对象的相等性。自定义__eq__的返回与异常行为需要单独考虑。
