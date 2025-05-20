from langgraph.graph import StateGraph, END
from typing import Annotated, TypedDict
from langchain_core.runnables import Runnable

from planner_intro_agent import intro_agent_node
from planner_audience_agent import audience_agent_node
from planner_structure_agent import structure_agent_node
from planner_question_agent import question_agent_node
from planner_analysis_agent import analysis_agent_node

class PlannerState(TypedDict):
    topic: Annotated[str, "사용자가 입력한 조사 주제"]
    lang: Annotated[str, "사용 언어"]
    objective: Annotated[str, "사용자가 직접 작성한 조사 목적 및 배경"]
    generated_objective: Annotated[str, "LLM이 정제한 조사 목적"]
    audience: Annotated[str, "LLM이 제안한 타겟 응답자 특성"]
    structure: Annotated[str, "설문 구조 및 섹션 구성"]
    questions: Annotated[str, "각 섹션별 추천 문항"]
    analysis: Annotated[str, "분석 방법 및 통계 고려사항"]

def build_planner_graph() -> Runnable:
    builder = StateGraph(state_schema=PlannerState)

    builder.add_node("intro_agent", intro_agent_node)
    builder.add_node("audience_agent", audience_agent_node)
    builder.add_node("structure_agent", structure_agent_node)
    builder.add_node("question_agent", question_agent_node)
    builder.add_node("analysis_agent", analysis_agent_node)

    builder.set_entry_point("intro_agent")
    builder.add_edge("intro_agent", "audience_agent")
    builder.add_edge("audience_agent", "structure_agent")
    builder.add_edge("structure_agent", "question_agent")
    builder.add_edge("question_agent", "analysis_agent")
    builder.add_edge("analysis_agent", END)

    return builder.compile()

planner_graph = build_planner_graph()