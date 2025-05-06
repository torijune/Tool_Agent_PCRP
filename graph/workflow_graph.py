from langgraph.graph import StateGraph, END
from typing import Annotated, TypedDict
from langchain_core.runnables import Runnable

from agents.planner_agent import planner_node
from agents.tools import tool_caller_node
from agents.critic_agent import critic_node

class AgentState(TypedDict):
    query: Annotated[str, "query"]
    plan: Annotated[str, "plan"]
    tool_result: Annotated[str, "tool"]
    decision: Annotated[str, "decision"]

def build_workflow_graph() -> Runnable:
    builder = StateGraph(state_schema=AgentState)

    # 🧩 Node 등록
    builder.add_node("planner", planner_node)
    builder.add_node("tool_caller", tool_caller_node)
    builder.add_node("critic", critic_node)

    # ▶️ Entry Point
    builder.set_entry_point("planner")

    # 🔁 Edge 연결
    builder.add_edge("planner", "tool_caller")
    builder.add_edge("tool_caller", "critic")

    # 🔀 조건 분기 함수
    def route_critic(state: dict) -> str:
        decision = state.get("decision", "")
        if decision == "accept":
            return END
        elif decision == "reject":
            return "planner"
        else:
            raise ValueError(f"Unexpected decision: {decision}")

    # 📍 조건부 분기 등록 (END 포함)
    builder.add_conditional_edges("critic", route_critic, [END, "planner"])

    # Remove this line that causes the error
    # builder.set_finish_point(END)

    return builder.compile()