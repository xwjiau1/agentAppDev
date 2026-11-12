# str与bytes及encode和decode

> 复习优先级：必背。

## 面试速记

str表示Unicode文本，bytes表示字节序列。encode按编码把文本变成字节，decode反向转换；编码必须与数据实际格式一致。

## 面试问答

**问：中文字符串长度就是UTF-8字节数吗？** 不是，len(str)与len(encoded_bytes)衡量不同对象的长度。

**问：Base64是字符编码还是加密？** 它是二进制到文本的编码方式，不提供保密性。

## 实际案例与代码

[GUI视觉动作生成](../../应用侧/多模态与行业应用/GUI视觉动作生成/案例说明.md) · [2-gui-plus使用.py，13–15行](../../应用侧/多模态与行业应用/GUI视觉动作生成/2-gui-plus使用.py#L13-L15)

以下为源码节选，统一去除外层缩进。

```python
with open(image_path, "rb") as image_file:

    return base64.b64encode(image_file.read()).decode('utf-8')
```

rb读取图片bytes，b64encode返回Base64 bytes，再decode为文本以嵌入JSON。这里解码的是Base64文本字节，不是把原图片直接解释为UTF-8。

## 易错点与追问

decode失败可能是选错编码或数据损坏；errors="ignore"会丢失数据。文本文件读写应明确编码，不依赖机器默认值。
