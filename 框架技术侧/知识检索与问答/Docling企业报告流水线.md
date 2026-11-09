# Docling企业报告流水线

## 技术实现

项目以Pipeline组织离线文档处理与在线问答，入口调用阶段方法，src模块保留解析、切分、索引和问题处理依赖。

## 应用思路

适合批量企业报告处理。离线索引准备与在线查询应分别检查，缺少原始数据时仅保留代码无法直接得到答案。

## 代码解析

### 索引准备流程

[企业报告知识库基础流水线](../../应用侧/知识问答与文档处理/企业报告知识库基础流水线/案例说明.md) · [src/pipeline.py，212–231行](../../应用侧/知识问答与文档处理/企业报告知识库基础流水线/src/pipeline.py#L212-L231)

```python
def process_parsed_reports(self):
    """Process already parsed PDF reports through the pipeline:
    1. Merge to simpler JSON structure
    2. Export to markdown
    3. Chunk the reports
    4. Create vector databases
    """
    print("Starting reports processing pipeline...")

    print("Step 1: Merging reports...")
    self.merge_reports()

    print("Step 2: Exporting reports to markdown...")
    self.export_reports_to_markdown()

    print("Step 3: Chunking reports...")
    self.chunk_reports()

    print("Step 4: Creating vector databases...")
    self.create_vector_dbs()
```

方法顺序体现解析结果的合并、切分和索引准备；每阶段读写路径由Pipeline配置提供。

### 按企业检索回答

[企业报告知识库基础流水线](../../应用侧/知识问答与文档处理/企业报告知识库基础流水线/案例说明.md) · [src/questions_processing.py，123–142行](../../应用侧/知识问答与文档处理/企业报告知识库基础流水线/src/questions_processing.py#L123-L142)

```python
def get_answer_for_company(self, company_name: str, question: str, schema: str) -> dict:
    # 针对单个公司，检索上下文并调用LLM生成答案
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

    if self.full_context:
        retrieval_results = retriever.retrieve_all(company_name)
    else:           
        retrieval_results = retriever.retrieve_by_company_name(
            company_name=company_name,
            query=question,
            llm_reranking_sample_size=self.llm_reranking_sample_size,
```

先按公司定位相关材料，再调用模型生成答案；上下文与引用需要共同保存。交互版增加单问入口，基础版侧重批处理。

