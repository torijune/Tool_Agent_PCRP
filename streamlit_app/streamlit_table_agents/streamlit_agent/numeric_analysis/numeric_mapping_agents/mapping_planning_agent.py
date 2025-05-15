# mapping_planning_agent.py
# [Step 2️⃣] mapping 계획 수립: 각 변수에 대해 어떤 값이 어떤 label로 mapping 되어야 할지 계획을 세우세요.  

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
llm = ChatOpenAI(temperature=0.2, model="gpt-4o")

# 🎯 Step 2: mapping 계획 수립 프롬프트
MAPPING_PLANNING_PROMPT = """
당신은 통계 조사 raw data를 분석하고 mapping 계획을 수립하는 AI Assistant입니다.

아래 데이터를 바탕으로 각 변수에 대해 어떤 값(code)이 어떤 label로 mapping 되어야 할지 mapping table 형태로 정리하세요.

[대분류 값 목록]
{major_str}

[소분류 값 목록]
{minor_str}

[Raw Data Code Guide (일부)]
{code_guide_str}

[Raw Data 변수 설명]
{raw_variables}

[변수 의미 추론 결과]
{semantics_result}

출력 예시:
변수명:
    - code: label
    - code: label
...
"""

def mapping_planning_fn(state: dict) -> dict:
    major_str = state.get("major_str", "")
    minor_str = state.get("minor_str", "")
    code_guide_str = state.get("code_guide_str", "")
    raw_variables = state.get("raw_variables", "")
    semantics_result = state.get("semantics_result", "")

    prompt = MAPPING_PLANNING_PROMPT.format(
        major_str=major_str,
        minor_str=minor_str,
        code_guide_str=code_guide_str,
        raw_variables=raw_variables,
        semantics_result=semantics_result
    )

    response = llm.invoke(prompt)
    mapping_plan_result = response.content.strip()

    print("📝 Mapping 계획 수립 완료.")
    return {**state, "mapping_plan_result": mapping_plan_result}

# ✅ LangGraph Node 정의
mapping_planning_node = RunnableLambda(mapping_planning_fn)