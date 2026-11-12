# JSON序列化与反序列化

> 复习优先级：必背。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

json.dumps把Python数据编码为JSON字符串，json.loads反向解析字符串；dump/load面向文件对象。JSON对象、数组、null对应dict、list、None。

## 面试问答

**问：所有Python对象都能直接JSON编码吗？** 不能，set、任意实例等通常需转换或自定义编码。

**问：`ensure_ascii=False`控制什么？** 允许输出非ASCII字符原样呈现，不改变底层文件编码设置。

## 实际案例与代码

[查询改写与搜索策略](../../应用侧/搜索与研究助手/查询改写与搜索策略/案例说明.md) · [2-Query联网搜索改写.py，65–72行](../../应用侧/搜索与研究助手/查询改写与搜索策略/2-Query联网搜索改写.py#L65-L72)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
    return json.loads(response)
except:
    return {
        "need_web_search": False,
        "search_reason": "无法解析",
        "confidence": 0.5
    }
```

模型响应先按JSON解析，失败时返回默认结构。源码使用宽泛except，学习时应能提出改为针对JSON解析异常并记录原因。

## 易错点与追问

模型声称输出JSON不代表一定有效；解析错误、字段缺失与字段类型不符要分开处理。JSON不等于Python字面量，不能用eval替代loads。
