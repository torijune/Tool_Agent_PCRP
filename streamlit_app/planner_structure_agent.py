from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(temperature=0.3, model="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))

STRUCTURE_PLANNING_PROMPT = {
    "한국어": """
당신은 설문조사 설계를 지원하는 전문가입니다. 아래 조사 주제와 목적, 응답자 정보를 참고하여 설문조사의 전체 구조(섹션)를 제안해주세요.

다음 지침을 따르세요:
- 각 섹션은 논리적인 흐름을 가져야 함 (예: 일반 → 구체 → 민감)
- 각 섹션의 목적을 한 줄로 설명해주세요
- 총 3~5개 섹션으로 구성하는 것이 이상적
- 설문 흐름은 응답자의 피로도를 고려한 순서여야 함

📌 조사 주제: {topic}
📌 조사 목적: {objective}
📌 타겟 응답자 정보: {audience}

---

📑 설문 구조 제안:
""",

    "English": """
You are an expert in survey design. Based on the topic, objective, and target audience, propose a logical section structure for the survey.

Guidelines:
- Sections should follow a logical order (e.g., general → specific → sensitive)
- Briefly describe the purpose of each section
- 3 to 5 sections is ideal
- Consider respondent fatigue in your suggested flow

📌 Topic: {topic}
📌 Objective: {objective}
📌 Target Audience: {audience}

---

📑 Suggested Survey Structure:
"""
}

# ✅ LangGraph-compatible Node Function
def planner_structure_agent_fn(state):
    topic = state["topic"]
    objective = state["objective"]
    audience = state["audience"]
    lang = state.get("lang", "한국어")

    prompt = STRUCTURE_PLANNING_PROMPT[lang].format(topic=topic, objective=objective, audience=audience)
    response = llm.invoke(prompt)
    return {
        **state,
        "structure": response.content.strip()
    }

structure_agent_node = RunnableLambda(planner_structure_agent_fn)