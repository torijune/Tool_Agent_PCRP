import os
import openai
import streamlit as st

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=api_key)

POLISHING_PROMPT = {
    "한국어": """
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
""",
    "English": """
You are a stylistic editor for statistical summaries written in Korean.

Below is a draft summary of a statistical analysis.  
If the sentences are too choppy ("~했음. ~했음." repetition), redundant, or include subjective insights, rewrite them into a more readable style **without altering their meaning**.

🎯 Strictly follow these instructions:

1. **No additions or deletions** — Do not add new interpretations, background, or causal reasoning beyond the original numeric-based content.
2. **Keep declarative tone** — Use styles like: "~was observed", "~was shown"
3. **Remove speculative insights** — Phrases like “due to health concerns” or “because they were affected” must be removed; stick only to observable facts
4. **Only include categories with statistical significance (asterisked)** in the report
5. **Eliminate and connect duplicates** — Avoid repeating the same idea (e.g., “was high”, “interest was high”); connect with transitions
6. **Avoid monotonous structure** — Don’t repeat "~was observed." repeatedly; vary structure and combine related findings into single sentences
7. **Use varied expressions** — Mix in phrases like:
   - Showed notable trend
   - Displayed clear difference
   - Exhibited relatively high values
   - Recorded the highest
8. **Avoid listing all subgroups** — Focus on concise summaries of characteristic groups
9. **Only report table-based facts** — Do not include interpretations; describe numeric trends only

📝 Original draft:
{raw_summary}

---

🎯 Polished final summary:
"""
}

def streamlit_sentence_polish_fn(state):
    lang = state.get("lang", "한국어")
    st.info("✅ [Polish Agent] 문장 다듬기 시작" if lang == "한국어" else "✅ [Polish Agent] Start sentence polishing")

    hallucination_reject_num = state["hallucination_reject_num"]

    raw_summary = state["table_analysis"] if hallucination_reject_num == 0 else state["revised_analysis"]

    with st.spinner("LLM이 문장을 다듬는 중..." if lang == "한국어" else "LLM is polishing the summary..."):
        response = llm.invoke(POLISHING_PROMPT[lang].format(raw_summary=raw_summary))

    polishing_result = response.content.strip()

    st.text("### ✅ 최종 보고서" if lang == "한국어" else "### ✅ Final Report")
    st.success("🎉 다듬어진 최종 요약문:" if lang == "한국어" else "🎉 Polished Final Summary:")
    st.text(polishing_result)

    return {**state, "polishing_result": polishing_result}

streamlit_sentence_polish_node = RunnableLambda(streamlit_sentence_polish_fn)