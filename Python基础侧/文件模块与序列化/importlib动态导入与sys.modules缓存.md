# importlib动态导入与sys.modules缓存

> 复习优先级：进阶。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

importlib可从文件路径创建模块加载规范，再构建模块对象并执行。sys.modules是按模块名缓存已加载模块的映射。

## 面试问答

**问：动态导入为什么要先写sys.modules？** 便于执行期间的同名导入与后续访问定位同一模块，但失败时也要考虑清理半初始化状态。

**问：动态导入有风险吗？** exec_module会执行目标文件的顶层代码，只应加载可信源码。

## 实际案例与代码

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [2-langsmith_testing_evaluation.py，32–39行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/2-langsmith_testing_evaluation.py#L32-L39)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
spec = importlib.util.spec_from_file_location(
    "hybrid_wealth_advisor_langgraph_langsmith",
    "1-hybrid_wealth_advisor_langgraph_langsmith.py"
)
hybrid_module = importlib.util.module_from_spec(spec)
sys.modules["hybrid_wealth_advisor_langgraph_langsmith"] = hybrid_module
spec.loader.exec_module(hybrid_module)
```

为带数字前缀的脚本建立合法模块名，创建模块后放进缓存，再执行源码。动态导入没有绕过顶层API初始化等副作用。

## 易错点与追问

这里传入的是相对文件名，因此受cwd影响；spec或loader可能为空，健壮实现应先校验。
