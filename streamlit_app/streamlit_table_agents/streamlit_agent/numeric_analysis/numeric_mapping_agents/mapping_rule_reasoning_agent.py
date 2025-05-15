# mapping_rule_reasoning_agent.py
# [Step 3️⃣] reasoning 기반 mapping rule 결정: mapping 기준, 예외 처리, 비율 계산, 다중 변수 비교 등을 reasoning 하세요.

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
llm = ChatOpenAI(temperature=0.2, model="gpt-4o")

# 🎯 Step 3: reasoning 기반 mapping rule 결정 프롬프트
MAPPING_RULE_REASONING_PROMPT = """
당신은 통계 조사 raw data를 분석하고 mapping 규칙을 결정하는 AI Assistant입니다.

아래 데이터를 기반으로 각 변수의 mapping rule을 reasoning 과정을 포함하여 작성하세요.
- 예외 처리, 특이값, 다중 변수 비교, 계산식 등 사람이 판단하는 과정을 모두 포함하세요.
- 최대한 자세하게 작성하세요.

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

[Mapping 계획 결과]
{mapping_plan_result}

출력 예시:
변수명:
    - Reasoning: 논리적 판단 및 설명
    - Rule: 적용할 mapping rule
...
"""

def mapping_rule_reasoning_fn(state: dict) -> dict:
    major_str = state.get("major_str", "")
    minor_str = state.get("minor_str", "")
    code_guide_str = state.get("code_guide_str", "")
    raw_variables = state.get("raw_variables", "")
    semantics_result = state.get("semantics_result", "")
    mapping_plan_result = state.get("mapping_plan_result", "")

    prompt = MAPPING_RULE_REASONING_PROMPT.format(
        major_str=major_str,
        minor_str=minor_str,
        code_guide_str=code_guide_str,
        raw_variables=raw_variables,
        semantics_result=semantics_result,
        mapping_plan_result=mapping_plan_result
    )

    response = llm.invoke(prompt)
    mapping_rule_result = response.content.strip()

    print("🤔 Mapping rule reasoning 완료.")
    return {**state, "mapping_rule_result": mapping_rule_result}

# ✅ LangGraph Node 정의
mapping_rule_reasoning_node = RunnableLambda(mapping_rule_reasoning_fn)