import os
import openai
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

# ✅ 환경 설정
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

# ✅ 수정 프롬프트
REVISION_PROMPT = """
당신은 통계 데이터를 바탕으로 인구집단 간 패턴과 경향성을 객관적으로 요약하는 데이터 분석 전문가입니다.

아래는 테이블 분석 결과에 대해 일부 잘못된 해석이 포함된 요약입니다. 피드백과 사전에 생성된 가설을 참고하여 잘못된 내용을 제거하고, 원본 데이터를 기반으로 수치 기반의 객관적 분석을 다시 작성할 것.

📊 표 데이터 (선형화된 형태):
{linearized_table}

📈 수치 분석 결과 (F/T-test 결과 요약):
{ft_test_summary}

📝 Reject된 보고서 (수정해야할 보고서):
{table_analysis}

❗ 피드백 (수정이 필요한 이유 또는 잘못된 부분):
{feedback}

---

Let's think step by step

🎯 수정 및 재작성 지침:

1. 수치 분석 결과에서 통계적으로 유의미한 대분류 항목(별표가 있는 항목)은 반드시 요약에 언급할 것
2. 외부 배경지식, 주관적 해석 없이 오직 수치 기반 사실만 작성할 것
3. 통계적으로 유의하지 않은 항목(p-value ≥ 0.05, 별표 없음)은 절대 요약에 포함하지 말 것
4. 숫자 기반의 경향을 중심으로 "상대적으로 더 높은 경향 보였음", "낮은 값을 나타냈음" 등 음슴체로 작성할 것
5. 문장은 평서문이 아닌, 보고서 음슴체 스타일로 작성할 것 (예: ~했음, ~로 나타났음)
6. 너무 단절적 (~했음. ~했음.) 표현은 피하고, 연결어를 활용해 자연스럽게 서술할 것
7. 정확한 수치값은 쓰지 말고, 수치 차이에 기반한 경향만 서술할 것
8. 사소한 차이는 무시하고, 유의한 항목만 중심으로 간결하게 작성할 것
9. 동일 의미의 그룹이 중복되지 않도록 주의할 것
"""

# ✅ LangGraph 노드 함수
def streamlit_revise_table_analysis_fn(state):
    st.info("✅ [Revision Agent] Start table analysis revision")

    # 📌 table_analysis는 revised가 있으면 그것을 우선, 없으면 초안을 fallback
    table_analysis = state.get("revised_analysis") or state.get("table_analysis", "")

    prompt = REVISION_PROMPT.format(
        linearized_table=state["linearized_table"],
        ft_test_summary=str(state["ft_test_summary"]),
        table_analysis=table_analysis,
        feedback=state["feedback"]
    )

    with st.spinner("LLM Revision Agent가 수정 보고서를 작성 중..."):
        response = llm.invoke(prompt)

    revised_analysis = response.content.strip()

    st.success("🎉 수정된 최종 보고서:")
    st.text(revised_analysis)

    return {
        **state,
        "revised_analysis": revised_analysis
    }

# ✅ LangGraph 노드 등록
streamlit_revise_table_analysis_node = RunnableLambda(streamlit_revise_table_analysis_fn)