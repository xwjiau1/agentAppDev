# Daytona沙箱与GUI动作模型

## 技术实现

沙箱服务负责隔离执行代码，GUI模型负责从截图生成操作描述。二者分别属于执行环境与视觉决策，不能将模型返回动作等同于已经操作成功。

## 应用思路

需要远程计算时使用沙箱；需要视觉定位时先取得截图，再解释模型动作，并在执行后验证界面状态。当前仅整理已有请求示例。

## 代码解析

### 创建并调用沙箱

[Daytona沙箱执行](../../应用侧/基础技术示例/Daytona沙箱执行/案例说明.md) · [1-daytona.py，11–18行](../../应用侧/基础技术示例/Daytona沙箱执行/1-daytona.py#L11-L18)

```python
sandbox = daytona.create()

# 在沙箱中安全地运行代码
response = sandbox.process.code_run('print("Hello World from code!")')
if response.exit_code != 0:
  print(f"错误: {response.exit_code} {response.result}")
else:
    print(response.result)
```

code_run返回exit_code与result。创建远程实例可能产生资源消耗；现有片段未清理，需要在实际集成中补全生命周期。

### 请求视觉动作

[GUI视觉动作生成](../../应用侧/多模态与行业应用/GUI视觉动作生成/案例说明.md) · [2-gui-plus使用.py，61–65行](../../应用侧/多模态与行业应用/GUI视觉动作生成/2-gui-plus使用.py#L61-L65)

```python
completion = client.chat.completions.create(

    model="gui-plus", 

    messages=messages
```

model选择gui-plus，messages混合截图与文本，最终仅打印响应内容。动作执行和结果确认不在这份代码中。

