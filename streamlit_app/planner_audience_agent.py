from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(temperature=0.3, model="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))

AUDIENCE_ANALYSIS_PROMPT = {
    "한국어": """
당신은 설문조사 전문가입니다. 아래 조사 주제와 목적을 바탕으로 적절한 응답자(타겟 집단)를 정의해주세요.

다음 지침을 따르세요:
- 타겟은 연령, 성별, 거주 지역, 직업, 생활 패턴 등으로 구체화할 수 있음
- 설문 목적을 고려해 가장 의미 있는 응답 집단을 선정
- 필요한 경우 제외해야 할 집단도 명시

📌 조사 주제: {topic}
📌 조사 목적: {objective}

---

🎯 적절한 응답자(타겟 집단):
""",

    "English": """
You are a survey research expert. Based on the following topic and objective, suggest the most appropriate target respondent group.

Guidelines:
- Be specific in terms of age, gender, region, occupation, lifestyle, etc.
- Focus on which group would give the most meaningful insight
- Mention any groups that should be excluded if necessary

📌 Topic: {topic}
📌 Objective: {objective}

---

🎯 Target Audience:
"""
}

# ✅ LangGraph-compatible Node Function
def planner_audience_agent_fn(state):
    topic = state["topic"]
    objective = state["objective"]
    lang = state.get("lang", "한국어")

    prompt = AUDIENCE_ANALYSIS_PROMPT[lang].format(topic=topic, objective=objective)
    response = llm.invoke(prompt)
    return {
        **state,
        "audience": response.content.strip()
    }

audience_agent_node = RunnableLambda(planner_audience_agent_fn)