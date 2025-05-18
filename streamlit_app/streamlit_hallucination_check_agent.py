import os
import openai
import streamlit as st

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

# ✅ 환경 변수 로드 및 API 키 설정
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# ✅ LLM 설정
llm = ChatOpenAI(model="gpt-4o-mini", temperature=1.0, top_p = 0.9, openai_api_key=api_key)

HALLUCINATION_CHECK_PROMPT = """
당신은 통계 해석 결과를 검증하는 전문가입니다.

아래의 테이블 데이터와 수치 분석 결과(F/T-test 기반), 그리고 해당 결과를 바탕으로 작성된 요약 보고서가 주어집니다.

📝 설문 문항:
{selected_question}

📊 선형화된 테이블:
{linearized_table}

📈 수치 분석 결과 (F/T-test 결과 요약):
{ft_test_summary}

🧾 생성된 요약:
{table_analysis}

---

이 요약이 위의 수치 분석 결과를 **정확하고 일관성 있게** 반영하고 있는지 평가해주세요.

⚠️ 주의 사항 (위반 시 우선 피드백 제공, 심각한 왜곡에 한해 reject):
1. F/T-test에서 통계적으로 유의미한 차이가 확인된 대분류가 요약에 언급되지 않은 경우
2. 유의미한 차이가 확인된 대분류에서의 주요 경향이나 수치 결과가 왜곡되어 해석된 경우 (e.g. 더 높지 않은데 더 높다고 잘못 된 주장을 하는 경우)

🎯 평가 방식:
- 요약이 전체적으로 신뢰할 만하고 통계 결과를 잘 반영하면 "accept"
- 위 항목 위반 시 "reject: [이유]" 형식으로 출력

※ F/T-test 결과는 중요한 기준이지만, 사소한 누락은 reject 대신 피드백으로 처리해도 됩니다. 명백한 왜곡이나 중대한 누락 시에만 reject 하세요.
"""

# ✅ LangGraph-compatible hallucination 체크 노드
def streamlit_hallucination_check_node_fn(state):
    st.info("✅ [Hallucination Check Agent] Start hallucination evaluation")

    hallucination_reject_num = state.get("hallucination_reject_num", 0)

    # 🔁 수정 여부에 따라 분석 결과 선택
    if "revised_analysis_history" in state and state["revised_analysis_history"]:
        table_analysis = state["revised_analysis_history"][-1]
    else:
        table_analysis = state["table_analysis"]

    # ✅ 프롬프트 생성
    prompt = HALLUCINATION_CHECK_PROMPT.format(
        selected_question=state["selected_question"],
        linearized_table=state["linearized_table"],
        ft_test_summary=str(state["ft_test_summary"]),
        table_analysis=table_analysis
    )

    # ✅ LLM 호출
    with st.spinner("Hallucination 평가 중..."):
        response = llm.invoke(prompt)

    result = response.content.strip()

    # ✅ 결과 해석 및 상태 업데이트
    if result.lower().startswith("reject"):
        decision = "reject"
        feedback = result[len("reject"):].strip(": ").strip()
        hallucination_reject_num += 1
        st.warning(f"❌ Hallucination Check 결과: {decision}")
        st.info(f"💡 LLM Feedback: {feedback}")
        if "revised_analysis_history" not in state:
            state["revised_analysis_history"] = []
        state["revised_analysis_history"].append(table_analysis)
    else:
        decision = "accept"
        feedback = ""
        st.success(f"✅ Hallucination Check 결과: {decision}")

    return {
        **state,
        "hallucination_check": decision,
        "feedback": feedback,
        "hallucination_reject_num": hallucination_reject_num
    }

streamlit_hallucination_check_node = RunnableLambda(streamlit_hallucination_check_node_fn)