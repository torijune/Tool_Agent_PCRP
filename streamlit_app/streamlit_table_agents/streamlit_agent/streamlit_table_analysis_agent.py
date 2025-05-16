# streamlit_table_analysis_agent.py

import streamlit as st
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

TABLE_ANALYSIS_PROMPT = """
당신은 통계 데이터를 바탕으로 인구집단 간 패턴과 경향성을 객관적으로 요약하는 데이터 분석 전문가입니다.

📝 설문 조사 질문:
{selected_question}

📊 표 데이터 (선형화된 형태):
{linearized_table}

📈 주요 anchor column: {anchor_column}

📈 수치 분석 결과:
{ft_test_summary}

---

Let's think step by step

🎯 분석 및 요약 지침:

1. Anchor column ({anchor_column})을 중심으로 의미 있는 그룹 차이를 분석할 것  
2. 대분류 / 소분류의 모든 그룹을 나열하지 말고, 차이가 가장 큰 주요 그룹만 선택적으로 언급할 것  
3. 외부 배경지식, 주관적 해석 없이 오직 수치 기반 사실만 작성할 것  
4. 숫자 기반의 경향을 중심으로 "**상대적으로 더 높은 경향 보였음**", "**낮은 값을 나타냈음**" 등 음슴체로 작성할 것  
5. 평서문이 아닌, **보고서 음슴체 스타일**로 짧게 작성할 것 (예: ~했음, ~로 나타났음)  
6. 너무 단절적 (~했음. ~했음.) 표현은 피하고, 연결어를 활용해 자연스럽게 서술할 것  
7. 통계적으로 유의하지 않은 항목(p-value ≥ 0.05, 별표(*) 없음)은 분석 대상에서 제외할 것

---

📝 출력 예시:

대기환경 문제 관심 정도, 연령대 높을수록 더 높은 경향 보였음. 기저질환 있는 그룹, 대기오염 배출사업장 주변 거주 그룹, 실외 체류시간 많은 그룹도 상대적으로 높은 관심 보였음.
"""

def streamlit_table_anaylsis_node_fn(state):
    st.info("✅ [Table Analysis Agent] Start table analyzing")

    linearized_table = state["linearized_table"]
    ft_test_summary = state["ft_test_summary"]
    selected_question = state["selected_question"]

    # ✅ anchor column 추출
    try:
        result_df = pd.DataFrame(ft_test_summary).T.reset_index(names="대분류")
        result_df_sorted = result_df.sort_values("p-value", ascending=True)
        anchor_column = result_df_sorted.iloc[0]["대분류"]
    except Exception:
        anchor_column = "알 수 없음"

    with st.spinner("LLM 분석 중..."):
        prompt = TABLE_ANALYSIS_PROMPT.format(
            selected_question=selected_question,
            linearized_table=linearized_table,
            ft_test_summary=str(ft_test_summary),
            anchor_column=anchor_column
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