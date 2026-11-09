# Python文档切片策略

## 技术实现

切片策略决定检索单位如何保留语义和结构。固定长度控制大小，滑动窗口保留相邻上下文，层次切片依标题和段落边界控制合并。

## 应用思路

按文档格式选择策略，再用真实检索结果验证；切片大小本身不能保证问答质量。

## 代码解析

### 窗口与步长

[文档切片策略对比](../../应用侧/基础技术示例/文档切片策略对比/案例说明.md) · [5-滑动窗口切片.py，8–18行](../../应用侧/基础技术示例/文档切片策略对比/5-滑动窗口切片.py#L8-L18)

```python
def sliding_window_chunking(text, window_size=512, step_size=256):
    """滑动窗口切片"""
    chunks = []

    for i in range(0, len(text), step_size):
        chunk = text[i:i + window_size]

        if len(chunk.strip()) > 0:
            chunks.append(chunk.strip())

    return chunks
```

窗口决定每段最大长度，overlap决定相邻共享部分；必须保证步长大于0才能推进。

### 标题和长度共同决定边界

[文档切片策略对比](../../应用侧/基础技术示例/文档切片策略对比/案例说明.md) · [4-层次切片.py，47–62行](../../应用侧/基础技术示例/文档切片策略对比/4-层次切片.py#L47-L62)

```python
# 1. 如果遇到更高级别的标题，开始新切片
if preserve_hierarchy and line_level in ['title1', 'title2']:
    should_start_new_chunk = True

# 2. 如果当前切片长度超过目标大小
if len(current_chunk) + len(line) > target_size and current_chunk.strip():
    should_start_new_chunk = True

# 3. 如果遇到段落分隔符且当前切片已经足够长
if line_level == 'paragraph' and len(current_chunk) > target_size * 0.8:
    should_start_new_chunk = True

# 开始新切片
if should_start_new_chunk and current_chunk.strip():
    chunks.append(current_chunk.strip())
    current_chunk = ""
```

preserve_hierarchy让高级标题开始新片段，target_size限制合并长度；段落达到80%目标大小时也允许切开。

### 语义模型切分

[文档切片策略对比](../../应用侧/基础技术示例/文档切片策略对比/案例说明.md) · [3-LLM语义切片.py，6–23行](../../应用侧/基础技术示例/文档切片策略对比/3-LLM语义切片.py#L6-L23)

```python
def advanced_semantic_chunking_with_llm(text, max_chunk_size=512):
    """使用LLM进行语义切片"""
    # 检查环境变量
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("警告: 未设置 DASHSCOPE_API_KEY 环境变量，将使用基础语义切片")
        return fallback_semantic_chunking(text, max_chunk_size)

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    prompt = f"""
请将以下文本按照语义完整性进行切片，每个切片不超过{max_chunk_size}字符。
要求：
1. 保持语义完整性
2. 在自然的分割点切分
```

模型通过提示词按语义划分段落，后续解析JSON。该策略有额外模型成本，结构合法与语义完整需要分别核对。

