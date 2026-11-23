# -*- coding: utf-8 -*-
"""以并行方式在 data/my_set 上跑通完整闭环：
分块(chunk) -> 建向量库(vector DBs) -> 并行问答(process_questions)。

配置沿用比赛最佳配置 max_nst_o3m（父文档检索 + LLM 重排 + qwen-turbo），
仅把 parallel_requests 提到 8，体现并行加速。
输出：data/my_set/answers_max_nst_o3m.json（已存在则自动编号）。
"""
import time
from pathlib import Path
from src.pipeline import Pipeline, configs

def main():
    root = Path(__file__).resolve().parent.parent / "data" / "my_set"

    cfg = configs["max_nst_o3m"]
    cfg.parallel_requests = 8  # Qwen-Turbo 限流 500 QPM，13 题用 8 并发安全
    pipeline = Pipeline(root, run_config=cfg)

    t0 = time.time()
    print("== 步骤1/3 分块报告 chunk_reports ==")
    pipeline.chunk_reports()
    print(f"   耗时 {time.time()-t0:.1f}s -> {pipeline.paths.documents_dir}")

    t1 = time.time()
    print("== 步骤2/3 创建向量库 create_vector_dbs ==")
    pipeline.create_vector_dbs()
    print(f"   耗时 {time.time()-t1:.1f}s -> {pipeline.paths.vector_db_dir}")

    t2 = time.time()
    print("== 步骤3/3 并行问答 process_questions (parallel_requests=8) ==")
    pipeline.process_questions()
    print(f"   耗时 {time.time()-t2:.1f}s")
    print(f"== 全部完成，总耗时 {time.time()-t0:.1f}s ==")

if __name__ == "__main__":
    main()
