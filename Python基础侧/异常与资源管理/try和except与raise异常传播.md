# try和except与raise异常传播

> 复习优先级：必背。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

try包住可能失败的操作，except按类型处理异常；raise向上抛出。else在try正常完成后执行，finally用于离开时的清理。

## 面试问答

**问：`except Exception`能捕获所有终止情况吗？** 不能，SystemExit、KeyboardInterrupt等通常不属于Exception子类。

**问：`raise`与`raise e`如何选？** 在except中重新抛出通常用裸raise，保留原异常传播位置更清晰；`raise NewError(...) from e`可明确异常链。

## 实际案例与代码

[投顾AI助手效果评估](../../应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) · [1-hybrid_wealth_advisor_langgraph_langsmith.py，278–283行](../../应用侧/金融投研与投顾/投顾AI助手效果评估/1-hybrid_wealth_advisor_langgraph_langsmith.py#L278-L283)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
except Exception as e:
    return {
        **state,
        "error": f"评估阶段出错: {str(e)}",
        "final_response": "评估查询时发生错误，无法处理您的请求。"
    }
```

节点捕获异常后返回含error的状态字典，而不是重新抛出；调用方需要检查error，单凭函数返回不能认定执行成功。

## 易错点与追问

不要用裸except吞掉所有异常；也不要把错误文本当成成功业务输出而丢失失败状态。
