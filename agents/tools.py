from langchain_core.runnables import RunnableLambda
from agents.abstract_agents.abstract_graph.abstract_workflow_graph import build_abstract_graph
import math
import re
from duckduckgo_search import DDGS

'''
현재 tools:
- web searching
- 논문 Abstract 분석기 (LangGraph로 구현되어 있음)
'''

# 🌐 Web Search Tool
def search_web(query):
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=3))
        if results:
            title = results[0].get('title')
            url = results[0].get('href')
            return f"검색 결과: {title} ({url})"
        else:
            return "검색 결과를 찾을 수 없습니다."

# 📄 논문 Abstract 분석기 (LangGraph 기반)
def paper_abstract(query: str):
    # 만들어둔 LangGraph 불러오기
    abstract_graph = build_abstract_graph()
    input_state = {"query": query}
    result = abstract_graph.invoke(input_state)
    return result.get("retrieved_doc", "분석 결과를 생성하지 못했습니다.")

# 🧠 Tool 선택기 (Function Calling 기반)
def tool_executor(tool_name: str, query: str):
    tool_name = tool_name.lower()

    # web search 할 때
    if tool_name == "search":
        return search_web(query)
    
    # 논문 abstract 분석할 때
    elif tool_name == "abstract analyzer":
        return paper_abstract(query)
    else:
        return "❌ 적절한 도구를 찾을 수 없습니다."

# ✅ LangChain-compatible node
def tool_caller_fn(state: dict) -> dict:
    plan = state.get("plan", "")  # ex: "abstract analyzer"
    query = state.get("query", "")
    tool_result = tool_executor(plan, query)
    return {**state, "tool_result": tool_result}

tool_caller_node = RunnableLambda(tool_caller_fn)