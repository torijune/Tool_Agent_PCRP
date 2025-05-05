from langchain_core.runnables import RunnableLambda
import math
import re
from duckduckgo_search import DDGS

# 💡 복리 계산기 (단순 예시)
def calculate_compound_interest(principal: float, rate: float, years: int) -> str:
    final_amount = principal * ((1 + rate) ** years)
    return f"복리 계산 결과는 약 {round(final_amount):,}원입니다."

from duckduckgo_search import DDGS

def search_web(query: str) -> str:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=1))
        if results:
            title = results[0].get('title')
            url = results[0].get('href')
            return f"검색 결과: {title} ({url})"
        else:
            return "검색 결과를 찾을 수 없습니다."

# 💡 코드 실행 (Python)
def extract_code_from_query(query: str) -> str:
    # 단순 정규표현식 예시: "factorial(5)" 찾기
    match = re.search(r'factorial\s*\(\s*\d+\s*\)', query)
    if match:
        return f"result = math.{match.group()}"
    return ""

def execute_python_code(query: str) -> str:
    try:
        code = extract_code_from_query(query)
        if not code:
            return "코드 추출 실패: 실행할 수 없습니다."

        local_vars = {}
        exec(code, {"math": math}, local_vars)
        return f"파이썬 코드 실행 결과: {local_vars}"
    except Exception as e:
        return f"코드 실행 오류: {str(e)}"

# ✅ tool dispatcher
def tool_executor(plan: str, query: str) -> str:
    if "calculator" in plan.lower():
        # 실전에서는 query를 파싱해야 하지만, 여기는 하드코딩
        return calculate_compound_interest(10_000_000, 0.05, 3)
    elif "search" in plan.lower():
        return search_web(query)
    elif "python" in plan.lower():
        return execute_python_code(query)
    else:
        return "적절한 도구를 찾을 수 없습니다."

# ✅ LangChain-compatible node
def tool_caller_fn(state: dict) -> dict:
    plan = state.get("plan", "")
    query = state.get("query", "")
    tool_result = tool_executor(plan, query)
    return {**state, "tool_result": tool_result}

tool_caller_node = RunnableLambda(tool_caller_fn)