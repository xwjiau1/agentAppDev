# Agent应用与框架代码库

收录可参考的应用项目、基础技术与模型服务示例。按应用场景寻找实现，按框架技术阅读机制、参数和实际代码。完整源码保留项目内部结构；案例说明记录依赖、数据与运行限制。

## Python基础面试索引

[进入Python基础侧：分类速查与复习顺序](Python基础侧/README.md)。每个知识点单独归档，含速记、面试问答、真实案例代码及易错追问；与应用侧、框架技术侧并列。

## 应用索引

| 分类 | 案例 | 用途 | 技术栈 |
|---|---|---|---|
| 自动化与工具助手 | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) | 工具、权限、记忆、任务、协作与恢复运行时 | Python、Anthropic SDK、标准库 |
| 基础技术示例 | [OpenEvals评估与自动化测试](应用侧/基础技术示例/OpenEvals评估与自动化测试/案例说明.md) | 单项裁判与批量评估 | OpenEvals、LangSmith |
| 金融投研与投顾 | [Qwen投顾助手与Langfuse追踪](应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/案例说明.md) | 投顾对话与查询追踪 | Qwen-Agent、Langfuse |
| 金融投研与投顾 | [投顾AI助手效果评估](应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) | 双路径投顾与规则、模型评分 | LangGraph、LangSmith、DeepEval |
| 知识问答与文档处理 | [PDF问答与页码溯源](应用侧/知识问答与文档处理/PDF问答与页码溯源/案例说明.md) | 提取PDF文本并检索相关片段生成回答。 | PyPDF2、LangChain、FAISS、DashScope |
| 基础技术示例 | [Embedding与FAISS元数据检索](应用侧/基础技术示例/Embedding与FAISS元数据检索/案例说明.md) | 生成文本向量并将搜索结果映射回业务元数据。 | OpenAI兼容SDK、NumPy、FAISS |
| 搜索与推荐 | [酒店文本相似推荐](应用侧/搜索与推荐/酒店文本相似推荐/案例说明.md) | 根据酒店描述查找相似酒店。 | pandas、scikit-learn、Matplotlib |
| 模型与服务示例 | [Word2Vec词向量训练](应用侧/模型与服务示例/Word2Vec词向量训练/案例说明.md) | 训练中文词向量并计算词相似度。 | Gensim、jieba、NumPy |
| 知识问答与文档处理 | [PDF问答与直接提示词生成](应用侧/知识问答与文档处理/PDF问答与直接提示词生成/案例说明.md) | 检索PDF片段并通过直接提示词调用生成回答。 | PyPDF2、LangChain Text Splitters、FAISS、Tongyi |
| 模型与服务示例 | [BGE与GTE文本向量推理](应用侧/模型与服务示例/BGE与GTE文本向量推理/案例说明.md) | 比较本地Embedding模型的向量生成与相似度计算。 | FlagEmbedding、SentenceTransformers、PyTorch、ModelScope |
| 搜索与研究助手 | [查询改写与搜索策略](应用侧/搜索与研究助手/查询改写与搜索策略/案例说明.md) | 将上下文依赖问题补全，并识别联网检索需求。 | DashScope、Python JSON |
| 多模态与行业应用 | [Gemini图像与视频理解](应用侧/多模态与行业应用/Gemini图像与视频理解/案例说明.md) | 通过统一内容生成接口理解文本、图片和视频。 | Google GenAI、Pillow |
| 基础技术示例 | [文档切片策略对比](应用侧/基础技术示例/文档切片策略对比/案例说明.md) | 比较固定长度、句子、语义、层次、窗口和自适应切片。 | Python、OpenAI兼容SDK |
| 知识问答与文档处理 | [主题乐园多模态知识问答](应用侧/知识问答与文档处理/主题乐园多模态知识问答/案例说明.md) | 统一检索文档、海报和视频，并附加相关媒体。 | DashScope多模态Embedding、FAISS、python-docx、OpenAI兼容SDK |
| 模型与服务示例 | [BGE交叉编码重排](应用侧/模型与服务示例/BGE交叉编码重排/案例说明.md) | 对查询和候选文档联合编码生成相关性分数。 | Transformers、PyTorch、ModelScope、SentenceTransformers |
| 知识问答与文档处理 | [多查询混合检索与重排问答](应用侧/知识问答与文档处理/多查询混合检索与重排问答/案例说明.md) | 组合查询扩展、词项检索、向量检索和候选重排。 | FAISS、BM25、jieba、LangChain、Tongyi、BGE |
| 知识问答与文档处理 | [知识库维护与检索评估](应用侧/知识问答与文档处理/知识库维护与检索评估/案例说明.md) | 生成检索问题、沉淀对话知识并检查知识库质量。 | DashScope、OpenAI兼容SDK、BM25、FAISS、pandas |
| 知识问答与文档处理 | [企业报告知识库基础流水线](应用侧/知识问答与文档处理/企业报告知识库基础流水线/案例说明.md) | 解析企业报告并执行带来源的检索问答。 | Docling、FAISS、BM25、Pydantic、OpenAI兼容SDK |
| 知识问答与文档处理 | [企业报告知识库交互版](应用侧/知识问答与文档处理/企业报告知识库交互版/案例说明.md) | 解析企业报告并执行带来源的检索问答。 | Docling、FAISS、BM25、Pydantic、OpenAI兼容SDK、Streamlit |
| 知识问答与文档处理 | [企业报告问答与回归评估](应用侧/知识问答与文档处理/企业报告问答与回归评估/案例说明.md) | 处理企业报告，按公司检索并生成带引用的答案。 | Docling、FAISS、BM25、Pydantic、Click、DashScope |
| 知识问答与文档处理 | [企业报告交互问答增强版](应用侧/知识问答与文档处理/企业报告交互问答增强版/案例说明.md) | 处理企业报告，按公司检索并生成带引用的答案。 | Docling、FAISS、BM25、Pydantic、Click、DashScope、Streamlit |
| 数据分析与ChatBI | [门票订单查询与图表助手](应用侧/数据分析与ChatBI/门票订单查询与图表助手/案例说明.md) | 将自然语言问题转为订单SQL查询，并展示表格或图表。 | Qwen-Agent、DashScope、SQLAlchemy、pandas、Matplotlib |
| 自动化与工具助手 | [MCP地图搜索与文件助手](应用侧/自动化与工具助手/MCP地图搜索与文件助手/案例说明.md) | 以MCP服务接入地图、联网搜索和本地文本文件工具。 | Qwen-Agent、FastMCP、Node.js MCP服务 |
| 金融投研与投顾 | [工具循环与混合式投顾](应用侧/金融投研与投顾/工具循环与混合式投顾/案例说明.md) | 根据查询选择工具循环或多阶段投资分析。 | LangGraph、LangChain、ChatTongyi |
| 金融投研与投顾 | [多阶段智能投研助手](应用侧/金融投研与投顾/多阶段智能投研助手/案例说明.md) | 通过感知、建模、推理、决策和报告形成分析结果。 | LangGraph、Pydantic、Qwen-Agent、DashScope |
| 金融投研与投顾 | [基金规则工具问答](应用侧/金融投研与投顾/基金规则工具问答/案例说明.md) | 从内存规则样例中按关键词或类别搜索并回答。 | LangChain create_agent、ChatTongyi |
| 模型与服务示例 | [二手车价格预测与模型融合](应用侧/模型与服务示例/二手车价格预测与模型融合/案例说明.md) | 对结构化车辆数据进行价格回归与多模型融合。 | pandas、scikit-learn、CatBoost、LightGBM、XGBoost |
| 搜索与研究助手 | [Qwen搜索与文档助手](应用侧/搜索与研究助手/Qwen搜索与文档助手/案例说明.md) | 组合本地文档检索、联网搜索和多轮问答。 | Qwen-Agent、DashScope、Elasticsearch、Tavily MCP、Gradio |
| 搜索与研究助手 | [保险知识检索与搜索集成](应用侧/搜索与研究助手/保险知识检索与搜索集成/案例说明.md) | 组合本地文档检索、联网搜索和多轮问答。 | Qwen-Agent、DashScope、Elasticsearch、Tavily MCP、Gradio |
| 搜索与研究助手 | [Elasticsearch保险问答与会话界面](应用侧/搜索与研究助手/Elasticsearch保险问答与会话界面/案例说明.md) | 组合本地文档检索、联网搜索和多轮问答。 | Qwen-Agent、DashScope、Elasticsearch、Tavily MCP、Gradio |
| 基础技术示例 | [Elasticsearch保险全文检索](应用侧/基础技术示例/Elasticsearch保险全文检索/案例说明.md) | 独立演示保险文档索引与检索。 | Elasticsearch、Python |
| 基础技术示例 | [Daytona沙箱执行](应用侧/基础技术示例/Daytona沙箱执行/案例说明.md) | 创建远程沙箱并执行一段Python代码。 | Daytona SDK |
| 多模态与行业应用 | [GUI视觉动作生成](应用侧/多模态与行业应用/GUI视觉动作生成/案例说明.md) | 把截图和目标转换为结构化GUI操作描述。 | OpenAI兼容SDK、DashScope GUI模型 |
| 自动化与工具助手 | [OpenManus通用任务助手](应用侧/自动化与工具助手/OpenManus通用任务助手/案例说明.md) | 组织模型、浏览器、代码执行和MCP工具完成多步任务。 | OpenManus、Pydantic、FastAPI、MCP、浏览器工具 |
| 自动化与工具助手 | [OpenManus浏览器与视觉操作](应用侧/自动化与工具助手/OpenManus浏览器与视觉操作/案例说明.md) | 组织模型、浏览器、代码执行和MCP工具完成多步任务。 | OpenManus、Pydantic、FastAPI、MCP、浏览器工具 |
| 自动化与工具助手 | [OpenManus文档检索扩展](应用侧/自动化与工具助手/OpenManus文档检索扩展/案例说明.md) | 组织模型、浏览器、代码执行和MCP工具完成多步任务。 | OpenManus、Pydantic、FastAPI、MCP、浏览器工具 |
| 自动化与工具助手 | [LangGraph规划执行与人工审查](应用侧/自动化与工具助手/LangGraph规划执行与人工审查/案例说明.md) | 以规划、执行和审查循环组织任务。 | LangGraph、ChatOpenAI、MemorySaver |
| 基础技术示例 | [LangChain模型工具与会话基础](应用侧/基础技术示例/LangChain模型工具与会话基础/案例说明.md) | 展示提示词管道、搜索计算工具和带历史的对话。 | LangChain、Tongyi、SerpAPI |
| 基础技术示例 | [LangChain文本工具与LCEL组合](应用侧/基础技术示例/LangChain文本工具与LCEL组合/案例说明.md) | 组合文本分析、格式转换及行数统计等工具。 | LangChain Runnables、Tongyi |
| 自动化与工具助手 | [网络故障诊断Agent](应用侧/自动化与工具助手/网络故障诊断Agent/案例说明.md) | 通过网络诊断工具组合解释用户报告的故障。 | LangChain create_agent、ChatTongyi |
| 知识问答与文档处理 | [多框架多文件智能问答](应用侧/知识问答与文档处理/多框架多文件智能问答/案例说明.md) | 对同一文档目录提供LangChain、LlamaIndex与Qwen-Agent问答实现。 | LangChain、LlamaIndex、Qwen-Agent、DashScope、FAISS |

## 框架技术索引

| 分类 | 技术文档 | 关联应用 |
|---|---|---|
| 效果评估 | [DeepEval效果评估](框架技术侧/效果评估/DeepEval效果评估.md) | [投顾AI助手效果评估](应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) |
| 效果评估 | [LangSmith效果评估](框架技术侧/效果评估/LangSmith效果评估.md) | [投顾AI助手效果评估](应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) |
| 效果评估 | [OpenEvals RAG评估](框架技术侧/效果评估/OpenEvals%20RAG评估.md) | [OpenEvals评估与自动化测试](应用侧/基础技术示例/OpenEvals评估与自动化测试/案例说明.md) |
| 效果评估 | [OpenEvals效果评估](框架技术侧/效果评估/OpenEvals效果评估.md) | [OpenEvals评估与自动化测试](应用侧/基础技术示例/OpenEvals评估与自动化测试/案例说明.md) |
| 流程编排与工具调用 | [LangGraph流程编排](框架技术侧/流程编排与工具调用/LangGraph流程编排.md) | [投顾AI助手效果评估](应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) |
| 流程编排与工具调用 | [Qwen-Agent工具调用与提示词编排](框架技术侧/流程编排与工具调用/Qwen-Agent工具调用与提示词编排.md) | [Qwen投顾助手与Langfuse追踪](应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/案例说明.md) |
| 调用追踪 | [Langfuse调用追踪](框架技术侧/调用追踪/Langfuse调用追踪.md) | [Qwen投顾助手与Langfuse追踪](应用侧/金融投研与投顾/Qwen投顾助手与Langfuse追踪/案例说明.md) |
| 调用追踪 | [LangSmith调用追踪](框架技术侧/调用追踪/LangSmith调用追踪.md) | [投顾AI助手效果评估](应用侧/金融投研与投顾/投顾AI助手效果评估/案例说明.md) |
| 向量化与检索 | [FAISS向量与元数据检索](框架技术侧/向量化与检索/FAISS向量与元数据检索.md) | [Embedding与FAISS元数据检索](应用侧/基础技术示例/Embedding与FAISS元数据检索/案例说明.md) |
| 知识检索与问答 | [LangChain PDF问答](框架技术侧/知识检索与问答/LangChain%20PDF问答.md) | [PDF问答与页码溯源](应用侧/知识问答与文档处理/PDF问答与页码溯源/案例说明.md) |
| 向量化与检索 | [Gensim Word2Vec训练](框架技术侧/向量化与检索/Gensim%20Word2Vec训练.md) | [Word2Vec词向量训练](应用侧/模型与服务示例/Word2Vec词向量训练/案例说明.md) |
| 向量化与检索 | [Scikit-learn TF-IDF推荐](框架技术侧/向量化与检索/Scikit-learn%20TF-IDF推荐.md) | [酒店文本相似推荐](应用侧/搜索与推荐/酒店文本相似推荐/案例说明.md) |
| 向量化与检索 | [BGE与GTE向量推理](框架技术侧/向量化与检索/BGE与GTE向量推理.md) | [BGE与GTE文本向量推理](应用侧/模型与服务示例/BGE与GTE文本向量推理/案例说明.md) |
| 查询改写与搜索 | [DashScope查询改写](框架技术侧/查询改写与搜索/DashScope查询改写.md) | [查询改写与搜索策略](应用侧/搜索与研究助手/查询改写与搜索策略/案例说明.md) |
| 知识检索与问答 | [Tongyi检索上下文生成](框架技术侧/知识检索与问答/Tongyi检索上下文生成.md) | [PDF问答与直接提示词生成](应用侧/知识问答与文档处理/PDF问答与直接提示词生成/案例说明.md) |
| 多模态处理 | [Gemini图像与视频理解](框架技术侧/多模态处理/Gemini图像与视频理解.md) | [Gemini图像与视频理解](应用侧/多模态与行业应用/Gemini图像与视频理解/案例说明.md) |
| 文档解析与切片 | [Python文档切片策略](框架技术侧/文档解析与切片/Python文档切片策略.md) | [文档切片策略对比](应用侧/基础技术示例/文档切片策略对比/案例说明.md) |
| 多模态处理 | [DashScope多模态检索](框架技术侧/多模态处理/DashScope多模态检索.md) | [主题乐园多模态知识问答](应用侧/知识问答与文档处理/主题乐园多模态知识问答/案例说明.md) |
| 向量化与检索 | [BM25与FAISS混合召回](框架技术侧/向量化与检索/BM25与FAISS混合召回.md) | [多查询混合检索与重排问答](应用侧/知识问答与文档处理/多查询混合检索与重排问答/案例说明.md) |
| 向量化与检索 | [BGE重排与多查询召回](框架技术侧/向量化与检索/BGE重排与多查询召回.md) | [BGE交叉编码重排](应用侧/模型与服务示例/BGE交叉编码重排/案例说明.md)、[多查询混合检索与重排问答](应用侧/知识问答与文档处理/多查询混合检索与重排问答/案例说明.md) |
| 知识库维护 | [DashScope知识抽取与健康检查](框架技术侧/知识库维护/DashScope知识抽取与健康检查.md) | [知识库维护与检索评估](应用侧/知识问答与文档处理/知识库维护与检索评估/案例说明.md) |
| 知识检索与问答 | [Docling企业报告流水线](框架技术侧/知识检索与问答/Docling企业报告流水线.md) | [企业报告知识库基础流水线](应用侧/知识问答与文档处理/企业报告知识库基础流水线/案例说明.md) |
| 知识检索与问答 | [Streamlit企业知识库交互](框架技术侧/知识检索与问答/Streamlit企业知识库交互.md) | [企业报告知识库交互版](应用侧/知识问答与文档处理/企业报告知识库交互版/案例说明.md) |
| 知识检索与问答 | [企业报告父页召回与LLM重排](框架技术侧/知识检索与问答/企业报告父页召回与LLM重排.md) | [企业报告问答与回归评估](应用侧/知识问答与文档处理/企业报告问答与回归评估/案例说明.md) |
| 知识检索与问答 | [Streamlit单问题检索界面](框架技术侧/知识检索与问答/Streamlit单问题检索界面.md) | [企业报告交互问答增强版](应用侧/知识问答与文档处理/企业报告交互问答增强版/案例说明.md) |
| 流程编排与工具调用 | [Qwen-Agent SQL工具调用](框架技术侧/流程编排与工具调用/Qwen-Agent%20SQL工具调用.md) | [门票订单查询与图表助手](应用侧/数据分析与ChatBI/门票订单查询与图表助手/案例说明.md) |
| 流程编排与工具调用 | [Qwen-Agent MCP服务接入](框架技术侧/流程编排与工具调用/Qwen-Agent%20MCP服务接入.md) | [MCP地图搜索与文件助手](应用侧/自动化与工具助手/MCP地图搜索与文件助手/案例说明.md) |
| 流程编排与工具调用 | [LangGraph工具循环与失败重试](框架技术侧/流程编排与工具调用/LangGraph工具循环与失败重试.md) | [工具循环与混合式投顾](应用侧/金融投研与投顾/工具循环与混合式投顾/案例说明.md)、[多阶段智能投研助手](应用侧/金融投研与投顾/多阶段智能投研助手/案例说明.md) |
| 流程编排与工具调用 | [LangChain规则查询Agent](框架技术侧/流程编排与工具调用/LangChain规则查询Agent.md) | [基金规则工具问答](应用侧/金融投研与投顾/基金规则工具问答/案例说明.md) |
| 模型训练与预测 | [XGBoost回归与模型融合](框架技术侧/模型训练与预测/XGBoost回归与模型融合.md) | [二手车价格预测与模型融合](应用侧/模型与服务示例/二手车价格预测与模型融合/案例说明.md) |
| 知识检索与问答 | [Elasticsearch检索工具与联网补充](框架技术侧/知识检索与问答/Elasticsearch检索工具与联网补充.md) | [Elasticsearch保险问答与会话界面](应用侧/搜索与研究助手/Elasticsearch保险问答与会话界面/案例说明.md) |
| 流程编排与工具调用 | [OpenManus工具执行循环](框架技术侧/流程编排与工具调用/OpenManus工具执行循环.md) | [OpenManus通用任务助手](应用侧/自动化与工具助手/OpenManus通用任务助手/案例说明.md) |
| 平台与模型服务接入 | [Daytona沙箱与GUI动作模型](框架技术侧/平台与模型服务接入/Daytona沙箱与GUI动作模型.md) | [Daytona沙箱执行](应用侧/基础技术示例/Daytona沙箱执行/案例说明.md)、[GUI视觉动作生成](应用侧/多模态与行业应用/GUI视觉动作生成/案例说明.md) |
| 流程编排与工具调用 | [LangGraph规划执行与人工审查](框架技术侧/流程编排与工具调用/LangGraph规划执行与人工审查.md) | [LangGraph规划执行与人工审查](应用侧/自动化与工具助手/LangGraph规划执行与人工审查/案例说明.md) |
| 状态与记忆 | [LangChain会话历史管理](框架技术侧/状态与记忆/LangChain会话历史管理.md) | [LangChain模型工具与会话基础](应用侧/基础技术示例/LangChain模型工具与会话基础/案例说明.md) |
| 流程编排与工具调用 | [LangChain LCEL串并行组合](框架技术侧/流程编排与工具调用/LangChain%20LCEL串并行组合.md) | [LangChain文本工具与LCEL组合](应用侧/基础技术示例/LangChain文本工具与LCEL组合/案例说明.md) |
| 流程编排与工具调用 | [LangChain诊断工具调度](框架技术侧/流程编排与工具调用/LangChain诊断工具调度.md) | [网络故障诊断Agent](应用侧/自动化与工具助手/网络故障诊断Agent/案例说明.md) |
| 知识检索与问答 | [LangChain多文件问答](框架技术侧/知识检索与问答/LangChain多文件问答.md) | [多框架多文件智能问答](应用侧/知识问答与文档处理/多框架多文件智能问答/案例说明.md) |
| 知识检索与问答 | [LlamaIndex检索工具Agent](框架技术侧/知识检索与问答/LlamaIndex检索工具Agent.md) | [多框架多文件智能问答](应用侧/知识问答与文档处理/多框架多文件智能问答/案例说明.md) |
| 知识检索与问答 | [Qwen-Agent文件知识接入](框架技术侧/知识检索与问答/Qwen-Agent文件知识接入.md) | [多框架多文件智能问答](应用侧/知识问答与文档处理/多框架多文件智能问答/案例说明.md) |
| Agent运行时 | [Agent Harness模型与工具循环](框架技术侧/Agent运行时/Agent%20Harness模型与工具循环.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| Agent运行时 | [Harness工具分派与工作区路径约束](框架技术侧/Agent运行时/Harness工具分派与工作区路径约束.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| 权限与扩展 | [Harness工具权限判定](框架技术侧/权限与扩展/Harness工具权限判定.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| 权限与扩展 | [Harness事件钩子与短路处理](框架技术侧/权限与扩展/Harness事件钩子与短路处理.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| 状态与记忆 | [Harness Todo状态校验](框架技术侧/状态与记忆/Harness%20Todo状态校验.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| Agent运行时 | [Harness子代理上下文隔离](框架技术侧/Agent运行时/Harness子代理上下文隔离.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| 权限与扩展 | [Harness技能目录与按需加载](框架技术侧/权限与扩展/Harness技能目录与按需加载.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| 状态与记忆 | [Harness上下文压缩与调用结果配对](框架技术侧/状态与记忆/Harness上下文压缩与调用结果配对.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| 状态与记忆 | [Harness文件记忆的筛选与召回](框架技术侧/状态与记忆/Harness文件记忆的筛选与召回.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| 任务与协作 | [Harness持久任务与依赖状态](框架技术侧/任务与协作/Harness持久任务与依赖状态.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| 任务与协作 | [Harness后台任务与结果回收](框架技术侧/任务与协作/Harness后台任务与结果回收.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| 任务与协作 | [Harness定时任务队列与投递确认](框架技术侧/任务与协作/Harness定时任务队列与投递确认.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| 任务与协作 | [Harness团队邮箱与任务分配](框架技术侧/任务与协作/Harness团队邮箱与任务分配.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| 任务与协作 | [Harness任务绑定Git Worktree隔离](框架技术侧/任务与协作/Harness任务绑定Git%20Worktree隔离.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| 权限与扩展 | [Harness MCP式插件命名与分派](框架技术侧/权限与扩展/Harness%20MCP式插件命名与分派.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| Agent运行时 | [集成Harness的模块复用与入口协调](框架技术侧/Agent运行时/集成Harness的模块复用与入口协调.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| Agent运行时 | [Harness工作流日志缓存与恢复](框架技术侧/Agent运行时/Harness工作流日志缓存与恢复.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |
| Agent运行时 | [Harness目标评估与停止控制](框架技术侧/Agent运行时/Harness目标评估与停止控制.md) | [通用Agent Harness](应用侧/自动化与工具助手/通用AgentHarness/案例说明.md) |


## 使用说明

- 优先阅读案例说明，再按入口配置依赖、凭据和数据；代码片段是源码摘录，不是独立运行程序。
- 历史SDK和框架接口未统一迁移，静态检查通过不代表外部服务调用已经验证。
- 模型权重、大型原始数据和运行缓存不入库，相关条件在案例中说明；不携带现有账号的访问凭据。
- 第三方项目的许可证和作者信息随源码保留。本仓库不为第三方代码重新授予许可证。
