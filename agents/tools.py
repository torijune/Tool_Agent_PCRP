from langchain_core.runnables import RunnableLambda
import math
import re
from duckduckgo_search import DDGS

'''
현재 tools:
- web searching

'''

# Web Search Tool
def search_web(query: str) -> str:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=3))
        if results:
            title = results[0].get('title')
            url = results[0].get('href')
            return f"검색 결과: {title} ({url})"
        else:
            return "검색 결과를 찾을 수 없습니다."

# 선택된 tool을 실행 시키는 함수
def tool_executor(plan: str, query: str) -> str:
    if "search" in plan.lower():
        return search_web(query)
    else:
        return "적절한 도구를 찾을 수 없습니다."

# ✅ LangChain-compatible node
def tool_caller_fn(state: dict) -> dict:
    # 앞서 정의된 plan을 불러옴
    plan = state.get("plan", "")
    query = state.get("query", "")

    # 이렇게 plan 속에서 선택된 tool을 실행
    tool_result = tool_executor(plan, query)
    return {**state, "tool_result": tool_result}

tool_caller_node = RunnableLambda(tool_caller_fn)