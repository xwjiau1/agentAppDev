# 混合检索 RAG

用 Spring Boot 和 LangChain4j 导入文档，通过 FastAPI 的 BGE-M3 服务生成密集和稀疏向量，使用 Qdrant 混合召回，并返回带来源的上下文。Docker Compose 负责部署各服务。

首版已通过本机 Docker Compose 双模型验收，覆盖文档导入、混合检索、重排、页码引用、超时回退和缓存重启。运行证据与样本指标见 [开发记录](docs/开发记录.md)。

## 启动与查询

在项目目录使用 Docker Compose v2 和 Linux x86-64 容器。首轮构建需要拉取镜像、安装依赖并下载约 4.6 GB 模型文件。首版使用 CPU 推理，每种模型一个 worker，开发环境可从给 Docker 分配约 8 GiB 内存开始。

```powershell
docker compose up --build --wait --wait-timeout 1200
$body = @{ query = '退款批准后多久能退回原支付渠道？'; topK = 5 } | ConvertTo-Json -Compress
Invoke-RestMethod http://127.0.0.1:8080/v1/search -Method Post -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body)) | ConvertTo-Json -Depth 8
```

`hits` 保留 `chunkId`、正文和 `scoreType`，`citations` 保留进入 `context` 的来源和页码。示例退款 PDF 第 2 页说明退款在五个工作日内原路退回。默认 `scoreType` 为 `reranker`。模型重排调用失败时返回 `rerankDegraded: true`，并保留召回顺序。查询也可传 `filters.documentIds`，该值可从命中结果取得。

| 操作 | 命令或配置 |
| --- | --- |
| 查看服务与模型状态 | `docker compose ps -a`，`docker compose logs encoder reranker ingest` |
| 停止并保留模型与索引 | `docker compose down` |
| 使用已缓存权重 | 将 `HF_HUB_OFFLINE=1` 写入 `.env`，然后 `docker compose up --wait --pull never --wait-timeout 1200` |
| 调整端口、CPU 线程与超时 | 复制 [.env.example](.env.example) 为 `.env` 后修改 |

使用只读模型快照时，在 `.env` 配置 `BGE_M3_SNAPSHOT` 和 `BGE_RERANKER_SNAPSHOT`，分别指向完整模型目录。各目录的 `.revision` 记录对应源码中的固定修订。然后运行 `docker compose -f compose.yaml -f compose.snapshots.yaml up --build --wait --wait-timeout 1200`。使用预构建镜像时可改用 `--pull never` 并省略 `--build`。[模型及修订定义](encoder/rag_models/models.py)

语料通过 `RAG_CORPUS_DIR` 只读挂载。已有 collection 绑定原语料快照，更换语料时先 `docker compose stop rag-api`，在 `.env` 指定原语料目录或新目录及新的 `RAG_COLLECTION`，再执行 `docker compose up --wait`。旧 collection 保留在 `qdrant-storage` 卷中，回退时恢复对应的语料目录和 collection 名称后重启。单文件上限 16 MiB、支持文件数上限 1000、PDF 页数上限 2000、总切片上限 20000。PDF 支持可提取文本的页面，纯扫描 PDF 导入时报错。

评估时将 `RAG_EVALUATION_ENABLED=true` 写入 `.env` 并重建容器配置，运行 `python sample/evaluate.py`。脚本对同一批 [标注查询](sample/queries.json) 比较 dense、sparse、RRF 和重排的 Recall@5、MRR@5 与预热后 p95。Qdrant、模型服务和导入任务留在 Compose 网络中，外部调用入口为 `127.0.0.1:8080`。

| 文档 | 内容 |
| --- | --- |
| [落地方案](docs/落地方案.md) | 服务职责、Qdrant 切片与页码存取示例、重排接入点、部署与验收 |
| [开发记录](docs/开发记录.md) | 当前决策、验证范围及知识库回写计划 |

`encoder` 运行 `BAAI/bge-m3`，`reranker` 运行 `BAAI/bge-reranker-v2-m3`。PostgreSQL 和答案生成列为后续扩展。

相关案例见 [RAG 应用实现检查](../../doc/RAG应用实现检查.md)，项目归档与验证遵循 [维护规则](../../doc/维护规则.md)。
