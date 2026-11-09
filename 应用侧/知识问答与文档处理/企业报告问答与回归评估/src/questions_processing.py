"""
questions_processing.py —— 问题处理（问答主流程）模块。

QuestionsProcessor 是比赛问答流程的核心：
  1. 加载 questions.json（问题文本 + 答案类型 kind：name/number/boolean/names/comparative）
  2. 从问题中识别公司名（new_challenge_pipeline 下用 subset.csv 的公司名做正则匹配，
     支持一个问题涉及多家公司的比较题）
  3. 单公司问题：检索（向量 / 混合 / 全文）-> 拼接 RAG 上下文 ->
     按 kind 选择 prompts.py 中对应的结构化提示词 -> LLM 生成
     带 step_by_step_analysis / relevant_pages / final_answer 的答案
  4. 比较题：LLM 先把问题拆成各公司的子问题 -> 并行处理各公司 ->
     汇总各公司答案 -> 再用 LLM 得出最终比较结论
  5. 引用校验：_validate_page_references 剔除 LLM 幻觉出的、
     不在检索结果中的页码；不足最小小页数时用检索 top 页补齐
  6. 批量处理：支持多线程并行 + 断点保存（每批写一次 debug/提交文件）

输出：
  answers{config_suffix}.json           比赛提交格式（页码转为 0-based）
  answers{config_suffix}_debug.json     完整调试信息（推理过程、token 用量、错误堆栈）
"""
import json
from typing import Union, Dict, List, Optional
import re
from pathlib import Path
from src.retrieval import VectorRetriever, HybridRetriever
from src.api_requests import APIProcessor
from tqdm import tqdm
import pandas as pd
import threading
import concurrent.futures


class QuestionsProcessor:
    """问答主流程处理器。

    初始化参数要点：
      parent_document_retrieval  是否返回 chunk 所属整页（父文档检索）
      llm_reranking              是否用混合检索（向量召回 + LLM 重排）
      top_n_retrieval            最终送入 LLM 的上下文块/页数
      parallel_requests          问题级并行线程数（受 API 限流约束）
      api_provider/answering_model  回答所用 API 与模型（openai/ibm/gemini/dashscope）
      full_context               全文模式（不做检索，整份报告直接作为上下文）
    """

    def __init__(
        self,
        vector_db_dir: Union[str, Path] = './vector_dbs',
        documents_dir: Union[str, Path] = './documents',
        questions_file_path: Optional[Union[str, Path]] = None,
        new_challenge_pipeline: bool = False,
        subset_path: Optional[Union[str, Path]] = None,
        parent_document_retrieval: bool = False,  # 是否启用父文档检索
        llm_reranking: bool = False,              # 是否启用LLM重排
        llm_reranking_sample_size: int = 20,
        top_n_retrieval: int = 10,
        parallel_requests: int = 10,
        api_provider: str = "dashscope", # openai
        answering_model: str = "qwen-turbo-latest", # gpt-4o-2024-08-06
        full_context: bool = False
    ):
        # 初始化问题处理器，配置检索、模型、并发等参数
        self.questions = self._load_questions(questions_file_path)
        self.documents_dir = Path(documents_dir)
        self.vector_db_dir = Path(vector_db_dir)
        self.subset_path = Path(subset_path) if subset_path else None
        
        self.new_challenge_pipeline = new_challenge_pipeline
        self.return_parent_pages = parent_document_retrieval
        self.llm_reranking = llm_reranking
        self.llm_reranking_sample_size = llm_reranking_sample_size
        self.top_n_retrieval = top_n_retrieval
        self.answering_model = answering_model
        self.parallel_requests = parallel_requests
        self.api_provider = api_provider
        self.openai_processor = APIProcessor(provider=api_provider)
        self.full_context = full_context

        self.answer_details = []
        self.detail_counter = 0
        self._lock = threading.Lock()

    def _load_questions(self, questions_file_path: Optional[Union[str, Path]]) -> List[Dict[str, str]]:
        # 加载问题文件，返回问题列表
        if questions_file_path is None:
            return []
        with open(questions_file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def _format_retrieval_results(self, retrieval_results) -> str:
        """将检索结果格式化为RAG上下文字符串"""
        if not retrieval_results:
            return ""
        
        context_parts = []
        for result in retrieval_results:
            page_number = result['page']
            text = result['text']
            context_parts.append(f'Text retrieved from page {page_number}: \n"""\n{text}\n"""')
            
        return "\n\n---\n\n".join(context_parts)

    def _extract_references(self, pages_list: list, company_name: str) -> list:
        # 根据公司名和页码列表，提取引用信息
        if self.subset_path is None:
            raise ValueError("subset_path is required for new challenge pipeline when processing references.")
        self.companies_df = pd.read_csv(self.subset_path)

        # Find the company's SHA1 from the subset CSV
        matching_rows = self.companies_df[self.companies_df['company_name'] == company_name]
        if matching_rows.empty:
            company_sha1 = ""
        else:
            company_sha1 = matching_rows.iloc[0]['sha1']

        refs = []
        for page in pages_list:
            refs.append({"pdf_sha1": company_sha1, "page_index": page})
        return refs

    def _validate_page_references(self, claimed_pages: list, retrieval_results: list, min_pages: int = 2, max_pages: int = 8) -> list:
        """【流程步骤 7】引用校验（防幻觉）：
        1. 只保留确实出现在本次检索结果 retrieved_pages 中的页码；
        2. 不足 min_pages(默认2) 时，按检索排序依次补充真实页；
        3. 超过 max_pages(默认8) 时截断。
        返回的页码列表将用于生成最终 references。
        """
        if claimed_pages is None:
            claimed_pages = []
        
        retrieved_pages = [result['page'] for result in retrieval_results]
        
        validated_pages = [page for page in claimed_pages if page in retrieved_pages]
        
        if len(validated_pages) < len(claimed_pages):
            removed_pages = set(claimed_pages) - set(validated_pages)
            print(f"Warning: Removed {len(removed_pages)} hallucinated page references: {removed_pages}")
        
        if len(validated_pages) < min_pages and retrieval_results:
            existing_pages = set(validated_pages)
            
            for result in retrieval_results:
                page = result['page']
                if page not in existing_pages:
                    validated_pages.append(page)
                    existing_pages.add(page)
                    
                    if len(validated_pages) >= min_pages:
                        break
        
        if len(validated_pages) > max_pages:
            print(f"Trimming references from {len(validated_pages)} to {max_pages} pages")
            validated_pages = validated_pages[:max_pages]
        
        return validated_pages

    def get_answer_for_company(self, company_name: str, question: str, schema: str) -> dict:
        """【流程步骤 6】核心：检索 + 生成答案（单家公司）。

        分四小步：
          6.1 选检索器：llm_reranking=True -> HybridRetriever（向量召回 30 候选 + LLM 重排），
              否则 VectorRetriever；full_context=True 时直接 retrieve_all 返回整份报告
          6.2 retriever.retrieve_by_company_name()  -> 得到 top_n 个 {page, text, distance}
          6.3 _format_retrieval_results()           -> 拼成 RAG 上下文字符串
          6.4 APIProcessor.get_answer_from_rag_context() -> LLM 生成结构化答案
        之后的 new_challenge_pipeline 处理：
          _validate_page_references() 剔除幻觉页码并补齐 -> _extract_references()
          生成 [{pdf_sha1, page_index}] 引用列表
        """
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
                top_n=self.top_n_retrieval,
                return_parent_pages=self.return_parent_pages
            )
        
        if not retrieval_results:
            raise ValueError("No relevant context found")
        
        rag_context = self._format_retrieval_results(retrieval_results)
        answer_dict = self.openai_processor.get_answer_from_rag_context(
            question=question,
            rag_context=rag_context,
            schema=schema,
            model=self.answering_model
        )
        self.response_data = self.openai_processor.response_data
        if self.new_challenge_pipeline:
            pages = answer_dict.get("relevant_pages", [])
            validated_pages = self._validate_page_references(pages, retrieval_results)
            answer_dict["relevant_pages"] = validated_pages
            answer_dict["references"] = self._extract_references(validated_pages, company_name)
        return answer_dict

    def _extract_companies_from_subset(self, question_text: str) -> list[str]:
        """【流程步骤 5】从问题文本中提取公司名（问题路由的关键）。

        匹配规则（兼容中英文数据集）：
          1. 公司名按长度从长到短排序后逐一尝试，长名优先，
             命中后把名字从问题文本中删除，避免子串重复匹配（如
             "星辰科技" 是 "星辰科技股份有限公司" 的子串）；
          2. 先尝试带词边界的模式 `名字(?:\W|$)`（适合英文公司名，
             如 "Holley Inc." 后面跟空格/标点）；
          3. 词边界匹配失败则退化为纯包含匹配 —— 中文公司名后面通常
             直接跟"的""在"等字（\w），带边界会永远匹配不到。
        返回按出现顺序排列的去重公司名列表；长度 0/1/>1 分别驱动
        报错、单公司流程、比较题流程。
        """
        if not hasattr(self, 'companies_df'):
            if self.subset_path is None:
                raise ValueError("subset_path must be provided to use subset extraction")
            self.companies_df = pd.read_csv(self.subset_path)

        found_companies = []
        company_names = sorted(self.companies_df['company_name'].unique(), key=len, reverse=True)

        for company in company_names:
            escaped_company = re.escape(company)

            # 先尝试带词边界的匹配（英文公司名，避免子串误匹配）
            pattern = rf'{escaped_company}(?:\W|$)'
            if not re.search(pattern, question_text, re.IGNORECASE):
                # 退化方案：纯包含匹配（中文公司名后常直接跟"的"等中文字符）
                pattern = escaped_company

            if re.search(pattern, question_text, re.IGNORECASE):
                found_companies.append(company)
                question_text = re.sub(pattern, '', question_text, flags=re.IGNORECASE)

        return found_companies

    def process_question(self, question: str, schema: str):
        """【流程步骤 5】问题路由：从问题文本中识别公司 -> 决定走单公司还是比较题流程。

        - new_challenge_pipeline=True：用 subset.csv 的公司名表做不区分大小写的正则匹配，
          支持一个问题里出现多家公司；extracted_companies 即步骤 6 的路由依据
        - 仅 1 家公司 -> get_answer_for_company()（步骤 6）
        - 多家公司     -> process_comparative_question()（拆解->并行->汇总）
        """
        # 处理单个问题，支持多公司比较
        if self.new_challenge_pipeline:
            extracted_companies = self._extract_companies_from_subset(question)
        else:
            extracted_companies = re.findall(r'"([^"]*)"', question)
        
        if len(extracted_companies) == 0:
            raise ValueError("No company name found in the question.")
        
        if len(extracted_companies) == 1:
            company_name = extracted_companies[0]
            answer_dict = self.get_answer_for_company(company_name=company_name, question=question, schema=schema)
            return answer_dict
        else:
            return self.process_comparative_question(question, extracted_companies, schema)
    
    def _create_answer_detail_ref(self, answer_dict: dict, question_index: int) -> str:
        """创建答案详情的引用ID，并存储详细内容"""
        ref_id = f"#/answer_details/{question_index}"
        with self._lock:
            self.answer_details[question_index] = {
                "step_by_step_analysis": answer_dict['step_by_step_analysis'],
                "reasoning_summary": answer_dict['reasoning_summary'],
                "relevant_pages": answer_dict['relevant_pages'],
                "response_data": self.response_data,
                "self": ref_id
            }
        return ref_id

    def _calculate_statistics(self, processed_questions: List[dict], print_stats: bool = False) -> dict:
        """统计处理结果，包括总数、错误数、N/A数、成功数"""
        total_questions = len(processed_questions)
        error_count = sum(1 for q in processed_questions if "error" in q)
        na_count = sum(1 for q in processed_questions if (q.get("value") if "value" in q else q.get("answer")) == "N/A")
        success_count = total_questions - error_count - na_count
        if print_stats:
            print(f"\nFinal Processing Statistics:")
            print(f"Total questions: {total_questions}")
            print(f"Errors: {error_count} ({(error_count/total_questions)*100:.1f}%)")
            print(f"N/A answers: {na_count} ({(na_count/total_questions)*100:.1f}%)")
            print(f"Successfully answered: {success_count} ({(success_count/total_questions)*100:.1f}%)\n")
        
        return {
            "total_questions": total_questions,
            "error_count": error_count,
            "na_count": na_count,
            "success_count": success_count
        }

    def process_questions_list(self, questions_list: List[dict], output_path: str = None, submission_file: bool = False, team_email: str = "", submission_name: str = "", pipeline_details: str = "") -> dict:
        """【流程步骤 3】批量处理：给问题加索引 -> 按 parallel_requests 分批 -> 线程池并行
        -> 每批结束都调 _save_progress 落盘（断点保存，崩溃可续）。

        关键变量：
          questions_with_index      每个问题附加 "_question_index"，用于 answer_details 定位
          self.answer_details       预分配的列表，按索引存放每题的推理过程/错误堆栈
          parallel_threads          来自 RunConfig.parallel_requests（受 API 限流约束）
        """
        # 批量处理问题列表，支持并行与断点保存，返回处理结果和统计信息
        total_questions = len(questions_list)
        # 给每个问题加索引，便于后续答案详情定位
        questions_with_index = [{**q, "_question_index": i} for i, q in enumerate(questions_list)]
        self.answer_details = [None] * total_questions  # 预分配答案详情列表
        processed_questions = []
        parallel_threads = self.parallel_requests

        if parallel_threads <= 1:
            # 单线程顺序处理
            for question_data in tqdm(questions_with_index, desc="Processing questions"):
                processed_question = self._process_single_question(question_data)
                processed_questions.append(processed_question)
                if output_path:
                    self._save_progress(processed_questions, output_path, submission_file=submission_file, team_email=team_email, submission_name=submission_name, pipeline_details=pipeline_details)
        else:
            # 多线程并行处理
            with tqdm(total=total_questions, desc="Processing questions") as pbar:
                for i in range(0, total_questions, parallel_threads):
                    batch = questions_with_index[i : i + parallel_threads]
                    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_threads) as executor:
                        # executor.map 保证结果顺序与输入一致
                        batch_results = list(executor.map(self._process_single_question, batch))
                    processed_questions.extend(batch_results)
                    
                    if output_path:
                        self._save_progress(processed_questions, output_path, submission_file=submission_file, team_email=team_email, submission_name=submission_name, pipeline_details=pipeline_details)
                    pbar.update(len(batch_results))
        
        statistics = self._calculate_statistics(processed_questions, print_stats = True)
        
        return {
            "questions": processed_questions,
            "answer_details": self.answer_details,
            "statistics": statistics
        }

    def _process_single_question(self, question_data: dict) -> dict:
        """【流程步骤 4】单题包装层：取问题文本与类型(kind/schema) -> 调 process_question(步骤5)
        -> 把答案整理为提交格式 -> 任何异常都在 _handle_processing_error 中兜住，
        保证批量流程不因单题失败而中断。

        返回字典的字段（new_challenge_pipeline=True 时）：
          question_text / kind / value(最终答案) / references(引用页) /
          answer_details(指向 self.answer_details[i] 的 $ref)
        """
        question_index = question_data.get("_question_index", 0)
        
        if self.new_challenge_pipeline:
            question_text = question_data.get("text")
            schema = question_data.get("kind")
        else:
            question_text = question_data.get("question")
            schema = question_data.get("schema")
        try:
            answer_dict = self.process_question(question_text, schema)
            
            if "error" in answer_dict:
                detail_ref = self._create_answer_detail_ref({
                    "step_by_step_analysis": None,
                    "reasoning_summary": None,
                    "relevant_pages": None
                }, question_index)
                if self.new_challenge_pipeline:
                    return {
                        "question_text": question_text,
                        "kind": schema,
                        "value": None,
                        "references": [],
                        "error": answer_dict["error"],
                        "answer_details": {"$ref": detail_ref}
                    }
                else:
                    return {
                        "question": question_text,
                        "schema": schema,
                        "answer": None,
                        "error": answer_dict["error"],
                        "answer_details": {"$ref": detail_ref},
                    }
            detail_ref = self._create_answer_detail_ref(answer_dict, question_index)
            if self.new_challenge_pipeline:
                return {
                    "question_text": question_text,
                    "kind": schema,
                    "value": answer_dict.get("final_answer"),
                    "references": answer_dict.get("references", []),
                    "answer_details": {"$ref": detail_ref}
                }
            else:
                return {
                    "question": question_text,
                    "schema": schema,
                    "answer": answer_dict.get("final_answer"),
                    "answer_details": {"$ref": detail_ref},
                }
        except Exception as err:
            return self._handle_processing_error(question_text, schema, err, question_index)

    def _handle_processing_error(self, question_text: str, schema: str, err: Exception, question_index: int) -> dict:
        """
        处理问题处理过程中的异常。
        记录错误详情并返回包含错误信息的字典。
        """
        import traceback
        error_message = str(err)
        tb = traceback.format_exc()
        error_ref = f"#/answer_details/{question_index}"
        error_detail = {
            "error_traceback": tb,
            "self": error_ref
        }
        
        with self._lock:
            self.answer_details[question_index] = error_detail
        
        print(f"Error encountered processing question: {question_text}")
        print(f"Error type: {type(err).__name__}")
        print(f"Error message: {error_message}")
        print(f"Full traceback:\n{tb}\n")
        
        if self.new_challenge_pipeline:
            return {
                "question_text": question_text,
                "kind": schema,
                "value": None,
                "references": [],
                "error": f"{type(err).__name__}: {error_message}",
                "answer_details": {"$ref": error_ref}
            }
        else:
            return {
                "question": question_text,
                "schema": schema,
                "answer": None,
                "error": f"{type(err).__name__}: {error_message}",
                "answer_details": {"$ref": error_ref},
            }

    def _post_process_submission_answers(self, processed_questions: List[dict]) -> List[dict]:
        """
        提交格式后处理：
        1. 页码从1-based转为0-based
        2. N/A答案清空引用
        3. 格式化为比赛提交schema
        4. 包含step_by_step_analysis
        """
        submission_answers = []
        
        for q in processed_questions:
            question_text = q.get("question_text") or q.get("question")
            kind = q.get("kind") or q.get("schema")
            value = "N/A" if "error" in q else (q.get("value") if "value" in q else q.get("answer"))
            references = q.get("references", [])
            
            answer_details_ref = q.get("answer_details", {}).get("$ref", "")
            step_by_step_analysis = None
            if answer_details_ref and answer_details_ref.startswith("#/answer_details/"):
                try:
                    index = int(answer_details_ref.split("/")[-1])
                    if 0 <= index < len(self.answer_details) and self.answer_details[index]:
                        step_by_step_analysis = self.answer_details[index].get("step_by_step_analysis")
                except (ValueError, IndexError):
                    pass
            
            # Clear references if value is N/A
            if value == "N/A":
                references = []
            else:
                # Convert page indices from one-based to zero-based (competition requires 0-based page indices, but for debugging it is easier to use 1-based)
                references = [
                    {
                        "pdf_sha1": ref["pdf_sha1"],
                        "page_index": ref["page_index"] - 1
                    }
                    for ref in references
                ]
            
            submission_answer = {
                "question_text": question_text,
                "kind": kind,
                "value": value,
                "references": references,
            }
            
            if step_by_step_analysis:
                submission_answer["reasoning_process"] = step_by_step_analysis
            
            submission_answers.append(submission_answer)
        
        return submission_answers

    def _save_progress(self, processed_questions: List[dict], output_path: Optional[str], submission_file: bool = False, team_email: str = "", submission_name: str = "", pipeline_details: str = ""):
        """【流程步骤 8】落盘（每批处理完都会调用，实现断点保存）：
        - 始终写 {name}_debug.json：questions + answer_details（推理过程/错误堆栈）+ statistics
        - submission_file=True 时再写正式提交文件 answers{suffix}.json：
          _post_process_submission_answers() 负责把页码从 1-based 转为比赛要求的
          0-based，并给 N/A 答案清空引用、附加 reasoning_process
        """
        if output_path:
            statistics = self._calculate_statistics(processed_questions)
            
            # Prepare debug content
            result = {
                "questions": processed_questions,
                "answer_details": self.answer_details,
                "statistics": statistics
            }
            output_file = Path(output_path)
            debug_file = output_file.with_name(output_file.stem + "_debug" + output_file.suffix)
            with open(debug_file, 'w', encoding='utf-8') as file:
                json.dump(result, file, ensure_ascii=False, indent=2)
            
            if submission_file:
                # Post-process answers for submission
                submission_answers = self._post_process_submission_answers(processed_questions)
                submission = {
                    "answers": submission_answers,
                    "team_email": team_email,
                    "submission_name": submission_name,
                    "details": pipeline_details
                }
                with open(output_file, 'w', encoding='utf-8') as file:
                    json.dump(submission, file, ensure_ascii=False, indent=2)

    def process_all_questions(self, output_path: str = 'questions_with_answers.json', team_email: str = "79250515615@yandex.com", submission_name: str = "Ilia_Ris SO CoT + Parent Document Retrieval", submission_file: bool = False, pipeline_details: str = ""):
        """【流程步骤 2】问答总入口：对 questions.json 中的全部问题执行批量处理。

        内部直接转到 process_questions_list（步骤 3），本方法只是默认参数的装配层。
        """
        result = self.process_questions_list(
            self.questions,
            output_path,
            submission_file=submission_file,
            team_email=team_email,
            submission_name=submission_name,
            pipeline_details=pipeline_details
        )
        return result

    def process_comparative_question(self, question: str, companies: List[str], schema: str) -> dict:
        """
        处理多公司比较类问题：
        1. 先将比较问题重写为单公司问题
        2. 并行处理每个公司
        3. 汇总结果并生成最终比较答案
        """
        # Step 1: Rephrase the comparative question
        rephrased_questions = self.openai_processor.get_rephrased_questions(
            original_question=question,
            companies=companies
        )
        
        individual_answers = {}
        aggregated_references = []
        
        # Step 2: Process each individual question in parallel
        def process_company_question(company: str) -> tuple[str, dict]:
            """Helper function to process one company's question and return (company, answer)"""
            sub_question = rephrased_questions.get(company)
            if not sub_question:
                raise ValueError(f"Could not generate sub-question for company: {company}")
            
            answer_dict = self.get_answer_for_company(
                company_name=company, 
                question=sub_question, 
                schema="number"
            )
            return company, answer_dict

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_company = {
                executor.submit(process_company_question, company): company 
                for company in companies
            }
            
            for future in concurrent.futures.as_completed(future_to_company):
                try:
                    company, answer_dict = future.result()
                    individual_answers[company] = answer_dict
                    
                    company_references = answer_dict.get("references", [])
                    aggregated_references.extend(company_references)
                except Exception as e:
                    company = future_to_company[future]
                    print(f"Error processing company {company}: {str(e)}")
                    raise
        
        # Remove duplicate references
        unique_refs = {}
        for ref in aggregated_references:
            key = (ref.get("pdf_sha1"), ref.get("page_index"))
            unique_refs[key] = ref
        aggregated_references = list(unique_refs.values())
        
        # Step 3: Get the comparative answer using all individual answers
        comparative_answer = self.openai_processor.get_answer_from_rag_context(
            question=question,
            rag_context=individual_answers,
            schema="comparative",
            model=self.answering_model
        )
        self.response_data = self.openai_processor.response_data
        
        comparative_answer["references"] = aggregated_references
        return comparative_answer
    