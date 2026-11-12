# sorted与list.sort及稳定排序

> 复习优先级：必背。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

sorted接受可迭代对象并返回新列表；list.sort原地排序并返回None。key指定排序键，reverse指定方向；Python排序是稳定的。

## 面试问答

**问：稳定排序是什么意思？** 排序键相等的元素保持原有相对次序。

**问：为什么`a = a.sort()`后a变成None？** sort返回None，结果不在返回值里，而在原列表中。

## 实际案例与代码

[多查询混合检索与重排问答](../../应用侧/知识问答与文档处理/多查询混合检索与重排问答/案例说明.md) · [3-chatpdf-faiss-HybridSearch.py，96–98行](../../应用侧/知识问答与文档处理/多查询混合检索与重排问答/3-chatpdf-faiss-HybridSearch.py#L96-L98)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
hybrid_scores.sort(key=lambda x: x[1], reverse=True)
top_k = hybrid_scores[:k]
```

按score降序原地排序后再取前k项，原hybrid_scores顺序被改变；如后续需要原顺序，应使用sorted或先保留副本。

## 易错点与追问

不能对不可比较的混合键随意排序；用key归一化比较标准。不要把“排序原地修改”理解成绝不使用额外空间。
