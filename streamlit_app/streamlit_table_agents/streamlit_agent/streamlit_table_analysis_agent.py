# streamlit_table_analysis_agent.py

import streamlit as st
import pandas as pd
import os

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

TABLE_ANALYSIS_PROMPT = """
당신은 통계 데이터를 바탕으로 인구집단 간 유의미한 차이를 중심으로 경향을 분석하고 요약하는 데이터 분석 전문가입니다.

# 설문 조사 질문:
{selected_question}

# 표 데이터 (선형화된 형태):
{linearized_table}

# 사전에 생성된 가설 (참고용):
{generated_hypotheses}

# 통계 분석 결과 (F/T test 기반 요약):
{ft_test_summary}

---

Let's think step by step.

🎯 분석 및 요약 지침:

1. 반드시 **F/T test 결과에서 통계적으로 유의미한 대분류만을 중심으로 분석**할 것 (p-value < 0.05, 유의성 별(*) 존재)
2. 모든 대분류 / 소분류를 나열하지 말고, **검정 결과에서 차이가 크고 의미 있는 대분류만 선택적으로 언급**할 것
3. **절대 해석하지 말 것**. 수치적 차이에 대한 인과 해석(예: 건강에 민감해서, 주변에 있어서 등)은 모두 금지함
4. 외부 배경지식, 주관적 추론, 해석적 언급은 절대 금지. **표로부터 직접 확인 가능한 사실만 서술**할 것
5. 수치 기반 경향을 다음과 같은 형식으로 서술할 것:
   - 상대적으로 더 높은 경향 보였음
   - 낮은 값을 나타냈음
6. 보고서 음슴체로 작성할 것 (예: ~했음, ~로 나타났음)
7. 문장 간 연결어를 활용해 자연스럽게 서술하고, 너무 단조롭거나 반복적인 표현 (~했음. ~했음.)은 피할 것
8. **유의성이 없거나, 검정에서 제외된 항목은 절대 언급하지 말 것**
9. **특정 대분류가 가장 두드러진 차이를 보였을 경우**, 해당 경향을 강조할 것
10. 숫자값을 직접 쓰지 말고 상대적인 경향만 언급할 것

---

📝 출력 예시:

기저질환 있는 그룹, 대기오염 배출사업장 주변 거주 그룹에서 대기환경 관심 정도가 상대적으로 높았음. 연령대가 높을수록 관심도가 증가하는 경향도 관찰됨.
"""

def streamlit_table_anaylsis_node_fn(state):
    st.info("✅ [Table Analysis Agent] Start table analyzing")

    linearized_table = state["linearized_table"]
    ft_test_summary = state["ft_test_summary"]
    selected_question = state["selected_question"]
    generated_hypotheses = state["generated_hypotheses"]

    with st.spinner("LLM 분석 중..."):
        prompt = TABLE_ANALYSIS_PROMPT.format(
            selected_question=selected_question,
            linearized_table=linearized_table,
            ft_test_summary=str(ft_test_summary),
            generated_hypotheses = generated_hypotheses
        )

        response = llm.invoke(prompt)
        table_analysis = response.content.strip()

    # ✅ Custom 스타일 적용
    st.markdown("""
        <style>
        .big-text {
            font-size: 17px !important;
            line-height: 1.7;
            max-width: 1200px;
        }
        </style>
        """, unsafe_allow_html=True)

    # ✅ Table Analysis 출력
    st.markdown("### 📋 Table Analysis 요약 결과")
    st.markdown(f"<div class='big-text'>{table_analysis}</div>", unsafe_allow_html=True)

    return {**state, "table_analysis": table_analysis}

streamlit_table_anaylsis_node = RunnableLambda(streamlit_table_anaylsis_node_fn)