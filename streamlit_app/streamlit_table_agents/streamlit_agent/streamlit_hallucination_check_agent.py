import os
import openai
import streamlit as st

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

# ✅ 환경 변수 로드 및 API 키 설정
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ LLM 설정
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

# ✅ 프롬프트 정의 (ft_test_summary 사용)
HALLUCINATION_CHECK_PROMPT = """
당신은 통계 해석 결과를 검증하는 전문가입니다.

아래의 테이블 데이터와 수치 분석 결과, 그리고 해당 테이블을 기반으로 생성된 요약 결과가 주어집니다.

📝 설문 문항:
{selected_question}

📊 선형화된 테이블:
{linearized_table}

📈 수치 분석 결과 (F/T-test 결과 요약):
{ft_test_summary}

🧾 생성된 요약:
{table_analysis}

이 요약이 위의 표와 수치 분석 결과를 **크게 벗어나지 않고 전반적으로 일관성 있게** 반영하고 있는지 평가해주세요.

⚠️ 주의:
- 약간의 표현 차이, 어순 변화, 경미한 해석적 표현은 허용됩니다.
- 다만 **중요 수치, 주요 경향, 그룹 간 순위** 등 핵심적인 사실 왜곡이 있으면 reject 하세요.

🎯 평가 방식:
- 요약이 전체적으로 신뢰할 만하고 사실 기반이면 "accept"라고만 출력하세요.
- 요약에서 **명확한 사실 오류, 수치 왜곡, 잘못된 결론**이 있으면 "reject: [이유]" 형식으로 출력하세요.
"""

# ✅ LangGraph-compatible hallucination 체크 노드
def streamlit_hallucination_check_node_fn(state):
    st.info("✅ [Hallucination Check Agent] Start hallucination evaluation")

    hallucination_reject_num = state.get("hallucination_reject_num", 0)

    # 🔁 수정 여부에 따라 분석 결과 선택
    table_analysis = (
        state["table_analysis"]
        if hallucination_reject_num == 0
        else state["revised_analysis"]
    )

    # ✅ 프롬프트 생성
    prompt = HALLUCINATION_CHECK_PROMPT.format(
        selected_question=state["selected_question"],
        linearized_table=state["linearized_table"],
        ft_test_summary=str(state["ft_test_summary"]),  # ✅ 여기서 ft_test_summary 사용
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

# ✅ LangGraph 노드 등록
streamlit_hallucination_check_node = RunnableLambda(streamlit_hallucination_check_node_fn)