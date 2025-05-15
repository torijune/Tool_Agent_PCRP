# mapping_function_generator.py
# [Step 4️⃣] mapping_function(df) 코드를 작성하세요. 반드시 pandas 문법으로 작성하세요.

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
llm = ChatOpenAI(temperature=0.2, model="gpt-4o")

# 🎯 Step 4: 최종 mapping function code 생성 프롬프트
MAPPING_FUNCTION_GENERATOR_PROMPT = """
당신은 통계 조사 raw data를 분석하고 최종 mapping function 코드를 작성하는 AI Assistant입니다.

아래 정보를 기반으로 assign_strata(raw_df) 함수를 작성하세요.
- 반드시 pandas 문법으로 작성하세요.
- 가능한 경우 Skeleton 코드 형식을 유지하세요.
- 코드는 바로 실행 가능한 형태로 작성하세요.

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

[Mapping rule reasoning 결과]
{mapping_rule_result}

출력 예시:
```python
def assign_strata(raw_df):
    # 예시
    raw_df["성별"] = raw_df["SQ1"].map({1: "남성", 2: "여성"})
    ...
    return raw_df
```
"""

def mapping_function_generator_fn(state: dict) -> dict:
    major_str = state.get("major_str", "")
    minor_str = state.get("minor_str", "")
    code_guide_str = state.get("code_guide_str", "")
    raw_variables = state.get("raw_variables", "")
    semantics_result = state.get("semantics_result", "")
    mapping_plan_result = state.get("mapping_plan_result", "")
    mapping_rule_result = state.get("mapping_rule_result", "")
                                    
    prompt = MAPPING_FUNCTION_GENERATOR_PROMPT.format(
        major_str=major_str,
        minor_str=minor_str,
        code_guide_str=code_guide_str,
        raw_variables=raw_variables,
        semantics_result=semantics_result,
        mapping_plan_result=mapping_plan_result,
        mapping_rule_result=mapping_rule_result
    )

    response = llm.invoke(prompt)
    generated_code = response.content.strip()

    print("💻 mapping_function 코드 생성 완료.")

    # ✅ 추가: assign_strata 실행 후 raw_data_mapped 저장
    import pandas as pd
    import numpy as np

    local_vars = {"pd": pd, "np": np}
    exec(generated_code, globals(), local_vars)
    mapping_function = local_vars["assign_strata"]

    raw_data = state["raw_data"]  # ✅ 반드시 workflow state에 raw_data가 있어야 함
    mapped_raw_data = mapping_function(raw_data)
    
    return {
        **state,
        "generated_code": generated_code,
        "raw_data_mapped": mapped_raw_data    # ✅ 추가
    }

mapping_function_generator_node = RunnableLambda(mapping_function_generator_fn)