# Streamlit单问题检索界面

## 技术实现

企业报告检索器以向量召回候选，并可将命中切片扩展为父页，再通过LLM重排截取最终上下文。交互版本把单问题入口接入Streamlit。

## 应用思路

对于表格和跨行信息，父页上下文有助于保留结构；候选量、批次和最终页数控制不同阶段的成本。

## 代码解析

### 候选召回与精排

[企业报告交互问答增强版](../../应用侧/知识问答与文档处理/企业报告交互问答增强版/案例说明.md) · [src/retrieval.py，319–336行](../../应用侧/知识问答与文档处理/企业报告交互问答增强版/src/retrieval.py#L319-L336)

```python
vector_results = self.vector_retriever.retrieve_by_company_name(
    company_name=company_name,
    query=query,
    top_n=llm_reranking_sample_size,
    return_parent_pages=return_parent_pages
)
t1 = time.time()
print(f"[计时] [HybridRetriever] 向量检索耗时: {t1-t0:.2f} 秒")
# 使用LLM对结果进行重排
print("[计时] [HybridRetriever] 开始LLM重排 ...")
reranked_results = self.reranker.rerank_documents(
    query=query,
    documents=vector_results,
    documents_batch_size=documents_batch_size,
    llm_weight=llm_weight
)
t2 = time.time()
print(f"[计时] [HybridRetriever] LLM重排耗时: {t2-t1:.2f} 秒")
```

llm_reranking_sample_size控制首轮候选，documents_batch_size控制每批裁判材料，top_n控制最终输出，return_parent_pages决定返回整页还是切片；这里的Hybrid指向量加LLM重排，并非BM25融合。

### 配置向问题处理器传递

[企业报告交互问答增强版](../../应用侧/知识问答与文档处理/企业报告交互问答增强版/案例说明.md) · [src/pipeline.py，235–254行](../../应用侧/知识问答与文档处理/企业报告交互问答增强版/src/pipeline.py#L235-L254)

```python
def process_questions(self):
    # 处理所有问题，生成答案文件
    processor = QuestionsProcessor(
        vector_db_dir=self.paths.vector_db_dir,
        documents_dir=self.paths.documents_dir,
        questions_file_path=self.paths.questions_file_path,
        new_challenge_pipeline=True,
        subset_path=self.paths.subset_path,
        parent_document_retrieval=self.run_config.parent_document_retrieval,
        llm_reranking=self.run_config.llm_reranking,
        llm_reranking_sample_size=self.run_config.llm_reranking_sample_size,
        top_n_retrieval=self.run_config.top_n_retrieval,
        parallel_requests=self.run_config.parallel_requests,
        api_provider=self.run_config.api_provider,
        answering_model=self.run_config.answering_model,
        full_context=self.run_config.full_context            
    )

    output_path = self._get_next_available_filename(self.paths.answers_file_path)
```

Pipeline将运行配置映射给QuestionsProcessor，包括父页、重排和回答模型等选择，避免把预处理和在线回答混为一步。

## 应用方式差异

与基础流水线相比，这两份项目含实际代码差异，因此独立保留。交互版增加单问题页面与耗时记录；批处理增强版包含回归评估脚本。相同Docling解析和切分机制不重复摘录。
