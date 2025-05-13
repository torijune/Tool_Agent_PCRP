import os
import openai

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

import streamlit as st

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

TABLE_PROMPT = """
당신은 통계 데이터를 바탕으로 인구집단 간 패턴과 경향성을 객관적으로 요약하는 데이터 분석 전문가입니다.

📝 설문 조사 질문:
{selected_question}

📊 표 데이터 (선형화된 형태):
{linearized_table}

📈 수치 분석 결과 (대분류별 항목별 최고/최저 값, 표준편차, 범위 등):
{numeric_anaylsis}

💡 데이터 기반 자동 생성 가설 목록 (참고용):
{generated_hypotheses}

---

Let's think step by step

🎯 분석 및 요약 지침:

1. 주요 대분류 (예: 연령대, 기저질환 여부, 대기오염 배출사업장 유무, 주요 체류 공간 등)를 중심으로 통계적으로 유의미한 차이가 있는지 분석할 것
2. 의미 있는 차이가 나타나는 주요 그룹만 선택적으로 언급할 것 (예: 평균 값, % 비율 차이가 크거나 두드러진 경우만)
3. 세부 소분류 (예: 성별, 20대/30대 등)는 의미 차이가 명확하게 클 경우에만 선택적으로 언급할 것
4. 모든 세부 그룹 또는 row를 나열하지 말 것 (불필요한 row 설명 금지)
5. 외부 배경지식, 주관적 해석 없이 오직 표와 수치 기반의 사실만 작성할 것
6. 숫자 기반 경향을 중심으로 "상대적으로 더 높은 경향 보였음", "뚜렷한 차이를 나타냈음", "두드러진 경향 보였음" 등의 표현으로 작성할 것
7. 지나치게 단절적 (~했음. ~했음. 반복) 표현을 지양하고, 관련된 그룹들은 연결어를 사용해 한 문장으로 묶을 것
8. 동일 의미의 그룹은 중복 표현을 피하고 문장 가독성을 높일 것
9. 정확한 수치값(예: 45.3%)을 언급하지 말고, 수치 차이에 기반한 상대적 경향만 서술할 것
10. 반드시 '데이터 기반 자동 생성 가설 목록'을 참고하여 가설을 검증하거나 해당 가설과 관련된 패턴을 탐색하고 분석 결과에 반영할 것

---

📝 출력 형식:

- 제목, 불릿, 리스트 없이 서술형으로 작성할 것
- 짧고 명확하게 분석 결과만 요약할 것
- 아래 예시처럼 작성할 것

예시:
대기환경 문제 관심 정도, 연령대 높을수록 두드러진 경향 보였음. 기저질환 있는 그룹, 대기오염 배출사업장 주변 거주 그룹, 실외 체류시간 많은 그룹도 상대적으로 더 높은 관심 보였음.
"""

def streamlit_table_anaylsis_node_fn(state):
    st.info("✅ [Table Analysis Agent] Start table analysis")

    linearized_table = state["linearized_table"]
    numeric_anaylsis = state["numeric_anaylsis"]
    selected_question = state["selected_question"]
    generated_hypotheses = state["generated_hypotheses"]

    prompt = TABLE_PROMPT.format(
        selected_question=selected_question,
        linearized_table=linearized_table,
        numeric_anaylsis=numeric_anaylsis,
        generated_hypotheses=generated_hypotheses
    )

    with st.spinner("테이블 분석 LLM 진행 중..."):
        response = llm.invoke(prompt)

    table_analysis = response.content.strip()

    st.markdown("### ✅ Draft Generated Report")
    st.markdown(table_analysis)

    return {**state, "table_analysis": table_analysis}

streamlit_table_anaylsis_node = RunnableLambda(streamlit_table_anaylsis_node_fn)