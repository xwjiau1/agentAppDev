"""
ingestion.py —— 索引构建（入库）模块。

包含两个构建器：
  BM25Ingestor      基于 rank_bm25 的稀疏检索索引，按报告（公司）分别建索引，
                    每个索引以 pickle 保存（{sha1}.pkl）
  VectorDBIngestor  基于 DashScope text-embedding-v1 + FAISS 的稠密向量索引，
                    每份报告单独一个 FAISS 索引（{sha1}.faiss），
                    采用 IndexFlatIP（内积），适用于已归一化的 embedding 做余弦相似度
"""
import os
import json
import pickle
from typing import List, Union
from pathlib import Path
from tqdm import tqdm

from dotenv import load_dotenv
from openai import OpenAI
from rank_bm25 import BM25Okapi
import faiss
import numpy as np
from tenacity import retry, wait_fixed, stop_after_attempt
import dashscope
from dashscope import TextEmbedding


def _faiss_write_index(index, path):
    """写入 FAISS 索引，兼容 Windows 中文路径。

    与 retrieval._faiss_read_index 同一问题的写侧：FAISS 底层用 fopen（ANSI
    代码页）创建文件，中文路径会报 "could not open ... for writing"。
    解决办法：先写到系统临时目录（纯 ASCII 路径），再移动回目标位置。
    """
    path_str = str(path)
    if os.name == "nt":
        try:
            path_str.encode("ascii")
        except UnicodeEncodeError:
            import tempfile
            import shutil
            tmp_path = os.path.join(tempfile.gettempdir(), f"faiss_write_{os.getpid()}.faiss")
            faiss.write_index(index, tmp_path)
            shutil.move(tmp_path, path_str)
            return
    faiss.write_index(index, path_str)


# BM25Ingestor：BM25索引构建与保存工具
class BM25Ingestor:
    """稀疏检索索引构建器：对每份报告的 chunk 列表分别建一个 BM25Okapi 索引。

    索引与文档一一对应（文件名均为 sha1），检索时按公司找到报告后再加载对应 pkl。
    """
    def __init__(self):
        pass

    def create_bm25_index(self, chunks: List[str]) -> BM25Okapi:
        """从文本块列表创建BM25索引（简单按空白分词）"""
        tokenized_chunks = [chunk.split() for chunk in chunks]
        return BM25Okapi(tokenized_chunks)
    
    def process_reports(self, all_reports_dir: Path, output_dir: Path):
        """
        批量处理所有报告，生成并保存BM25索引。
        参数：
            all_reports_dir (Path): 存放JSON报告的目录
            output_dir (Path): 保存BM25索引的目录
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        all_report_paths = list(all_reports_dir.glob("*.json"))

        for report_path in tqdm(all_report_paths, desc="Processing reports for BM25"):
            # 加载报告
            with open(report_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
                
            # 提取文本块并创建BM25索引
            text_chunks = [chunk['text'] for chunk in report_data['content']['chunks']]
            bm25_index = self.create_bm25_index(text_chunks)
            
            # 保存BM25索引，文件名用sha1_name
            sha1_name = report_data["metainfo"]["sha1_name"]
            output_file = output_dir / f"{sha1_name}.pkl"
            with open(output_file, 'wb') as f:
                pickle.dump(bm25_index, f)
                
        print(f"Processed {len(all_report_paths)} reports")

# VectorDBIngestor：向量库构建与保存工具
class VectorDBIngestor:
    """稠密向量索引构建器：DashScope embedding + FAISS，每份报告一个索引文件。

    实现细节：
      - embedding 分批调用（每批 25 条），带 tenacity 重试（间隔 20s，最多 2 次）
      - FAISS 使用 IndexFlatIP（内积），适用于已归一化的向量做余弦相似度
      - DashScope 返回体有单条/多条两种格式，均已做兼容处理
    """
    def __init__(self):
        # 初始化DashScope API Key
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

    @retry(wait=wait_fixed(20), stop=stop_after_attempt(2))
    def _get_embeddings(self, text: Union[str, List[str]], model: str = "text-embedding-v1") -> List[float]:
        # 获取文本或文本块的嵌入向量，支持重试（使用阿里云DashScope，分批处理）
        if isinstance(text, str) and not text.strip():
            raise ValueError("Input text cannot be an empty string.")
        
        # 保证 input 为一维字符串列表或单个字符串
        if isinstance(text, list):
            text_chunks = text
        else:
            text_chunks = [text]

        # 类型检查，确保每一项都是字符串
        if not all(isinstance(x, str) for x in text_chunks):
            raise ValueError("所有待嵌入文本必须为字符串类型！实际类型: {}".format([type(x) for x in text_chunks]))

        # 过滤空字符串
        text_chunks = [x for x in text_chunks if x.strip()]
        if not text_chunks:
            raise ValueError("所有待嵌入文本均为空字符串！")
        # print('start embedding ================================')
        embeddings = []
        MAX_BATCH_SIZE = 25
        LOG_FILE = 'embedding_error.log'
        for i in range(0, len(text_chunks), MAX_BATCH_SIZE):
            batch = text_chunks[i:i+MAX_BATCH_SIZE]
            resp = TextEmbedding.call(
                model=TextEmbedding.Models.text_embedding_v1,
                input=batch
            )
            # print('i=',i)
            # print('resp=',resp)
            # with open(LOG_FILE, 'a', encoding='utf-8') as f:
            #     f.write('i='+str(i)+'\n')
            #     f.write('resp='+str(resp)+'\n')
            # 兼容单条和多条输入
            if 'output' in resp and 'embeddings' in resp['output']:
                print('11111111')
                for emb in resp['output']['embeddings']:
                    if emb['embedding'] is None or len(emb['embedding']) == 0:
                        error_text = batch[emb.text_index] if hasattr(emb, 'text_index') else None
                        with open(LOG_FILE, 'a', encoding='utf-8') as f:
                            f.write(f"DashScope返回的embedding为空，text_index={getattr(emb, 'text_index', None)}，文本内容如下：\n{error_text}\n{'-'*60}\n")
                        raise RuntimeError(f"DashScope返回的embedding为空，text_index={getattr(emb, 'text_index', None)}，文本内容已写入 {LOG_FILE}")
                    embeddings.append(emb['embedding'])
            elif 'output' in resp and 'embedding' in resp['output']:
                if resp['output']['embedding'] is None or len(resp['output']['embedding']) == 0:
                    print('22222222')
                    with open(LOG_FILE, 'a', encoding='utf-8') as f:
                        f.write("DashScope返回的embedding为空，文本内容如下：\n{}\n{}\n".format(batch[0] if batch else None, '-'*60))
                    raise RuntimeError("DashScope返回的embedding为空，文本内容已写入 {}".format(LOG_FILE))
                embeddings.append(resp.output.embedding)
            else:
                print('33333333')
                raise RuntimeError(f"DashScope embedding API返回格式异常: {resp}")
        return embeddings

    def _create_vector_db(self, embeddings: List[float]):
        # 用faiss构建向量库，采用内积（余弦距离）
        embeddings_array = np.array(embeddings, dtype=np.float32)
        dimension = len(embeddings[0])
        index = faiss.IndexFlatIP(dimension)  # Cosine distance
        index.add(embeddings_array)
        return index
    
    def _process_report(self, report: dict):
        # 针对单份报告，提取文本块并生成向量库
        text_chunks = [chunk['text'] for chunk in report['content']['chunks']]
        embeddings = self._get_embeddings(text_chunks)
        index = self._create_vector_db(embeddings)
        return index

    def process_reports(self, all_reports_dir: Path, output_dir: Path):
        # 批量处理所有报告，生成并保存faiss向量库
        all_report_paths = list(all_reports_dir.glob("*.json"))
        output_dir.mkdir(parents=True, exist_ok=True)

        for report_path in tqdm(all_report_paths, desc="Processing reports"):
            with open(report_path, 'r', encoding='utf-8') as file:
                report_data = json.load(file)
            index = self._process_report(report_data)
            sha1_name = report_data["metainfo"]["sha1_name"]
            faiss_file_path = output_dir / f"{sha1_name}.faiss"
            _faiss_write_index(index, faiss_file_path)

        print(f"Processed {len(all_report_paths)} reports")