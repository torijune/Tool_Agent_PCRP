import os
import openai
import streamlit as st

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

POLISHING_PROMPT = """
당신은 통계 데이터를 바탕으로 작성된 한국어 보고서를 다듬는 문체 전문 에디터입니다.

아래는 통계 분석 결과를 요약한 초안입니다.  
문장이 단절적이거나(~했음. ~했음 반복), 표현이 중복되거나, 불필요한 인사이트가 포함되어 있다면, **의미를 변경하지 않고** 더 읽기 쉬운 문장으로 다듬으세요.

🎯 다음 지침을 엄격히 따르세요:

1. **내용 추가, 삭제 금지** — 수치 기반의 원문 정보에서 벗어나는 새로운 해석, 배경 설명, 인과관계 유추는 모두 금지
2. **'음슴체' 스타일 유지** — 예: ~했음, ~로 나타났음
3. **인사이트 제거** — ‘건강에 민감해서’, ‘직접 영향을 받아서’ 등 주관적 추론은 모두 제거하고, 표로부터 드러나는 사실만 유지
4. **통계적으로 유의한 항목(별표 포함된 대분류)**만 문장에 포함되었는지 확인할 것
5. **중복 표현 제거 및 연결** — 동일 의미의 표현 반복("높게 나타났음", "관심이 높았음")은 피하고 연결어를 통해 간결하게 정리
6. **단조로운 나열 피하기** — ~했음. ~했음. 반복하지 말고, 문장 구조를 다양화하고 연관된 항목은 한 문장으로 묶기
7. **다양한 표현 혼용** — 아래와 같은 표현을 적절히 섞어 사용할 것:
   - 두드러진 경향 보였음
   - 뚜렷한 차이를 나타냈음
   - 상대적으로 높은 값을 보였음
   - 가장 높게 확인됐음
8. **불필요한 소분류 또는 모든 그룹 나열 금지** — 요약은 특징적인 그룹 중심으로 간결하게 작성할 것
9. **표 기반 사실만 요약** — 수치 기반 경향만 전달하고, 해석은 포함하지 말 것

📝 기존 요약:
{raw_summary}

---

🎯 다듬어진 최종 요약문:
"""

def streamlit_sentence_polish_fn(state):
    st.info("✅ [Polish Agent] Start sentence polishing")

    hallucination_reject_num = state["hallucination_reject_num"]

    raw_summary = state["table_analysis"] if hallucination_reject_num == 0 else state["revised_analysis"]

    with st.spinner("LLM Polish Agent가 문장을 다듬는 중..."):
        response = llm.invoke(POLISHING_PROMPT.format(raw_summary=raw_summary))

    polishing_result = response.content.strip()

    st.markdown("### ✅ Final Report")
    st.success("🎉 다듬어진 최종 요약문:")
    st.markdown(polishing_result)

    return {**state, "polishing_result": polishing_result}

streamlit_sentence_polish_node = RunnableLambda(streamlit_sentence_polish_fn)