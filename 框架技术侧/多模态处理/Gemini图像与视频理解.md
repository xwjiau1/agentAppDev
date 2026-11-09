# Gemini图像与视频理解

## 技术实现

Google GenAI通过contents接受文本、Pillow图像对象或上传文件对象。视频上传和处理完成是两个阶段，需轮询后推理。

## 应用思路

适合图像解释、视频摘要和关键信息提取；上传状态失败应中止，避免将未处理媒体传入推理。

## 代码解析

### 图像与文本组合

[Gemini图像与视频理解](../../应用侧/多模态与行业应用/Gemini图像与视频理解/案例说明.md) · [1-Gemini多模态处理.py，24–30行](../../应用侧/多模态与行业应用/Gemini图像与视频理解/1-Gemini多模态处理.py#L24-L30)

```python
image = Image.open("dog_and_girl.jpeg")

# 注意：contents 变成了一个列表，里面同时放了图片对象和文字
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[image, "帮我解释下这张照片"]
)
```

contents列表混合图像对象和指令；model指定已有脚本的模型名称，响应文本从response.text读取。

### 上传与处理状态

[Gemini图像与视频理解](../../应用侧/多模态与行业应用/Gemini图像与视频理解/案例说明.md) · [1-Gemini多模态处理.py，43–54行](../../应用侧/多模态与行业应用/Gemini图像与视频理解/1-Gemini多模态处理.py#L43-L54)

```python
video_file = client.files.upload(file="car.mp4") # 汽车剐蹭视频
print(f"上传成功: {video_file.name}")

# 2. 等待视频处理 (关键步骤！)
# 视频上传后，Google 需要几秒钟在云端进行转码。
while video_file.state.name == "PROCESSING":
    print("视频处理中，请稍候...")
    time.sleep(2)
    video_file = client.files.get(name=video_file.name)

if video_file.state.name == "FAILED":
    raise ValueError("视频处理失败")
```

upload返回文件对象；PROCESSING时使用files.get刷新状态；FAILED显式报错，随后才能用文件对象请求视频理解。

