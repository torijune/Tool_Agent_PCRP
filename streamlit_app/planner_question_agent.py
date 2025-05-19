from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(temperature=0.3, model="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))

QUESTION_SUGGESTION_PROMPT = {
    "한국어": """
당신은 전문 설문조사 기획자입니다. 다음 조사 정보를 기반으로 각 설문 섹션별 대표 문항을 제안해주세요.

지침:
- 각 섹션마다 2~3개의 문항을 제안해주세요
- 각 문항에는 괄호 안에 질문 유형도 함께 제시 (예: 객관식, 5점 척도, 주관식 등)
- 이중 질문, 편향 표현, 모호한 질문은 피하세요
- 문항은 응답자가 이해하기 쉬운 표현으로 구성되어야 합니다

📌 조사 주제: {topic}
📌 조사 목적: {objective}
📌 타겟 응답자: {audience}
📌 설문 구조:
{structure}

---

✍️ 섹션별 추천 문항:
""",

    "English": """
You are a professional survey planner. Based on the following survey details, suggest key questions for each section.

Guidelines:
- Propose 2–3 questions per section
- Indicate the question type in parentheses (e.g., Multiple Choice, Likert Scale, Open-ended)
- Avoid double-barreled, biased, or vague questions
- Make the wording simple and easy to understand

📌 Topic: {topic}
📌 Objective: {objective}
📌 Target Audience: {audience}
📌 Survey Structure:
{structure}

---

✍️ Suggested Questions by Section:
"""
}

# ✅ LangGraph-compatible Node Function
def planner_question_agent_fn(state):
    topic = state["topic"]
    objective = state["objective"]
    audience = state["audience"]
    structure = state["structure"]
    lang = state.get("lang", "한국어")

    prompt = QUESTION_SUGGESTION_PROMPT[lang].format(
        topic=topic,
        objective=objective,
        audience=audience,
        structure=structure
    )
    response = llm.invoke(prompt)
    return {
        **state,
        "questions": response.content.strip()
    }

question_agent_node = RunnableLambda(planner_question_agent_fn)