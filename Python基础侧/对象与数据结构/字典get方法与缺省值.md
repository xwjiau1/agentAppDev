# 字典get方法与缺省值

> 复习优先级：必背。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

`d[key]`在键不存在时抛KeyError；`d.get(key, default)`只在缺键时返回默认值，不会写入字典。键存在但值为None时仍返回None。

## 面试问答

**问：get与setdefault有什么区别？** setdefault缺键时会把默认值写进去；get不会。

**问：`get("x", [])`是否每次都共享一个空列表？** 该列表表达式在每次调用时求值，和函数定义中的可变默认参数不同。

## 实际案例与代码

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [1-hybrid_wealth_advisor_langgraph_langsmith.py，263–268行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/1-hybrid_wealth_advisor_langgraph_langsmith.py#L263-L268)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
processing_mode = result.get("processing_mode", "reactive")
if processing_mode not in ["reactive", "deliberative"]:
    processing_mode = "reactive"  # 默认使用反应式处理
# 获取查询类型，确保有值
query_type = result.get("query_type", "emergency")
if query_type not in ["emergency", "informational", "analytical"]:
```

模型结果可能缺少processing_mode，因此先给reactive默认值；接着检查允许值并回退，get本身不做枚举校验。

## 易错点与追问

不要用get的默认值掩盖必需配置缺失。`d.get("x") or fallback`还会把0、False、空字符串等值视作需要回退。
