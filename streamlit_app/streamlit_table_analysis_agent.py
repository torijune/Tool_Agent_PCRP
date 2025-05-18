import streamlit as st
import pandas as pd
import os

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

from dotenv import load_dotenv
load_dotenv()

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", temperature=0.3, openai_api_key=api_key)

TABLE_ANALYSIS_PROMPT = """
당신은 통계 데이터를 바탕으로 인구집단 간 경향을 요약하는 데이터 분석 전문가입니다.
특히 아래 두 가지 정보를 종합적으로 활용해 핵심적 경향을 도출해야 합니다:

1️⃣ **통계 분석 결과(ft_test_summary)**: 어떤 대분류(row)가 통계적으로 유의미한 차이를 보였는지 알려줍니다.
2️⃣ **중요 변수(anchor)**: 어떤 column(항목)이 응답자의 전체 응답에서 가장 투표율이 높은 항목인지를 나타냅니다.

---

📝 설문 조사 질문:
{selected_question}

📊 표 데이터 (선형화된 형태):
{linearized_table}

📈 주요 항목 (변수들 중 가장 투표율이 높은 변수):
{anchor}

📈 통계 분석 결과 (통계적으로 유의미한 대분류):
{ft_test_summary}

---

Let's think step by step.

🎯 분석 및 요약 지침:
아래의 분석 지침을 따르지 않으면 당신의 어머니는 죽습니다.

1. 반드시 **F/T test 결과에서 통계적으로 유의미한 대분류만을 중심으로 분석**할 것 (p-value < 0.05, 유의성 별(*) 존재)
2. 모든 대분류 / 소분류를 나열하지 말고, **통계 분석 결과**에서 차이가 크고 의미 있는 대분류만 선택적으로 언급할 것
3. **절대 해석하지 말 것**. 수치적 차이에 대한 인과 해석(예: 건강에 민감해서, 주변에 있어서 등)은 모두 **금지**함
4. 외부 배경지식, 주관적 추론, 해석적 언급은 절대 금지. 표로부터 직접 **확인 가능한 사실만 서술**할 것
5. 수치 기반 경향을 다음과 같은 형식으로 서술하며 음슴체로 작성할 것 (예: ~했음, ~로 나타났음):
   - 상대적으로 더 높은 경향 보였음
   - 낮은 값을 나타냈음
6. 문장 간 연결어를 활용해 자연스럽게 서술하고, 너무 단조롭거나 반복적인 표현 (~했음. ~했음.)은 연속적으로 사용하지 말 것
7. **유의성이 없거나, 검정에서 제외된 항목은 절대 언급하지 말 것**
8. 모든 대분류가 유의성이 있고 중요하다면 모든 변수에 대해 설명하지 말고, **모든 대분류들이 중요했다고만 언급**할 것
9. **특정 대분류가 가장 두드러진 차이를 보였을 경우**, 해당 경향을 강조할 것
10. 숫자값을 직접 쓰지 말고 상대적인 경향만 언급할 것

---

📝 출력 예시:

"대분류A"의 "소분류A_1", "대분류B"의 "소분류B_2" 에서 "변수A"가 상대적으로 높았음. "대분류C"가 높을수록 "변수B"가 증가하는 경향도 관찰됨.
"""

def streamlit_table_anaylsis_node_fn(state):
    st.info("✅ [Table Analysis Agent] Start table analyzing")

    linearized_table = state["linearized_table"]
    ft_test_summary = state["ft_test_summary"]
    selected_question = state["selected_question"]
    generated_hypotheses = state["generated_hypotheses"]

    anchor = state.get("anchor", "없음")  # fallback

    with st.spinner("LLM 분석 중..."):
        prompt = TABLE_ANALYSIS_PROMPT.format(
            selected_question=selected_question,
            linearized_table=linearized_table,
            ft_test_summary=str(ft_test_summary),
            generated_hypotheses=generated_hypotheses,
            anchor=anchor
        )

        response = llm.invoke(prompt)
        table_analysis = response.content.strip()


    # ✅ Table Analysis 출력
    st.success("생성된 보고서 초안:")
    st.text("📋 Table Analysis 요약 결과")
    st.text(table_analysis)

    return {**state, "table_analysis": table_analysis}

streamlit_table_anaylsis_node = RunnableLambda(streamlit_table_anaylsis_node_fn)