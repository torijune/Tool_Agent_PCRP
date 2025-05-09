from langgraph.graph import StateGraph, END
from typing import Annotated, TypedDict
from langchain_core.runnables import Runnable

from agents.abstract_agents.agents_B.retriever_agent import retriever_node
from agents.abstract_agents.agents_B.relevance_checker_agent import relevance_check_node

# 각 noded의 출력을 State라고 정의하여 각 Type을 미리 정해두는 것
class AgentState(TypedDict):
    query: Annotated[str, "query"]
    retrieved_doc: Annotated[str, "retrieved_doc"]
    relevance_decision: Annotated[str, "relevance_decision"]
    generated_analysis: Annotated[str, "generated_analysis"]
    hallucination_decision: Annotated[str, "hallucination_decision"]
    relevance_reject_num: Annotated[str, "relevance_reject_num"]


def build_abstract_graph() -> Runnable:
    builder = StateGraph(state_schema=AgentState)

    # 노드 정의
    builder.add_node("retriever", retriever_node)
    builder.add_node("relevance_checker", relevance_check_node)

    # 엣지 정의
    builder.set_entry_point("retriever")
    builder.add_edge("retriever", "relevance_checker")

    # 검색 결과 평가
    def route_relevance(state: dict) -> str:
        relevance_decision = state.get("relevance_decision", "")
        relevance_reject_num = state.get("relevance_reject_num", 0)
        if relevance_decision == "accept":
            return END
        elif relevance_decision == "reject":
            state["reject_number"] = relevance_reject_num + 1
            return "retriever"
        else:
            raise ValueError(f"[relevance_checker] Unexpected decision: {relevance_decision}")

    # 조건부 엣지 생성 (검색에 대해서)
    builder.add_conditional_edges("relevance_checker", route_relevance, [END, "retriever"])

    # # 생성 결과 평가
    # def route_hallucination(state: dict) -> str:
    #     decision = state.get("hallucination_decision", "")
    #     if decision in {"accept", "reject"}:
    #         return decision
    #     else:
    #         raise ValueError(f"[relevance_checker] Unexpected decision: {decision}")

    # # 조건부 엣지 생성 (생성에 대해서)
    # builder.add_conditional_edges(
    #     "hallucination_checker", 
    #     route_hallucination, 
    #     {
    #         "accept": END,
    #         "reject": "abstract_analyzer"
    #     }
    # )

    graph = builder.compile()
    return graph