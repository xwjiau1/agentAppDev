# Streamlit企业知识库交互

## 技术实现

项目以Pipeline组织离线文档处理与在线问答，入口调用阶段方法，src模块保留解析、切分、索引和问题处理依赖。

## 应用思路

适合批量企业报告处理。离线索引准备与在线查询应分别检查，缺少原始数据时仅保留代码无法直接得到答案。

## 代码解析

### 索引准备流程

[企业报告知识库交互版](../../应用侧/知识问答与文档处理/企业报告知识库交互版/案例说明.md) · [src/pipeline.py，198–217行](../../应用侧/知识问答与文档处理/企业报告知识库交互版/src/pipeline.py#L198-L217)

```python
def process_parsed_reports(self):
    """
    处理已解析的PDF报告，主要流程：
    1. 对报告进行分块
    2. 创建向量数据库
    """
    print("开始处理报告流程...")

    print("步骤1：报告分块...")
    self.chunk_reports()

    print("步骤2：创建向量数据库...")
    self.create_vector_dbs()

    print("报告处理流程已成功完成！")

def _get_next_available_filename(self, base_path: Path) -> Path:
    """
    获取下一个可用的文件名，如果文件已存在则自动添加编号后缀。
    例如：若answers.json已存在，则返回answers_01.json等。
```

方法顺序体现解析结果的合并、切分和索引准备；每阶段读写路径由Pipeline配置提供。

### 按企业检索回答

[企业报告知识库交互版](../../应用侧/知识问答与文档处理/企业报告知识库交互版/案例说明.md) · [src/questions_processing.py，129–148行](../../应用侧/知识问答与文档处理/企业报告知识库交互版/src/questions_processing.py#L129-L148)

```python
def get_answer_for_company(self, company_name: str, question: str, schema: str) -> dict:
    # 针对单个公司，检索上下文并调用LLM生成答案
    t0 = time.time()
    if self.llm_reranking:
        retriever = HybridRetriever(
            vector_db_dir=self.vector_db_dir,
            documents_dir=self.documents_dir
        )
    else:
        retriever = VectorRetriever(
            vector_db_dir=self.vector_db_dir,
            documents_dir=self.documents_dir
        )
    t1 = time.time()
    print(f"[计时] [get_answer_for_company] 检索器初始化耗时: {t1-t0:.2f} 秒")
    if self.full_context:
        retrieval_results = retriever.retrieve_all(company_name)
    else:           
        t2 = time.time()
        retrieval_results = retriever.retrieve_by_company_name(
```

先按公司定位相关材料，再调用模型生成答案；上下文与引用需要共同保存。交互版增加单问入口，基础版侧重批处理。

