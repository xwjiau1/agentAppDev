# FastAPI 模型生命周期与推理限流

## 实现机制

FastAPI 应用工厂根据进程角色只注册编码或重排入口。`lifespan` 通过工作线程加载权重并预热一次，完成后应用开始处理请求。就绪响应返回固定模型和 tokenizer 修订组成的签名，Java 在查询前用签名核对索引兼容性。[应用工厂](../../incubator/hybrid-rag/encoder/rag_models/api.py#L58-L89) · [FastAPI 生命周期](https://fastapi.tiangolo.com/advanced/events/)

## 代码解析

`InferenceSlot.run` 限制一个运行中的任务和两个等待者。用 `asyncio.timeout` 为获取锁设等待时间，满队列或等待过久返回 `503`。工作线程任务持有锁，其 `finally` 随真实计算完成而释放。接口使用 `asyncio.shield` 等待任务，并在进程停止时等待其结束。调用方取消等待后，下一条请求仍须等待该推理槽释放。[推理槽源码](../../incubator/hybrid-rag/encoder/rag_models/api.py#L18-L55) · [并发回归测试](../../incubator/hybrid-rag/encoder/tests/test_api.py)

## 适用边界

此并发限制作用于单个 FastAPI worker。每个 worker 有自己的模型副本和推理槽。示例 Compose 为每种模型启动一个 worker，用独立容器隔离两种模型。HTTP 超时解除调用方等待，服务仍计入正在运行的 CPU 任务。[项目部署](../../incubator/hybrid-rag/README.md) · [线程桥接基础](../../Python-base/异步与并发/asyncio.to_thread桥接同步阻塞函数.md)
