from langgraph.graph import StateGraph, END
from typing import Annotated, TypedDict
from langchain_core.runnables import Runnable

from agents.planner_agent import planner_node
from agents.tools import tool_caller_node
from agents.critic_agent import critic_node
from agents.responder_agent import responder_node

class AgentState(TypedDict):
    query: Annotated[str, "query"]
    plan: Annotated[str, "plan"]
    tool_result: Annotated[str, "tool"]
    decision: Annotated[str, "decision"]
    final_answer: Annotated[str, "final_answer"]

def build_workflow_graph() -> Runnable:
    builder = StateGraph(state_schema=AgentState)

    # 🧩 Node 등록

    ## 어떤 tool을 사용할지 planning node
    builder.add_node("planner", planner_node)
    ## plan 속에 포함 된 tool을 실행 시키는 node
    builder.add_node("tool_caller", tool_caller_node)
    ## tool 실행 결과, plan 등을 전반적으로 평가하여 accept, reject을 평가하는 node
    builder.add_node("critic", critic_node)
    ## tool 실행 결과, user query를 활용하여 최종 final response를 생성하는 node
    builder.add_node("responder", responder_node)

    # ▶️ Entry Point
    builder.set_entry_point("planner")

    # 🔁 Edge 연결
    builder.add_edge("planner", "tool_caller")
    builder.add_edge("tool_caller", "critic")
    builder.add_edge("responder", END) 

    # 🔀 조건 분기 함수
    def route_critic(state: dict) -> str:
        decision = state.get("decision", "")
        if decision == "accept":
            return "responder"
        elif decision == "reject":
            return "planner"
        else:
            raise ValueError(f"Unexpected decision: {decision}")

    # 📍 조건부 분기 등록 (END 포함)
    builder.add_conditional_edges("critic", route_critic, ["responder", "planner"])

    return builder.compile()