#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
深思熟虑智能体（Deliberative Agent）- 智能投研助手

基于LangGraph实现的深思熟虑型智能体，适用于投资研究场景，能够整合数据，
进行多步骤分析和推理，生成投资观点和研究报告。

核心流程：
1. 感知：收集市场数据和信息
2. 建模：构建内部世界模型，理解市场状态
3. 推理：生成多个候选分析方案并模拟结果
4. 决策：选择最优投资观点并形成报告
5. 报告：生成完整研究报告
"""

import os
import json
from typing import Dict, List, Any, Literal, TypedDict, Optional, Union, Tuple
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import Tongyi
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field, field_validator
from langgraph.graph import StateGraph, END

# 设置API密钥
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

# 创建LLM实例
llm = Tongyi(model_name="qwen-flash", dashscope_api_key=DASHSCOPE_API_KEY, enable_search=True)

# 定义输出模型
class PerceptionOutput(BaseModel):
    """感知阶段输出的市场数据和信息"""
    market_overview: str = Field(..., description="市场概况和最新动态")
    key_indicators: Dict[str, str] = Field(..., description="关键经济和市场指标")
    recent_news: List[str] = Field(..., description="近期重要新闻")
    industry_trends: Dict[str, str] = Field(..., description="行业趋势分析")

class ModelingOutput(BaseModel):
    """建模阶段输出的内部世界模型"""
    market_state: str = Field(..., description="当前市场状态评估")
    economic_cycle: str = Field(..., description="经济周期判断")
    risk_factors: List[str] = Field(..., description="主要风险因素")
    opportunity_areas: List[str] = Field(..., description="潜在机会领域")
    market_sentiment: str = Field(..., description="市场情绪分析")

class ReasoningPlan(BaseModel):
    """推理阶段生成的候选分析方案"""
    plan_id: str = Field(..., description="方案ID")
    hypothesis: str = Field(..., description="投资假设")
    analysis_approach: str = Field(..., description="分析方法")
    expected_outcome: str = Field(..., description="预期结果")
    confidence_level: float = Field(..., description="置信度(0-1)")
    pros: List[str] = Field(..., description="方案优势")
    cons: List[str] = Field(..., description="方案劣势")

class ReasoningPlanList(BaseModel):
    """推理阶段输出的候选方案列表"""
    plans: List[ReasoningPlan] = Field(..., description="候选投资分析方案列表，至少3个")

class DecisionOutput(BaseModel):
    """决策阶段选择的最优投资观点"""
    selected_plan_id: str = Field(..., description="选中的方案ID")
    investment_thesis: str = Field(..., description="投资论点")
    supporting_evidence: List[str] = Field(..., description="支持证据")
    risk_assessment: str = Field(..., description="风险评估")
    recommendation: str = Field(..., description="投资建议")
    timeframe: str = Field(..., description="时间框架")
    
# 定义智能体状态
class ResearchAgentState(TypedDict):
    """研究智能体的状态"""
    # 输入
    research_topic: str  # 研究主题
    industry_focus: str  # 行业焦点
    time_horizon: str  # 时间范围(短期/中期/长期)
    
    # 处理状态
    perception_data: Optional[Dict[str, Any]]  # 感知阶段收集的数据
    world_model: Optional[Dict[str, Any]]  # 内部世界模型
    reasoning_plans: Optional[List[Dict[str, Any]]]  # 候选分析方案
    selected_plan: Optional[Dict[str, Any]]  # 选中的最优方案
    
    # 输出
    final_report: Optional[str]  # 最终研究报告
    
    # 控制流
    current_phase: Literal["perception", "modeling", "reasoning", "decision", "report"]
    error: Optional[str]  # 错误信息
    retry_count: Optional[int]  # 当前阶段失败重试次数


# 提示模板
PERCEPTION_PROMPT = """你是一个专业的投资研究分析师，请收集和整理关于以下研究主题的市场数据和信息：

研究主题: {research_topic}
行业焦点: {industry_focus}
时间范围: {time_horizon}

请从以下几个方面进行市场感知：
1. 市场概况和最新动态
2. 关键经济和市场指标
3. 近期重要新闻（至少3条）
4. 行业趋势分析（至少针对3个细分领域）

根据你的专业知识和经验，提供尽可能详细和准确的信息。

{format_instructions}
"""

MODELING_PROMPT = """你是一个资深投资策略师，请根据以下市场数据和信息，构建市场内部模型，进行深度分析：

研究主题: {research_topic}
行业焦点: {industry_focus}
时间范围: {time_horizon}
当前时间： {current_time}

市场数据和信息:
{perception_data}

请构建一个全面的市场内部模型，包括：
1. 当前市场状态评估
2. 经济周期判断
3. 主要风险因素（至少3个）
4. 潜在机会领域（至少3个）
5. 市场情绪分析

{format_instructions}
"""

REASONING_PROMPT = """你是一个战略投资顾问，请根据以下市场模型，生成3个不同的投资分析方案：

研究主题: {research_topic}
行业焦点: {industry_focus}
时间范围: {time_horizon}

市场内部模型:
{world_model}

请为每个方案提供：
1. 方案ID（简短标识符）
2. 投资假设
3. 分析方法
4. 预期结果
5. 置信度（0-1之间的小数）
6. 方案优势（至少3点）
7. 方案劣势（至少2点）

这些方案应该有明显的差异，代表不同的投资思路或分析角度。

{format_instructions}
"""

DECISION_PROMPT = """你是一个投资决策委员会主席，请评估以下候选分析方案，选择最优方案并形成投资决策：

研究主题: {research_topic}
行业焦点: {industry_focus}
时间范围: {time_horizon}

市场内部模型:
{world_model}

候选分析方案:
{reasoning_plans}

请基于方案的假设、分析方法、预期结果、置信度以及优缺点，选择最优的投资方案，并给出详细的决策理由。
你的决策应该综合考虑投资潜力、风险水平和时间框架的匹配度。

{format_instructions}
"""

REPORT_PROMPT = """你是一个专业的投资研究报告撰写人，请根据以下信息生成一份完整的投资研究报告：

研究主题: {research_topic}
行业焦点: {industry_focus}
时间范围: {time_horizon}

市场数据和信息:
{perception_data}

市场内部模型:
{world_model}

选定的投资决策:
{selected_plan}

请生成一份结构完整、逻辑清晰的投研报告，包括但不限于：
1. 报告标题和摘要
2. 市场和行业背景
3. 核心投资观点
4. 详细分析论证
5. 风险因素
6. 投资建议
7. 时间框架和预期回报

报告应当专业、客观，同时提供足够的分析深度和洞见。
"""

# 第一阶段：感知 - 收集市场数据和信息
def perception(state: ResearchAgentState) -> ResearchAgentState:
    """感知阶段：收集和整理市场数据和信息"""
    
    print("1. 感知阶段：收集市场数据和信息...")
    
    try:
        # 准备提示
        parser = PydanticOutputParser(pydantic_object=PerceptionOutput)
        prompt = ChatPromptTemplate.from_template(PERCEPTION_PROMPT)

        # 构建输入
        input_data = {
            "research_topic": state["research_topic"],
            "industry_focus": state["industry_focus"],
            "time_horizon": state["time_horizon"],
            "format_instructions": parser.get_format_instructions()
        }

        # 调用LLM
        chain = prompt | llm | parser
        result = chain.invoke(input_data)

        # 更新状态（保持current_phase为当前阶段，由router统一推进）
        new_state = dict(state)
        new_state.update({
            "perception_data": result.model_dump(),
            "current_phase": "perception",
            "error": None,
            "retry_count": 0
        })
        return new_state
    except Exception as e:
        retry_count = state.get("retry_count", 0) + 1
        print(f"   感知阶段失败，将进行第 {retry_count} 次重试: {str(e)}")
        new_state = dict(state)
        new_state.update({
            "error": f"感知阶段出错: {str(e)}",
            "current_phase": "perception",
            "retry_count": retry_count
        })
        return new_state

# 第二阶段：建模 - 构建内部世界模型
def modeling(state: ResearchAgentState) -> ResearchAgentState:
    """建模阶段：构建内部世界模型，理解市场状态"""
    
    print("2. 建模阶段：构建内部世界模型...")
    
    try:
        # 确保感知数据已存在
        if not state.get("perception_data"):
            return {
                **state,
                "error": "建模阶段缺少感知数据",
                "current_phase": "perception"  # 回到感知阶段
            }
        
        # 准备提示
        parser = PydanticOutputParser[ModelingOutput](pydantic_object=ModelingOutput)
        prompt = ChatPromptTemplate.from_template(MODELING_PROMPT)

        # 构建输入
        input_data = {
            "research_topic": state["research_topic"],
            "industry_focus": state["industry_focus"],
            "time_horizon": state["time_horizon"],
            "current_time": datetime.now().strftime("%Y年%m月%d日"),
            "perception_data": json.dumps(state["perception_data"], ensure_ascii=False, indent=2),
            "format_instructions": parser.get_format_instructions()
        }

        # 调用LLM
        chain = prompt | llm | parser
        result = chain.invoke(input_data)

        # 更新状态（保持current_phase为当前阶段，由router统一推进）
        return {
            **state,
            "world_model": result.model_dump(),
            "current_phase": "modeling",
            "error": None,
            "retry_count": 0
        }
    except Exception as e:
        retry_count = state.get("retry_count", 0) + 1
        print(f"   建模阶段失败，将进行第 {retry_count} 次重试: {str(e)}")
        return {
            **state,
            "error": f"建模阶段出错: {str(e)}",
            "current_phase": "modeling",  # 保持在当前阶段
            "retry_count": retry_count
        }

# 第三阶段：推理 - 生成候选分析方案
def reasoning(state: ResearchAgentState) -> ResearchAgentState:
    """推理阶段：生成多个候选分析方案并模拟结果"""
    
    print("3. 推理阶段：生成候选分析方案...")
    
    try:
        # 确保世界模型已存在
        if not state.get("world_model"):
            return {
                **state,
                "error": "推理阶段缺少世界模型",
                "current_phase": "modeling"  # 回到建模阶段
            }
        
        # 准备提示
        parser = PydanticOutputParser(pydantic_object=ReasoningPlanList)
        prompt = ChatPromptTemplate.from_template(REASONING_PROMPT)

        # 构建输入
        input_data = {
            "research_topic": state["research_topic"],
            "industry_focus": state["industry_focus"],
            "time_horizon": state["time_horizon"],
            "world_model": json.dumps(state["world_model"], ensure_ascii=False, indent=2),
            "format_instructions": parser.get_format_instructions()
        }

        # 调用LLM
        chain = prompt | llm | parser
        result = chain.invoke(input_data)

        # 更新状态（保持current_phase为当前阶段，由router统一推进）
        return {
            **state,
            "reasoning_plans": [plan.model_dump() for plan in result.plans],
            "current_phase": "reasoning",
            "error": None,
            "retry_count": 0
        }
    except Exception as e:
        retry_count = state.get("retry_count", 0) + 1
        print(f"   推理阶段失败，将进行第 {retry_count} 次重试: {str(e)}")
        return {
            **state,
            "error": f"推理阶段出错: {str(e)}",
            "current_phase": "reasoning",  # 保持在当前阶段
            "retry_count": retry_count
        }

# 第四阶段：决策 - 选择最优方案
def decision(state: ResearchAgentState) -> ResearchAgentState:
    """决策阶段：评估候选方案并选择最优投资观点"""
    
    print("4. 决策阶段：选择最优投资观点...")
    
    try:
        # 确保候选方案已存在
        if not state.get("reasoning_plans"):
            return {
                **state,
                "error": "决策阶段缺少候选方案",
                "current_phase": "reasoning"  # 回到推理阶段
            }
        
        # 准备提示
        parser = PydanticOutputParser(pydantic_object=DecisionOutput)
        prompt = ChatPromptTemplate.from_template(DECISION_PROMPT)

        # 构建输入
        input_data = {
            "research_topic": state["research_topic"],
            "industry_focus": state["industry_focus"],
            "time_horizon": state["time_horizon"],
            "world_model": json.dumps(state["world_model"], ensure_ascii=False, indent=2),
            "reasoning_plans": json.dumps(state["reasoning_plans"], ensure_ascii=False, indent=2),
            "format_instructions": parser.get_format_instructions()
        }

        # 调用LLM
        chain = prompt | llm | parser
        result = chain.invoke(input_data)

        # 更新状态（保持current_phase为当前阶段，由router统一推进）
        return {
            **state,
            "selected_plan": result.model_dump(),
            "current_phase": "decision",
            "error": None,
            "retry_count": 0
        }
    except Exception as e:
        retry_count = state.get("retry_count", 0) + 1
        print(f"   决策阶段失败，将进行第 {retry_count} 次重试: {str(e)}")
        return {
            **state,
            "error": f"决策阶段出错: {str(e)}",
            "current_phase": "decision",  # 保持在当前阶段
            "retry_count": retry_count
        }

# 第五阶段：报告 - 生成完整研究报告
def report_generation(state: ResearchAgentState) -> ResearchAgentState:
    """报告阶段：生成完整的投资研究报告"""
    
    print("5. 报告阶段：生成完整研究报告...")
    
    try:
        # 确保选定方案已存在
        if not state.get("selected_plan"):
            return {
                **state,
                "error": "报告阶段缺少选定方案",
                "current_phase": "decision"  # 回到决策阶段
            }
        
        # 准备提示
        prompt = ChatPromptTemplate.from_template(REPORT_PROMPT)
        
        # 构建输入
        input_data = {
            "research_topic": state["research_topic"],
            "industry_focus": state["industry_focus"],
            "time_horizon": state["time_horizon"],
            "perception_data": json.dumps(state["perception_data"], ensure_ascii=False, indent=2),
            "world_model": json.dumps(state["world_model"], ensure_ascii=False, indent=2),
            "selected_plan": json.dumps(state["selected_plan"], ensure_ascii=False, indent=2)
        }
        
        # 调用LLM
        chain = prompt | llm | StrOutputParser()
        result = chain.invoke(input_data)
        
        # 更新状态（保持current_phase为当前阶段，由router统一推进）
        return {
            **state,
            "final_report": result,
            "current_phase": "report",
            "error": None,
            "retry_count": 0
        }
    except Exception as e:
        retry_count = state.get("retry_count", 0) + 1
        print(f"   报告阶段失败，将进行第 {retry_count} 次重试: {str(e)}")
        return {
            **state,
            "error": f"报告生成阶段出错: {str(e)}",
            "current_phase": "report",  # 保持在当前阶段
            "retry_count": retry_count
        }

# 最大重试次数
MAX_RETRIES = 3

# 路由函数 - 根据当前阶段决定下一步
def router(state: ResearchAgentState) -> str:
    """根据当前阶段路由到下一步或结束"""

    # 如果有错误，检查是否超过最大重试次数
    if state.get("error"):
        retry_count = state.get("retry_count", 0)
        if retry_count >= MAX_RETRIES:
            print(f"\n超过最大重试次数({MAX_RETRIES})，流程终止")
            return END
        # 未超过重试上限，回到当前阶段重试
        return state["current_phase"]

    # 根据当前阶段决定下一步
    current = state["current_phase"]

    if current == "perception":
        return "modeling"
    elif current == "modeling":
        return "reasoning"
    elif current == "reasoning":
        return "decision"
    elif current == "decision":
        return "report"
    elif current == "report":
        return END
    else:
        return END

# 创建智能体工作流图
def create_research_agent_workflow() -> StateGraph:
    """创建深思熟虑型研究智能体工作流图"""
    
    # 创建状态图
    workflow = StateGraph[ResearchAgentState, None, ResearchAgentState, ResearchAgentState](ResearchAgentState)
    
    # 添加节点
    workflow.add_node("perception", perception)
    workflow.add_node("modeling", modeling)
    workflow.add_node("reasoning", reasoning)
    workflow.add_node("decision", decision)
    workflow.add_node("report", report_generation)
    
    # 设置入口点
    workflow.set_entry_point("perception")
    
    # 设置边和转换条件（通过router实现失败重试）
    workflow.add_conditional_edges("perception", router, {
        "modeling": "modeling",
        "perception": "perception",  # 失败时重试
        END: END
    })
    workflow.add_conditional_edges("modeling", router, {
        "reasoning": "reasoning",
        "modeling": "modeling",  # 失败时重试
        END: END
    })
    workflow.add_conditional_edges("reasoning", router, {
        "decision": "decision",
        "reasoning": "reasoning",  # 失败时重试
        END: END
    })
    workflow.add_conditional_edges("decision", router, {
        "report": "report",
        "decision": "decision",  # 失败时重试
        END: END
    })
    workflow.add_conditional_edges("report", router, {
        "report": "report",  # 失败时重试
        END: END
    })
    
    # 编译工作流
    return workflow.compile()

# 测试函数
def run_research_agent(topic: str, industry: str, horizon: str) -> Dict[str, Any]:
    """运行研究智能体并返回结果"""
    
    # 创建工作流
    agent = create_research_agent_workflow()
    
    # 准备初始状态
    initial_state = {
        "research_topic": topic,
        "industry_focus": industry,
        "time_horizon": horizon,
        "perception_data": None,
        "world_model": None,
        "reasoning_plans": None,
        "selected_plan": None,
        "final_report": None,
        "current_phase": "perception",
        "error": None,
        "retry_count": 0
    }
    print("LangGraph Mermaid流程图：")
    print(agent.get_graph().draw_mermaid())
    
    # 运行智能体
    result = agent.invoke(initial_state)
    
    return result

# 主函数
if __name__ == "__main__":
    print("=== 深思熟虑智能体 - 智能投研助手 ===\n")
    print("使用模型：qwen-flash\n")
    
    # 用户输入
    topic = input("请输入研究主题 (例如: 新能源汽车行业投资机会): ")
    industry = input("请输入行业焦点 (例如: 电动汽车制造、电池技术): ")
    horizon = input("请输入时间范围 [短期/中期/长期]: ")
    
    print("\n智能投研助手开始工作...\n")
    
    try:
        # 运行智能体
        result = run_research_agent(topic, industry, horizon)
        
        # 处理结果
        if result.get("error"):
            print(f"\n发生错误: {result['error']}")
        else:
            print("\n=== 最终研究报告 ===\n")
            print(result.get("final_report", "未生成报告"))
            
            # 保存报告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_report_{timestamp}.txt"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(result.get("final_report", "未生成报告"))
            
            print(f"\n报告已保存为: {filename}")
            
    except Exception as e:
        print(f"\n运行过程中发生错误: {str(e)}") 