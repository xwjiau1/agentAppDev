# LangChain LCEL串并行组合

## 技术实现

LCEL用Runnable组件组合输入变换、函数和模型调用。串行管道传递上一步结果，RunnableMap把同一输入交给多个分支。

## 应用思路

固定处理顺序用显式管道更易检查；需要模型动态选择工具时再采用Agent。

## 代码解析

### 保留输入并添加分析结果

[LangChain文本工具与LCEL组合](../../应用侧/基础技术示例/LangChain文本工具与LCEL组合/案例说明.md) · [2-simple_toolchain.py，161–170行](../../应用侧/基础技术示例/LangChain文本工具与LCEL组合/2-simple_toolchain.py#L161-L170)

```python
chain = (
    RunnablePassthrough.assign(
        analysis=lambda x: text_analysis_chain.invoke({"text": x["text"]})
    )
    | RunnableLambda(lambda x: {
        "analysis": x["analysis"],
        "line_count": count_lines_chain.invoke({"content": x["text"]})
    })
)
return chain.invoke({"text": text})
```

RunnablePassthrough.assign在原输入上增加analysis，随后RunnableLambda输出分析和行数；原text仍被保留用于第二项。

### 并行工具分支

[LangChain文本工具与LCEL组合](../../应用侧/基础技术示例/LangChain文本工具与LCEL组合/案例说明.md) · [2-simple_toolchain.py，177–181行](../../应用侧/基础技术示例/LangChain文本工具与LCEL组合/2-simple_toolchain.py#L177-L181)

```python
parallel_chain = RunnableMap({
    "analysis": RunnableLambda(lambda x: text_analysis_chain.invoke({"text": x["text"]})),
    "line_count": RunnableLambda(lambda x: count_lines_chain.invoke({"content": x["text"]})),
})
return parallel_chain.invoke({"text": text})
```

两个分支读取同一text，返回字典中不同字段。并行提高独立步骤重叠机会，不保证外部调用无限并发。

### 模型串行与流式接口

[LangChain文本工具与LCEL组合](../../应用侧/基础技术示例/LangChain文本工具与LCEL组合/案例说明.md) · [3-lcel-demo.py，15–25行](../../应用侧/基础技术示例/LangChain文本工具与LCEL组合/3-lcel-demo.py#L15-L25)

```python
translate_to_en = ChatPromptTemplate.from_template("Translate this to English: {input}") | llm | StrOutputParser()
process_text = ChatPromptTemplate.from_template("Analyze this text: {text}") | llm | StrOutputParser()
translate_to_cn = ChatPromptTemplate.from_template("Translate this to Chinese: {output}") | llm | StrOutputParser()

# 组合成多任务链
workflow = {"text": translate_to_en} | process_text | translate_to_cn
#workflow.invoke({"input": "北京有哪些好吃的地方，简略回答不超过200字"})

# 使用stream方法，边生成边打印
for chunk in workflow.stream({"input": "北京有哪些好吃的地方，简略回答不超过200字"}):
    print(chunk, end="", flush=True)
```

Prompt→模型→StrOutputParser构成子链；workflow把翻译结果传给分析与回译。stream迭代输出片段，前置步骤仍需产生下游所需输入。

