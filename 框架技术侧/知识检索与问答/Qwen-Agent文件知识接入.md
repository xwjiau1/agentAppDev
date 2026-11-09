# Qwen-Agent文件知识接入

## 技术实现

Qwen-Agent版枚举docs文件并通过Assistant.files传入框架，应用侧无需显式写出切分和向量检索流水线。

## 应用思路

快速接入文件问答时可以采用框架托管路径；需要更细致控制时，应核对所用版本的内部检索实现，而非从files参数推断。

## 代码解析

### 枚举本地资料

[多框架多文件智能问答](../../应用侧/知识问答与文档处理/多框架多文件智能问答/案例说明.md) · [qwen-agent-multi-files.py，52–63行](../../应用侧/知识问答与文档处理/多框架多文件智能问答/qwen-agent-multi-files.py#L52-L63)

```python
def get_doc_files():
    """获取 docs 文件夹下的所有文件"""
    file_dir = os.path.join('./', 'docs')
    files = []
    if os.path.exists(file_dir):
        # 遍历目录下的所有文件
        for file in os.listdir(file_dir):
            file_path = os.path.join(file_dir, file)
            if os.path.isfile(file_path):  # 确保是文件而不是目录
                files.append(file_path)
    print('加载的文件:', files)
    return files
```

只收集docs顶层文件，不递归子目录；当前工作目录影响相对路径解析。

### 向助手传递文件

[多框架多文件智能问答](../../应用侧/知识问答与文档处理/多框架多文件智能问答/案例说明.md) · [qwen-agent-multi-files.py，73–78行](../../应用侧/知识问答与文档处理/多框架多文件智能问答/qwen-agent-multi-files.py#L73-L78)

```python
bot = Assistant(
    llm=llm_cfg,
    system_message=system_instruction,
    function_list=tools,
    files=files
)
```

files提供知识文件，function_list提供其他工具，两者分工不同。系统提示词描述回答行为，框架管理文件处理。

## 应用方式差异

三份实现保留在同一案例目录，使用相同业务资料；差异在检索控制位置、是否将检索包装为Agent工具，以及框架托管程度。没有为使用方式相同的模型配置重复说明。
