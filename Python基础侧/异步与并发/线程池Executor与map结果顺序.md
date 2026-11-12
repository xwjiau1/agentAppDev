# 线程池Executor与map结果顺序

> 复习优先级：常考。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

ThreadPoolExecutor把调用提交给工作线程；executor.map按输入次序提供结果，完成顺序可能不同。with退出时通常等待已提交任务结束并关闭线程池。

## 面试问答

**问：map与as_completed的结果顺序有何差异？** map按输入顺序取结果；as_completed按完成情况产出Future。

**问：max_workers=1是不是并发加速？** 本例只启用一个工作线程，不会让多个重排任务同时在线程池中执行。

## 实际案例与代码

[企业报告问答与回归评估](../../应用侧/知识问答与文档处理/企业报告问答与回归评估/案例说明.md) · [reranking.py，204–206行](../../应用侧/知识问答与文档处理/企业报告问答与回归评估/src/reranking.py#L204-L206)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
with ThreadPoolExecutor(max_workers=1) as executor:
    all_results = list(executor.map(process_single_doc, documents))
```

代码使用线程池接口但限制为一个工作线程。list消费map结果，异常通常在取对应结果时暴露；不能只看到Executor就声称已实现并发提速。

## 易错点与追问

多线程不等于所有Python代码都能多核并行；性能取决于解释器构建、扩展库和任务类型。避免共享可变数据而不协调。
