from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(temperature=0.3, model="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))

INTRO_ANALYSIS_PROMPT = {
    "한국어": """
당신은 전문 조사 기획자입니다. 사용자가 제공한 조사 주제에 따라 적절한 조사 목적을 요약하고 명확히 해주세요.

다음 내용을 참고하여 작성하세요:
- 조사 목적은 구체적이고 측정 가능해야 합니다.
- 조사 주제에서 파생되는 인사이트와 데이터 활용 방향도 간단히 언급해주세요.

📌 사용자 입력 조사 주제:
{topic}

---

🎯 조사 목적:
""",

    "English": """
You are a professional survey designer. Based on the given research topic, write a clear and concise survey objective.

Please follow these rules:
- The objective should be specific and measurable.
- Briefly mention what insights this survey could provide and how the data might be used.

📌 Research Topic:
{topic}

---

🎯 Survey Objective:
"""
}

# ✅ LangGraph-compatible Node Function
def planner_intro_agent_fn(state):
    topic = state["topic"]
    lang = state.get("lang", "한국어")

    prompt = INTRO_ANALYSIS_PROMPT[lang].format(topic=topic)
    response = llm.invoke(prompt)
    return {
        **state,
        "objective": response.content.strip()
    }

intro_agent_node = RunnableLambda(planner_intro_agent_fn)