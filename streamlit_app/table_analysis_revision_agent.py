import os
import openai
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, openai_api_key=api_key)

REVISION_PROMPT = {
    "한국어": """
당신은 통계 데이터를 바탕으로 인구집단 간 패턴과 경향성을 객관적으로 요약하는 데이터 분석 전문가입니다.

아래는 테이블 분석 결과에 대해 일부 잘못된 해석이 포함된 요약입니다. 피드백과 사전에 생성된 가설을 참고하여 잘못된 내용을 제거하고, 원본 데이터를 기반으로 수치 기반의 객관적 분석을 다시 작성할 것.

📊 표 데이터 (선형화된 형태):
{linearized_table}

📈 주요 항목 (변수들 중 가장 투표율이 높은 변수):
{anchor}

📈 통계 분석 결과 (통계적으로 유의미한 대분류):
{ft_test_summary}

📝 Reject된 보고서 (수정해야할 보고서):
{report_to_modify}

❗ 피드백 (수정이 필요한 이유 또는 잘못된 부분):
{feedback}

---

Let's think step by step

🎯 수정 및 재작성 지침:

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
11. 이전 수정 버전의 문장 표현을 재사용하지 않고, 새로운 어휘와 구조로 작성할 것
12. 추론 과정을 작성하지 말고 최종적으로 수정한 보고서만 출력하세요.
""",
    "English": """
You are a data analyst who objectively summarizes population-level patterns based on statistical data.

Below is a summary that contains partially incorrect interpretations of a statistical table analysis. Based on the given feedback and hypotheses, revise the summary by removing inaccurate parts and rewrite a new objective analysis grounded in the data.

📊 Table data (linearized):
{linearized_table}

📈 Key variables (most selected):
{anchor}

📈 Statistical analysis results (significant categories):
{ft_test_summary}

📝 Rejected summary (needs revision):
{report_to_modify}

❗ Feedback (reason for revision or incorrect points):
{feedback}

---

Let's think step by step

🎯 Revision Guidelines:

1. Focus only on categories that showed statistically significant differences in the F/T test (p-value < 0.05, marked with *)
2. Do not list all categories/subcategories; mention only those with meaningful differences
3. **Do not provide causal interpretations** – explanations like “due to health concerns” or similar are prohibited
4. No external knowledge or speculation – write only what is verifiable from the table
5. Describe trends in a form such as:
   - Showed relatively higher trend
   - Showed lower values
6. Write in bullet-style declarative tone (e.g., “~was observed”, “~was shown”)
7. Use transition words to make the sentences flow naturally; avoid repetitive sentence endings
8. **Do not mention non-significant or excluded categories**
9. **If a particular group showed the strongest difference**, emphasize it
10. Do not mention actual numerical values, only describe relative trends
11. Do not reuse previous sentence structures – use new wording and phrasing
12. Do not explain the reasoning – only output the final revised summary
"""
}

# ✅ LangGraph 노드 함수
def streamlit_revise_table_analysis_fn(state):
    lang = state.get("lang", "한국어")
    if state.get("analysis_type", True):
        st.info("✅ [Revision Agent] 테이블 분석 요약 수정 시작" if lang == "한국어" else "✅ [Revision Agent] Start table analysis revision")

    # 📌 table_analysis는 revised_history가 있으면 마지막 것을, 없으면 초안을 fallback
    report_to_modify = state.get("revised_analysis_history", [state.get("table_analysis", "")])[-1]

    prompt = REVISION_PROMPT[lang].format(
        linearized_table=state["linearized_table"],
        ft_test_summary=str(state["ft_test_summary"]),
        anchor=state["anchor"],
        report_to_modify=report_to_modify,
        feedback=state["feedback"]
    )

    if state.get("analysis_type", True):
        with st.spinner("LLM이 수정 보고서를 작성 중..." if lang == "한국어" else "LLM is drafting the revised summary..."):
            response = llm.invoke(prompt)
    else:
        response = llm.invoke(prompt)

    new_revised_analysis = response.content.strip()

    # Append to revision history
    revision_history = state.get("revised_analysis_history", [])
    revision_history.append(new_revised_analysis)

    if state.get("analysis_type", True):
        st.success("🎉 수정된 최종 보고서:" if lang == "한국어" else "🎉 Final revised report:")
        st.text(new_revised_analysis)
    # st.text_area("🪵 Revision History", "\n\n---\n\n".join(revision_history), height=300)

    return {
        **state,
        "revised_analysis": new_revised_analysis,
        "revised_analysis_history": revision_history
    }

# ✅ LangGraph 노드 등록
streamlit_revise_table_analysis_node = RunnableLambda(streamlit_revise_table_analysis_fn)