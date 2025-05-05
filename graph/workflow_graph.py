from langgraph.graph import StateGraph, END
from typing import Annotated, TypedDict
# StateGraph: LangGraph의 핵심 객체로 node와 edge를 정의함
# END: graph의 종료를 알리는 speical state
from langchain_core.runnables import Runnable
# Runnable: 각 node는 LangChain의 Runnable 인터페이스를 따라야 함

# 외부 (자체 커스텀) Agent Loading

## Planner LLM을 node로 정의하여 agent로 불러옴
from agents.planner_agent import planner_node
## 계획에 따라서 tool을 호출하는 agent를 불러옴
from agents.tools import tool_caller_node
## tool calling에 대해서 평가하고 accept, reject을 결정하는 agent를 불러옴
from agents.critic_agent import critic_node

# 각 node는 LangChain Runnable
# 입력은 {"query": str, "plan": str, "tool_result": str} 형태의 딕셔너리

class AgentState(TypedDict):
    query: Annotated[str,"query"]
    plan: Annotated[str,"plan"]
    tool_result: Annotated[str,"tool"]
    decision: Annotated[str,"decision"]

# LangGraph를 정의하기 위해 새로운 StateGraph 객체 생성
## StateGraph 객체를 통해 node, edge 추가 및 구성 가능
def build_workflow_graph() -> Runnable:
    builder = StateGraph(state_schema=AgentState)  # 이 부분 수정

    # Node 등록
    ## builder.add_node("node 명", node에 넣을 함수 명)
    builder.add_node("planner", planner_node)
    builder.add_node("tool_caller", tool_caller_node)
    builder.add_node("critic", critic_node)

    # 경로 구성
    ## builder.set_entry_point("시작점 명") -> 시작점을 정의하는 코드
    # 각 node들을 연결하는 edge를 정의

    ## builder.add_edge("출발 node 명", "도착 node 명")
    builder.set_entry_point("planner")

    # planner -> tool_caller
    builder.add_edge("planner", "tool_caller")
    # tool_caller -> critic
    builder.add_edge("tool_caller", "critic")


    # 조건부 분기 (조건부 edge를 정의)
        # builder.add_conditional_edges("node 명", condition 명) 을 통해 조건부 분기 생성
        # "condition 명"에 들어갈 condition을 정의 해야함
    
    # Critic 판단에 따른 조건 분기 -> condition을 정의
    def route_critic(state: dict) -> str:
        # decision 이라는 state를 만듦 -> 해당 state는 critic LLM의 decision이 들어갈 곳
        decision = state.get("decision", "")
        # 해당 decision의 값에 따라 다른 state를 정의
            # accept이면, END (Graph 끝)
            # reject이면, planner (다시 planner node로 이동하여 다시 tool_caller로 이동당함 -> 재계획)
        return "END" if decision == "accept" else "planner"

    builder.add_conditional_edges("critic", route_critic)

    # critic 끝나고 END를 정의
    builder.set_finish_point("critic")  # ✅ critic이 마지막 노드임을 선언

    # builder.compile()를 통해 Graph 완성
    return builder.compile()

'''
위의 graph는 아래의 구조를 가짐

User Query
   ↓
Planner (LLM 계획 수립)
   ↓
Tool Caller (계획 실행)
   ↓
Critic (평가)
   ↓
if Accept → END
   ↓
else → Re-plan (Planner로 다시)

'''