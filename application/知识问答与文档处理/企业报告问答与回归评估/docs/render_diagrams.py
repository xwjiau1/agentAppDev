# -*- coding: utf-8 -*-
"""渲染项目结构图与流程图为 PNG（使用 matplotlib + 内置 CJK 字体）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager
import os

# 查找可用中文字体
cjk = None
for f in font_manager.fontManager.ttflist:
    if any(k in f.name for k in ("Noto Sans CJK", "Microsoft YaHei", "SimHei", "WenQuanYi", "Source Han")):
        cjk = f.name
        break
if cjk:
    plt.rcParams["font.family"] = cjk
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.join(os.path.dirname(__file__), "diagrams")
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, text, fc="#EAF2FB", ec="#3B6EA5", fs=9):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.02,rounding_size=0.03",
                 fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(ax, p1, p2, color="#555555"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=14,
                 lw=1.3, color=color, shrinkA=2, shrinkB=2))


# ============ 图1：总体架构图 ============
fig, ax = plt.subplots(figsize=(11, 8.2))
ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
ax.set_title("RAG-Challenge-2 总体架构图", fontsize=15, pad=14)

box(ax, 0.3, 8.6, 3.6, 1.1, "入口层\nmain.py（click CLI）\nsrc/pipeline.py（Pipeline 编排）", fc="#FFF3D6", ec="#C8901A")
box(ax, 4.6, 8.6, 5.1, 1.1, "提示词层\nsrc/prompts.py（SO CoT 提示词 + Pydantic Schema）", fc="#F3E8FB", ec="#8A5CB8")

# 离线
ax.add_patch(FancyBboxPatch((0.3, 4.6), 5.9, 3.3, boxstyle="round,pad=0.05",
             fc="#F2F8F2", ec="#5A9E5A", lw=1.5))
ax.text(3.25, 7.55, "离线预处理（建库）", ha="center", fontsize=11, color="#2F6B2F", weight="bold")
box(ax, 0.6, 6.3, 2.6, 0.95, "pdf_parsing.py\nPDFParser + Docling", fs=8.5)
box(ax, 3.5, 6.3, 2.5, 0.95, "tables_serialization.py\nTableSerializer（LLM）", fs=8.5)
box(ax, 0.6, 5.1, 2.6, 0.95, "parsed_reports_merging.py\nPageTextPreparation", fs=8.5)
box(ax, 3.5, 5.1, 2.5, 0.95, "text_splitter.py\nTextSplitter 分块", fs=8.5)
box(ax, 2.0, 4.75 - 0.62, 2.7, 0.62, "ingestion.py：FAISS 向量库 + BM25 索引", fc="#E3F1E3", ec="#5A9E5A", fs=8.5)

# 在线
ax.add_patch(FancyBboxPatch((6.5, 4.6), 3.2, 3.3, boxstyle="round,pad=0.05",
             fc="#FDF0EF", ec="#C05A4E", lw=1.5))
ax.text(8.1, 7.55, "在线问答", ha="center", fontsize=11, color="#A03C30", weight="bold")
box(ax, 6.7, 6.3, 2.8, 0.95, "questions_processing.py\nQuestionsProcessor 主流程", fc="#FBEAE8", ec="#C05A4E", fs=8.5)
box(ax, 6.7, 5.1, 2.8, 0.95, "retrieval.py + reranking.py\n向量/BM25/混合检索 + LLM重排", fc="#FBEAE8", ec="#C05A4E", fs=8.5)

# 外部服务
box(ax, 0.8, 1.4, 2.6, 1.3, "外部服务\nDashScope（Qwen）\nEmbedding + 对话", fc="#EEF1F6", ec="#6B7A99", fs=8.5)
box(ax, 3.9, 1.4, 2.6, 1.3, "OpenAI / Gemini / IBM\n（备选 API Provider）", fc="#EEF1F6", ec="#6B7A99", fs=8.5)
box(ax, 7.0, 1.4, 2.3, 1.3, "Docling 模型\nPDF 解析后端", fc="#EEF1F6", ec="#6B7A99", fs=8.5)

arrow(ax, (2.1, 8.6), (2.1, 7.95))
arrow(ax, (2.6, 6.3), (2.6, 6.05))
arrow(ax, (4.8, 6.3), (4.8, 6.05))
arrow(ax, (3.35, 5.1), (3.35, 4.75))
arrow(ax, (2.1, 4.6 - 0.0), (2.1, 2.75), color="#999999")
arrow(ax, (7.0, 8.6), (7.6, 7.25))
arrow(ax, (8.1, 6.3), (8.1, 6.05))
arrow(ax, (8.1, 5.1), (5.6, 2.75), color="#999999")
plt.tight_layout()
plt.savefig(os.path.join(OUT, "01_总体架构图.png"), dpi=160, bbox_inches="tight")
plt.close()

# ============ 图2：离线建库流程图 ============
fig, ax = plt.subplots(figsize=(9, 10.5))
ax.set_xlim(0, 10); ax.set_ylim(0, 12); ax.axis("off")
ax.set_title("离线预处理流程（建库 Pipeline）", fontsize=15, pad=14)

steps = [
    ("pdf_reports/*.pdf  年报 PDF", "#EEF1F6", "#6B7A99"),
    ("① PDFParser（Docling）\nOCR + 表格结构识别", "#EAF2FB", "#3B6EA5"),
    ("② JsonReportProcessor\n展开引用、按页归组文本/表格/图片", "#EAF2FB", "#3B6EA5"),
    ("01_parsed_reports/*.json\n结构化 JSON", "#FFF3D6", "#C8901A"),
    ("③ TableSerializer（可选，LLM）\n表格 → 上下文独立信息块\n写回 serialized 字段", "#F3E8FB", "#8A5CB8"),
    ("④ PageTextPreparation\n过滤页脚/图片、组块合并、字符清洗", "#EAF2FB", "#3B6EA5"),
    ("02_merged_reports/*.json\n每页一段干净文本", "#FFF3D6", "#C8901A"),
    ("⑤ TextSplitter 分块\n300 tokens / 重叠 50 / 表格单独成块", "#EAF2FB", "#3B6EA5"),
    ("⑥ VectorDBIngestor\nDashScope embedding → FAISS", "#E3F1E3", "#5A9E5A"),
    ("databases/\nchunked_reports + vector_dbs(*.faiss)", "#FFF3D6", "#C8901A"),
]
y = 11.2
for text, fc, ec in steps:
    box(ax, 1.8, y - 0.85, 6.4, 1.0, text, fc=fc, ec=ec, fs=9.5)
    if y < 11.2:
        arrow(ax, (5.0, y + 0.18), (5.0, y - 0.02))
    y -= 1.13

# 旁支：BM25
box(ax, 0.2, 1.0, 3.4, 0.9, "BM25Ingestor（可选）\nrank_bm25 索引 *.pkl", fc="#E3F1E3", ec="#5A9E5A", fs=8.5)
arrow(ax, (1.8, 2.7), (1.6, 1.95), color="#999999")
# 旁支：markdown 导出
box(ax, 6.6, 1.0, 3.2, 0.9, "03_reports_markdown/*.md\n人工复核 / 全文模式", fc="#F2F2F2", ec="#888888", fs=8.5)
arrow(ax, (8.2, 3.0), (8.2, 1.95), color="#999999")
ax.text(8.2, 2.45, "Markdown 导出", ha="center", fontsize=8, color="#777777")
plt.tight_layout()
plt.savefig(os.path.join(OUT, "02_离线建库流程图.png"), dpi=160, bbox_inches="tight")
plt.close()

# ============ 图3：在线问答流程图 ============
fig, ax = plt.subplots(figsize=(10, 10.5))
ax.set_xlim(0, 12.4); ax.set_ylim(0, 12); ax.axis("off")
ax.set_title("在线问答流程（process-questions）", fontsize=15, pad=14)

box(ax, 3.9, 10.9, 4.2, 0.9, "questions.json（问题 + kind）", fc="#EEF1F6", ec="#6B7A99")
box(ax, 3.9, 9.6, 4.2, 0.9, "QuestionsProcessor\n从问题中正则匹配公司名", fc="#FBEAE8", ec="#C05A4E")
arrow(ax, (6.0, 10.9), (6.0, 10.5))

# 分支
box(ax, 0.4, 7.9, 3.4, 0.9, "单家公司问题", fc="#FFF3D6", ec="#C8901A")
box(ax, 4.6, 7.9, 4.6, 0.9, "比较题（多家公司）\nLLM 拆解子问题 → 并行处理\n→ LLM 汇总结论", fc="#FFF3D6", ec="#C8901A")
arrow(ax, (4.6, 9.6), (2.1, 8.8))
arrow(ax, (6.0, 9.6), (6.9, 8.8))
# 单公司分支从下方绕行，汇入 get_answer_for_company
arrow(ax, (2.1, 7.9), (2.1, 7.5), color="#999999")
arrow(ax, (2.1, 7.5), (10.1, 7.5), color="#999999")
arrow(ax, (10.1, 7.5), (10.1, 7.9), color="#999999")

box(ax, 8.6, 7.9, 3.0, 0.9, "get_answer_for_company", fc="#FBEAE8", ec="#C05A4E")
arrow(ax, (6.7, 7.9), (9.1, 7.9), color="#777777")

# 检索三选
box(ax, 8.6, 6.4, 3.0, 1.0, "检索方式\nfull_context / 向量 / 混合", fc="#EAF2FB", ec="#3B6EA5", fs=8.5)
arrow(ax, (10.1, 7.9), (10.1, 7.4))
box(ax, 8.0, 4.9, 4.0, 1.0, "VectorRetriever：FAISS top_n\n（父文档检索=返回整页）\nHybridRetriever：+LLMReranker 重排", fc="#EAF2FB", ec="#3B6EA5", fs=8)
arrow(ax, (10.1, 6.4), (10.1, 5.9))

box(ax, 3.9, 4.9, 3.6, 1.0, "拼接 RAG 上下文\n_format_retrieval_results", fc="#EAF2FB", ec="#3B6EA5", fs=8.5)
arrow(ax, (8.0, 5.4), (7.5, 5.4))

box(ax, 3.9, 3.4, 3.6, 1.0, "APIProcessor（dashscope）\n按 kind 选择 SO CoT 提示词\n结构化输出", fc="#F3E8FB", ec="#8A5CB8", fs=8.5)
arrow(ax, (5.7, 4.9), (5.7, 4.4))

box(ax, 3.9, 1.9, 3.6, 1.0, "LLM 回答\nstep_by_step_analysis\nrelevant_pages / final_answer", fc="#F3E8FB", ec="#8A5CB8", fs=8.5)
arrow(ax, (5.7, 3.4), (5.7, 2.9))

box(ax, 0.4, 0.5, 3.8, 1.0, "引用校验\n剔除幻觉页码 + 补齐", fc="#E3F1E3", ec="#5A9E5A", fs=8.5)
arrow(ax, (3.9, 2.0), (2.3, 1.5))
box(ax, 4.9, 0.5, 3.6, 1.0, "answers{suffix}.json\n提交格式（0-based 页码）", fc="#FFF3D6", ec="#C8901A")
arrow(ax, (4.2, 1.0), (4.9, 1.0))
box(ax, 9.0, 0.5, 2.8, 1.0, "answers*_debug.json\n推理过程/用量/错误堆栈", fc="#F2F2F2", ec="#888888", fs=8)
arrow(ax, (8.5, 1.0), (9.0, 1.0))
plt.tight_layout()
plt.savefig(os.path.join(OUT, "03_在线问答流程图.png"), dpi=160, bbox_inches="tight")
plt.close()

print("done:", os.listdir(OUT))
