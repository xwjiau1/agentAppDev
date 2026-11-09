"""
retrieval.py —— 检索模块。

提供三种检索器：
  BM25Retriever   稀疏检索：加载 pickled BM25 索引，按词项匹配打分
  VectorRetriever 稠密检索：对查询做 embedding，在对应公司的 FAISS 索引
                  （IndexFlatIP，余弦相似度）中查 top_n 最近 chunk；
                  支持 parent_document_retrieval（返回 chunk 所属整页文本）
  HybridRetriever 混合检索：VectorRetriever 召回更多候选
                  （llm_reranking_sample_size 个）-> LLMReranker 打分 ->
                  向量分与 LLM 分加权融合 -> 取 top_n

所有检索器都按公司名定位目标报告（每份报告/公司独立建库）。
"""
import json
import logging
from typing import List, Tuple, Dict, Union
from rank_bm25 import BM25Okapi
import pickle
from pathlib import Path
import faiss
from openai import OpenAI
from dotenv import load_dotenv
import os
import numpy as np
from src.reranking import LLMReranker

_log = logging.getLogger(__name__)


def _faiss_read_index(path):
    """读取 FAISS 索引，兼容 Windows 中文路径。

    FAISS 底层用 fopen（ANSI 代码页）打开文件，遇到中文等非 ASCII 字符的路径
    会报 "could not open ... for reading"。GetShortPathNameW 短路径方案在本项目
    的目录上只被部分转换、仍然包含中文字符，因此改用更稳妥的办法：
    先把索引文件复制到系统临时目录（纯 ASCII 路径），再让 FAISS 读取副本。
    索引文件仅几 MB，复制开销可忽略；同名文件只复制一次。
    """
    path_str = str(path)
    if os.name == "nt":
        try:
            path_str.encode("ascii")
        except UnicodeEncodeError:
            import tempfile
            import shutil
            cache_dir = os.path.join(tempfile.gettempdir(), "rag_faiss_cache")
            os.makedirs(cache_dir, exist_ok=True)
            cached = os.path.join(cache_dir, os.path.basename(path_str))
            if not os.path.exists(cached) or os.path.getsize(cached) != os.path.getsize(path_str):
                shutil.copyfile(path_str, cached)
            path_str = cached
    return faiss.read_index(path_str)


class BM25Retriever:
    def __init__(self, bm25_db_dir: Path, documents_dir: Path):
        # 初始化BM25检索器，指定BM25索引和文档目录
        self.bm25_db_dir = bm25_db_dir
        self.documents_dir = documents_dir
        
    def retrieve_by_company_name(self, company_name: str, query: str, top_n: int = 3, return_parent_pages: bool = False) -> List[Dict]:
        # 按公司名检索相关文本块，返回BM25分数最高的top_n个块
        document_path = None
        for path in self.documents_dir.glob("*.json"):
            with open(path, 'r', encoding='utf-8') as f:
                doc = json.load(f)
                if doc["metainfo"]["company_name"] == company_name:
                    document_path = path
                    document = doc
                    break
                    
        if document_path is None:
            raise ValueError(f"No report found with '{company_name}' company name.")
            
        # 加载对应的BM25索引
        bm25_path = self.bm25_db_dir / f"{document['metainfo']['sha1_name']}.pkl"
        with open(bm25_path, 'rb') as f:
            bm25_index = pickle.load(f)
            
        # 获取文档内容和BM25索引
        document = document
        chunks = document["content"]["chunks"]
        pages = document["content"]["pages"]
        
        # 计算BM25分数
        tokenized_query = query.split()
        scores = bm25_index.get_scores(tokenized_query)
        
        actual_top_n = min(top_n, len(scores))
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:actual_top_n]
        
        retrieval_results = []
        seen_pages = set()
        
        for index in top_indices:
            score = round(float(scores[index]), 4)
            chunk = chunks[index]
            parent_page = next(page for page in pages if page["page"] == chunk["page"])
            
            if return_parent_pages:
                if parent_page["page"] not in seen_pages:
                    seen_pages.add(parent_page["page"])
                    result = {
                        "distance": score,
                        "page": parent_page["page"],
                        "text": parent_page["text"]
                    }
                    retrieval_results.append(result)
            else:
                result = {
                    "distance": score,
                    "page": chunk["page"],
                    "text": chunk["text"]
                }
                retrieval_results.append(result)
        
        return retrieval_results



class VectorRetriever:
    """向量检索器：加载所有（文档 JSON + FAISS 索引）对，按公司名检索 top_n。

    关键参数：
      return_parent_pages  父文档检索开关：为 True 时返回 chunk 所属整页文本
                           （按页去重），而非 chunk 本身
      embedding_provider   "dashscope"（默认，text-embedding-v1）或 "openai"
                           （text-embedding-3-large）
    """
    def __init__(self, vector_db_dir: Path, documents_dir: Path, embedding_provider: str = "dashscope"):
        # 初始化向量检索器，加载所有向量库和文档
        self.vector_db_dir = vector_db_dir
        self.documents_dir = documents_dir
        self.all_dbs = self._load_dbs()
        # 默认使用 dashscope 作为 embedding provider
        self.embedding_provider = embedding_provider.lower()
        self.llm = self._set_up_llm()

    def _set_up_llm(self):
        # 根据 embedding_provider 初始化对应的 LLM 客户端
        load_dotenv()
        if self.embedding_provider == "openai":
            llm = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                timeout=None,
                max_retries=2
            )
            return llm
        elif self.embedding_provider == "dashscope":
            import dashscope
            dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
            return None  # dashscope 不需要 client 对象
        else:
            raise ValueError(f"不支持的 embedding provider: {self.embedding_provider}")

    def _get_embedding(self, text: str):
        # 根据 embedding_provider 获取文本的向量表示
        if self.embedding_provider == "openai":
            embedding = self.llm.embeddings.create(
                input=text,
                model="text-embedding-3-large"
            )
            return embedding.data[0].embedding
        elif self.embedding_provider == "dashscope":
            import dashscope
            rsp = dashscope.TextEmbedding.call(
                model="text-embedding-v1",
                input=[text]
            )
            # 兼容 dashscope 返回格式，不能用 resp.output，需用 resp['output']
            if 'output' in rsp and 'embeddings' in rsp['output']:
                # 多条输入（本处只有一条）
                emb = rsp['output']['embeddings'][0]
                if emb['embedding'] is None or len(emb['embedding']) == 0:
                    raise RuntimeError(f"DashScope返回的embedding为空，text_index={emb.get('text_index', None)}")
                return emb['embedding']
            elif 'output' in rsp and 'embedding' in rsp['output']:
                # 兼容单条输入格式
                if rsp['output']['embedding'] is None or len(rsp['output']['embedding']) == 0:
                    raise RuntimeError("DashScope返回的embedding为空")
                return rsp['output']['embedding']
            else:
                raise RuntimeError(f"DashScope embedding API返回格式异常: {rsp}")
        else:
            raise ValueError(f"不支持的 embedding provider: {self.embedding_provider}")

    @staticmethod
    def set_up_llm():
        # 静态方法，初始化OpenAI LLM
        load_dotenv()
        llm = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=None,
            max_retries=2
        )
        return llm

    def _load_dbs(self):
        # 加载所有向量库和对应文档，建立映射
        all_dbs = []
        # 获取所有JSON文档路径
        all_documents_paths = list(self.documents_dir.glob('*.json'))
        vector_db_files = {db_path.stem: db_path for db_path in self.vector_db_dir.glob('*.faiss')}
        
        for document_path in all_documents_paths:
            stem = document_path.stem
            if stem not in vector_db_files:
                _log.warning(f"No matching vector DB found for document {document_path.name}")
                continue
            try:
                with open(document_path, 'r', encoding='utf-8') as f:
                    document = json.load(f)
            except Exception as e:
                _log.error(f"Error loading JSON from {document_path.name}: {e}")
                continue
            
            # 校验文档结构
            if not (isinstance(document, dict) and "metainfo" in document and "content" in document):
                _log.warning(f"Skipping {document_path.name}: does not match the expected schema.")
                continue
            
            try:
                vector_db = _faiss_read_index(vector_db_files[stem])
            except Exception as e:
                _log.error(f"Error reading vector DB for {document_path.name}: {e}")
                continue
                
            report = {
                "name": stem,
                "vector_db": vector_db,
                "document": document
            }
            all_dbs.append(report)
        return all_dbs

    @staticmethod
    def get_strings_cosine_similarity(str1, str2):
        # 计算两个字符串的余弦相似度（通过嵌入）
        llm = VectorRetriever.set_up_llm()
        embeddings = llm.embeddings.create(input=[str1, str2], model="text-embedding-3-large")
        embedding1 = embeddings.data[0].embedding
        embedding2 = embeddings.data[1].embedding
        similarity_score = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        similarity_score = round(similarity_score, 4)
        return similarity_score

    def retrieve_by_company_name(self, company_name: str, query: str, llm_reranking_sample_size: int = None, top_n: int = 3, return_parent_pages: bool = False) -> List[Tuple[str, float]]:
        """【流程步骤 6.2b】向量召回：问题 embedding -> FAISS 内积检索 -> 取 top_n。

        关键变量：
          self.all_dbs        初始化时加载的全部 (文档JSON, FAISS索引) 对（每个公司一份）
          target_report       按 company_name 命中的那份报告
          embedding_array     问题向量（DashScope text-embedding-v1）
          distances, indices  FAISS 返回的内积分数与 chunk 下标（分数越高越相似）
        return_parent_pages=True 时（父文档检索），把 chunk 换成其所属整页文本并按页去重。
        """
        # 按公司名检索相关文本块，返回向量距离最近的top_n个块
        target_report = None
        for report in self.all_dbs:
            document = report.get("document", {})
            metainfo = document.get("metainfo")
            if not metainfo:
                _log.error(f"Report '{report.get('name')}' is missing 'metainfo'!")
                raise ValueError(f"Report '{report.get('name')}' is missing 'metainfo'!")
            if metainfo.get("company_name") == company_name:
                target_report = report
                break
        
        if target_report is None:
            _log.error(f"No report found with '{company_name}' company name.")
            raise ValueError(f"No report found with '{company_name}' company name.")
        
        document = target_report["document"]
        vector_db = target_report["vector_db"]
        chunks = document["content"]["chunks"]
        pages = document["content"]["pages"]
        
        actual_top_n = min(top_n, len(chunks))
        
        # 获取 query 的 embedding，支持 openai/dashscope
        embedding = self._get_embedding(query)
        embedding_array = np.array(embedding, dtype=np.float32).reshape(1, -1)
        distances, indices = vector_db.search(x=embedding_array, k=actual_top_n)
    
        retrieval_results = []
        seen_pages = set()
        
        for distance, index in zip(distances[0], indices[0]):
            distance = round(float(distance), 4)
            chunk = chunks[index]
            parent_page = next(page for page in pages if page["page"] == chunk["page"])
            if return_parent_pages:
                if parent_page["page"] not in seen_pages:
                    seen_pages.add(parent_page["page"])
                    result = {
                        "distance": distance,
                        "page": parent_page["page"],
                        "text": parent_page["text"]
                    }
                    retrieval_results.append(result)
            else:
                result = {
                    "distance": distance,
                    "page": chunk["page"],
                    "text": chunk["text"]
                }
                retrieval_results.append(result)
            
        return retrieval_results

    def retrieve_all(self, company_name: str) -> List[Dict]:
        # 检索公司所有文本块，返回全部内容
        target_report = None
        for report in self.all_dbs:
            document = report.get("document", {})
            metainfo = document.get("metainfo")
            if not metainfo:
                continue
            if metainfo.get("company_name") == company_name:
                target_report = report
                break
        
        if target_report is None:
            _log.error(f"No report found with '{company_name}' company name.")
            raise ValueError(f"No report found with '{company_name}' company name.")
        
        document = target_report["document"]
        pages = document["content"]["pages"]
        
        all_pages = []
        for page in sorted(pages, key=lambda p: p["page"]):
            result = {
                "distance": 0.5,
                "page": page["page"],
                "text": page["text"]
            }
            all_pages.append(result)
            
        return all_pages


class HybridRetriever:
    """混合检索器：向量召回 + LLM 重排。

    流程：VectorRetriever 召回 llm_reranking_sample_size 个候选 chunk
         -> LLMReranker 按 batch 打分并与向量分加权融合
         -> 按 combined_score 降序取 top_n
    """
    def __init__(self, vector_db_dir: Path, documents_dir: Path):
        self.vector_retriever = VectorRetriever(vector_db_dir, documents_dir)
        self.reranker = LLMReranker()
        
    def retrieve_by_company_name(
        self, 
        company_name: str, 
        query: str, 
        llm_reranking_sample_size: int = 28,
        documents_batch_size: int = 2,
        top_n: int = 6,
        llm_weight: float = 0.7,
        return_parent_pages: bool = False
    ) -> List[Dict]:
        """【流程步骤 6.2a】混合检索（llm_reranking=True 时由步骤 6.1 选中）：

        先以 llm_reranking_sample_size(默认30) 为候选数做向量召回（6.2b），
        再经 LLMReranker 打分融合（6.2c），最后截取 top_n(默认6，实际由 top_n_retrieval 传入)。

        参数：
          company_name            目标公司（决定检索哪份报告的索引）
          query                   查询文本（即问题）
          llm_reranking_sample_size  向量召回的候选数量（重排的"原料"）
          documents_batch_size    每批送入 LLM 打分的文档数
          top_n                   融合排序后返回的条数
          llm_weight              LLM 分数权重（其余给向量分数）
          return_parent_pages     是否返回 chunk 所属整页（父文档检索）
        返回：按 combined_score 降序的文档字典列表（page/text/distance 等字段）。
        """
        # Get initial results from vector retriever
        vector_results = self.vector_retriever.retrieve_by_company_name(
            company_name=company_name,
            query=query,
            top_n=llm_reranking_sample_size,
            return_parent_pages=return_parent_pages
        )
        
        # Rerank results using LLM
        reranked_results = self.reranker.rerank_documents(
            query=query,
            documents=vector_results,
            documents_batch_size=documents_batch_size,
            llm_weight=llm_weight
        )
        
        return reranked_results[:top_n]
