# LangChain4j 递归切片与 PDF 页码

## 实现机制

逐页打开文本型 PDF 的文本流，用 PDFBox `setStartPage`、`setEndPage` 定位同一页，然后把这页提取的文本交给 LangChain4j `DocumentSplitters.recursive(480, 64)`。按页建立 `Document` 可以让每个切片只引用一个物理页。TXT、Markdown 对整篇文本切片，页码为空。[逐页提取源码](../../incubator/hybrid-rag/rag-api/src/main/java/dev/agent/rag/CorpusReader.java#L64-L80) · [LangChain4j RAG 文档](https://docs.langchain4j.dev/tutorials/rag/)

## 代码解析

`split` 为每个切片写入文档 ID、页码、页内序号与正文。点 ID 由相对路径、文件摘要、页码、切片序号和切片策略版本生成。相同文档的相同正文可以在两页形成两个稳定点，重跑时各自覆盖原点。[切片源码](../../incubator/hybrid-rag/rag-api/src/main/java/dev/agent/rag/CorpusReader.java#L89-L101) · [双页重复文本测试](../../incubator/hybrid-rag/rag-api/src/test/java/dev/agent/rag/CorpusReaderTest.java)

## 适用边界

字符预算以 Java `String` 的 UTF-16 单元计量，编码服务另用模型 tokenizer 校验含特殊 token 的长度。物理页从 1 开始，不受封面或印刷页码影响。整份 PDF 提取不到文本时导入失败，混排文档的纯图像页面需由 OCR 扩展处理。[项目入口](../../incubator/hybrid-rag/README.md) · [Python 文档切片策略](Python文档切片策略.md)
