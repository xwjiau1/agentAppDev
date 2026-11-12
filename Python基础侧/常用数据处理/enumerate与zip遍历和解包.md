# enumerate与zip遍历和解包

> 复习优先级：必背。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

enumerate同时给出计数和元素；zip把多个可迭代对象逐项配对，默认在最短输入耗尽时结束。for中的多个变量会对每项做解包。

## 面试问答

**问：enumerate的start参数是什么？** 只改变计数起点，不改变输入序列或访问位置。

**问：zip会检查两个输入等长吗？** 默认不会；如需严格校验，可显式检查长度或在支持版本中使用strict选项。

## 实际案例与代码

[主题乐园多模态知识问答](../../应用侧/知识问答与文档处理/主题乐园多模态知识问答/案例说明.md) · [5-disney_query.py，87–92行](../../应用侧/知识问答与文档处理/主题乐园多模态知识问答/5-disney_query.py#L87-L92)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
for rank, (idx, dist) in enumerate(zip(indices[0], distances[0])):
    if idx == -1:
        continue
    m = metadata[idx]
    sim = distance_to_similarity(dist)
    content_preview = m['content'][:45].replace('\n', ' ')
```

zip配对邻居ID与距离，enumerate再提供排名计数；(idx, dist)是嵌套解包，idx=-1时跳过无效邻居。

## 易错点与追问

zip返回迭代器，不是可无限重复遍历的列表。维度或样本对齐错误可能被默认截断悄悄隐藏。
