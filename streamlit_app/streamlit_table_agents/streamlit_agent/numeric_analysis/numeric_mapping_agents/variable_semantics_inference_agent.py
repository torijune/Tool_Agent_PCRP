# variable_semantics_inference_agent.py
# [Step 1️⃣] 변수 의미 추론: 주어진 변수와 값, 코딩 가이드를 기반으로 변수의 의미를 추론하세요.  

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
llm = ChatOpenAI(temperature=0.2, model="gpt-4o")

# 🎯 Step 1: 변수 의미 추론 프롬프트
VARIABLE_SEMANTICS_PROMPT = """
당신은 통계 조사 raw data를 분석하고 변수 의미를 추론하는 AI Assistant입니다.

아래 데이터를 보고 각 변수의 의미를 사람이 이해할 수 있도록 설명하세요.

[대분류 값 목록]
{major_str}

[소분류 값 목록]
{minor_str}

[Raw Data Code Guide (일부)]
{code_guide_str}

[Raw Data 변수 설명]
{raw_variables}

출력 형식:
1. 변수명: 의미
2. 변수명: 의미
...
"""

def variable_semantics_inference_fn(state: dict) -> dict:
    major_str = state.get("major_str", "")
    minor_str = state.get("minor_str", "")
    code_guide_str = state.get("code_guide_str", "")
    raw_variables = state.get("raw_variables", "")

    prompt = VARIABLE_SEMANTICS_PROMPT.format(
        major_str=major_str,
        minor_str=minor_str,
        code_guide_str=code_guide_str,
        raw_variables=raw_variables
    )

    response = llm.invoke(prompt)
    semantics_result = response.content.strip()

    print("🔎 변수 의미 추론 완료.")
    return {**state, "semantics_result": semantics_result}

# ✅ LangGraph Node 정의
variable_semantics_node = RunnableLambda(variable_semantics_inference_fn)