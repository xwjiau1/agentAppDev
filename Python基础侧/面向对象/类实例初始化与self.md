# 类实例初始化与self

> 复习优先级：必背。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

类定义描述对象行为，实例保存各自状态。实例方法第一个参数通常写self；通过实例访问方法时，实例会作为绑定参数传入。__init__负责初始化，不负责返回新对象。

## 面试问答

**问：`self.name`与类属性name有什么区别？** 通常前者写入实例命名空间，后者位于类上；属性查找还受描述符与继承规则影响。

**问：__new__和__init__有什么区别？** __new__创建或返回实例，__init__在适用时初始化已有实例。

## 实际案例与代码

[LangChain文本工具与LCEL组合](../../应用侧/基础技术示例/LangChain文本工具与LCEL组合/案例说明.md) · [2-simple_toolchain.py，14–21行](../../应用侧/基础技术示例/LangChain文本工具与LCEL组合/2-simple_toolchain.py#L14-L21)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
class TextAnalysisTool:
    """文本分析工具，用于分析文本内容"""
    def __init__(self):
        self.name = "文本分析"
        self.description = "分析文本内容，提取字数、字符数和情感倾向"
    def run(self, text: str) -> str:
        word_count = len(text.split())
        char_count = len(text)
```

__init__设置每个实例的name和description；run通过self接收调用对象，再对text参数执行分析。

## 易错点与追问

类属性若是可变容器可能被多个实例共享；不要把所有写在类体内的字段都等同于普通实例属性，框架可能介入。
