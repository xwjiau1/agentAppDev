# ai_bot-5.py
import os
import asyncio
from typing import Optional
from qwen_agent.agents import Assistant
import warnings
import gradio as gr
import time

warnings.filterwarnings("ignore")

def init_agent_service():
    """初始化具备 Elasticsearch RAG 和网络搜索能力的助手服务"""
    
    # 步骤 1: LLM 配置
    llm_cfg = {
        'model': 'qwen-max',
        'model_server': 'dashscope',
        'api_key': os.getenv('DASHSCOPE_API_KEY'),
        'generate_cfg': {
            'top_p': 0.8
        }
    }

    # 步骤 2: RAG 配置 - 激活并配置 Elasticsearch 后端
    rag_cfg = {
        "rag_backend": "elasticsearch",
        "es": {
            "host": "https://localhost",
            "port": 9200,
            "user": "elastic",
            "password": "YOUR_CREDENTIAL",
            "index_name": "my_insurance_docs_index"
        },
        "parser_page_size": 500
    }

    # 步骤 3: 系统指令和工具
    system_instruction = '''你是一个AI助手。
请根据用户的问题，优先利用检索工具从本地知识库中查找最相关的信息。
如果本地知识库没有相关信息，再使用 tavily_search 工具从互联网上搜索，并结合这些信息给出专业、准确的回答。'''

    # MCP 工具配置 - 新增 tavily-mcp
    tools_cfg = [{
        "mcpServers": {
            "tavily-mcp": {
                "command": "npx",
                "args": ["-y", "tavily-mcp@0.1.4"],
                "env": {
                    "TAVILY_API_KEY": os.getenv('TAVILY_API_KEY', "YOUR_CREDENTIAL")
                },
                "disabled": False,
                "autoApprove": []
            }
        }
    }]

    # 获取文件夹下所有文件
    file_dir = os.path.join(os.path.dirname(__file__), 'docs')
    files = []
    if os.path.exists(file_dir):
        for file in os.listdir(file_dir):
            file_path = os.path.join(file_dir, file)
            if os.path.isfile(file_path):
                files.append(file_path)
    print('知识库文件列表:', files)

    # 步骤 4: 创建智能体实例
    bot = Assistant(
        llm=llm_cfg,
        system_message=system_instruction,
        function_list=tools_cfg,
        files=files,
        rag_cfg=rag_cfg
    )
    return bot

# 全局变量
bot = init_agent_service()
# 使用 session_id 来区分不同用户的对话历史
session_histories = {}

def get_session_id():
    # 简单地使用时间戳作为 session_id
    # 在实际应用中可能需要更健壮的 session 管理机制
    return str(time.time())

def predict(query, history, session_id):
    """Gradio 的核心预测函数"""
    if session_id not in session_histories:
        session_histories[session_id] = []
    
    messages = session_histories[session_id]
    messages.append({'role': 'user', 'content': query})
    
    response_text = ""
    for response in bot.run(messages=messages):
        if response and response[-1]['role'] == 'assistant':
            response_text = response[-1]['content']
            
    messages.append({'role': 'assistant', 'content': response_text})
    session_histories[session_id] = messages
    
    history[-1][1] = response_text
    return history

def main():
    """启动自定义的 Gradio Web 图形界面"""
    
    custom_css = """
    body { font-family: 'Arial', sans-serif; background-color: #F7F8FA; }
    .gradio-container { max-width: 100% !important; background-color: #F7F8FA;}
    #sidebar { background-color: #FFFFFF; padding: 20px; border-right: 1px solid #E5E7EB; min-height: 100vh; }
    #logo { display: flex; align-items: center; margin-bottom: 30px; }
    #logo-img { width: 40px; height: 40px; margin-right: 10px; border-radius: 50%; }
    #logo-text { font-size: 24px; font-weight: bold; color: #333; }
    .sidebar-btn { 
        display: block; width: 100%; text-align: left; padding: 12px 15px; 
        border: none; background: none; font-size: 16px; margin-bottom: 10px;
        cursor: pointer; border-radius: 8px; color: #374151;
    }
    .sidebar-btn.active, .sidebar-btn:hover { background-color: #F3F4F6; }
    #main-chat { padding: 20px; background-color: #F7F8FA; }
    #chat-header { text-align: center; margin-top: 8%; margin-bottom: 40px; }
    #chat-header-title { font-size: 48px; font-weight: 500; color: #333; letter-spacing: 2px; background: -webkit-linear-gradient(45deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    #chat-header-subtitle { font-size: 16px; color: #6B7280; margin-top: 10px;}
    #chatbot { box-shadow: none; border: none; background-color: transparent; }
    .message-bubble-user { background: #DBEAFE !important; color: #1E40AF !important; }
    .message-bubble-bot { background: #FFFFFF !important; color: #374151 !important; }
    .suggestion-row { margin-top: 20px; display: flex; justify-content: center; flex-wrap: wrap; gap: 10px;}
    .suggestion-btn { 
        background-color: #FFFFFF; border: 1px solid #E5E7EB; padding: 8px 16px;
        border-radius: 18px; cursor: pointer; color: #374151; font-size: 14px;
        transition: all 0.2s ease-in-out;
    }
    .suggestion-btn:hover { background-color: #F9FAFB; border-color: #D1D5DB; transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    #input-container { border: 1px solid #D1D5DB; border-radius: 24px; background-color: #fff; padding: 5px 5px 5px 20px; display:flex; align-items:center;}
    """
    
    with gr.Blocks(css=custom_css, theme=gr.themes.Soft(primary_hue="blue", secondary_hue="purple")) as demo:
        session_id = gr.State(get_session_id)
        
        with gr.Row():
            with gr.Column(scale=2, elem_id="sidebar"):
                with gr.Row(elem_id="logo"):
                    gr.HTML('<img id="logo-img" src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT6-E2TfIn_2E-O9j7A_T3dD_Rj-QDYJz-7_A&s" alt="logo">')
                    gr.HTML('<h1 id="logo-text">知乎直答</h1>')
                
                gr.Button("🔍  搜索", elem_classes=["sidebar-btn", "active"])
                gr.Button("📚  知识库", elem_classes="sidebar-btn")
                gr.Button("⭐  收藏", elem_classes="sidebar-btn")
                gr.Button("🕒  历史", elem_classes="sidebar-btn")
            
            with gr.Column(scale=8, elem_id="main-chat"):
                with gr.Row(elem_id="chat-header"):
                    gr.HTML('<h1 id="chat-header-title">用提问发现世界</h1><p id="chat-header-subtitle">输入你的问题，或使用「@快捷引用」对知乎答主、知识库进行提问</p>')

                chatbot = gr.Chatbot(elem_id="chatbot", bubble_full_width=False, height=550)
                
                with gr.Row(elem_id="suggestion-row") as suggestion_row:
                    suggestions = ['介绍下雇主责任险', '雇主责任险和工伤保险有什么主要区别？', '最近有什么新的保险产品推荐吗？']
                    suggestion_btns = []
                    for s in suggestions:
                        btn = gr.Button(s, elem_classes="suggestion-btn")
                        suggestion_btns.append(btn)
                
                with gr.Row(elem_id="input-container-wrapper"):
                    with gr.Row(elem_id="input-container"):
                        textbox = gr.Textbox(container=False, show_label=False, placeholder="输入你的问题...", scale=10)
                        submit_btn = gr.Button("↑", scale=1, min_width=0, variant="primary")
        
        def on_submit(query, history):
            history.append([query, None])
            return "", history

        def on_suggestion_click(suggestion, history):
            history.append([suggestion, None])
            return "", history, gr.update(visible=False)

        submit_event = textbox.submit(on_submit, [textbox, chatbot], [textbox, chatbot], queue=False)
        submit_event.then(lambda: gr.update(visible=False), None, suggestion_row)
        submit_event.then(predict, [textbox, chatbot, session_id], chatbot)

        click_event = submit_btn.click(on_submit, [textbox, chatbot], [textbox, chatbot], queue=False)
        click_event.then(lambda: gr.update(visible=False), None, suggestion_row)
        click_event.then(predict, [textbox, chatbot, session_id], chatbot)
        
        for btn in suggestion_btns:
            s_click_event = btn.click(on_suggestion_click, [btn, chatbot], [textbox, chatbot, suggestion_row], queue=False)
            s_click_event.then(predict, [btn, chatbot, session_id], chatbot)


    print("正在启动 AI 助手 Web 界面 (自定义)...")
    demo.launch()

if __name__ == '__main__':
    main() 