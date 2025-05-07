from langgraph.graph import StateGraph, END
from typing import Annotated, TypedDict
from langchain_core.runnables import Runnable

from agents.abstract_agents.agents_B.retriever_agent import retriever_node
from agents.abstract_agents.agents_B.relevance_checker_agent import relevance_check_node
from agents.abstract_agents.agents_B.abstract_analysis_agent import abstract_analysis_node
from agents.abstract_agents.agents_B.hallucination_checker_agent import hallucination_check_node


# 각 noded의 출력을 State라고 정의하여 각 Type을 미리 정해두는 것
class AgentState(TypedDict):
    query: Annotated[str, "query"]
    retrieved_doc: Annotated[str, "retrieved_doc"]
    relevance_decision: Annotated[str, "relevance_decision"]
    generated_analysis: Annotated[str, "generated_analysis"]
    hallucination_decision: Annotated[str, "hallucination_decision"]


def build_abstract_graph() -> Runnable:
    builder = StateGraph(state_schema=AgentState)

    # 노드 정의
    builder.add_node("retriever", retriever_node)
    builder.add_node("relevance_checker", relevance_check_node)
    builder.add_node("abstract_analyzer", abstract_analysis_node)
    builder.add_node("hallucination_checker", hallucination_check_node)

    # 엣지 정의
    builder.set_entry_point("retriever")
    builder.add_edge("retriever", "relevance_checker")
    builder.add_edge("relevance_checker", "abstract_analyzer")
    builder.add_edge("abstract_analyzer", "hallucination_checker")

    # 검색 결과 평가
    def route_relevance(state: dict) -> str:
        decision = state.get("relevance_decision", "")
        if decision in {"accept", "reject"}:
            return decision
        else:
            raise ValueError(f"[relevance_checker] Unexpected decision: {decision}")

    # 조건부 엣지 생성 (검색에 대해서)
    builder.add_conditional_edges(
        "relevance_checker", 
        route_relevance, 
        {
            "accept": "abstract_analyzer",
            "reject": "retriever"
        }
    )

    # 생성 결과 평가
    def route_hallucination(state: dict) -> str:
        decision = state.get("hallucination_decision", "")
        if decision in {"accept", "reject"}:
            return decision
        else:
            raise ValueError(f"[relevance_checker] Unexpected decision: {decision}")

    # 조건부 엣지 생성 (생성에 대해서)
    builder.add_conditional_edges(
        "hallucination_checker", 
        route_hallucination, 
        {
            "accept": END,
            "reject": "abstract_analyzer"
        }
    )

    graph = builder.compile()
    return graph