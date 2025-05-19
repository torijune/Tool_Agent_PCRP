from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(temperature=0.3, model="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))

ANALYSIS_SUGGESTION_PROMPT = {
    "한국어": """
당신은 데이터 분석 및 설문조사 결과 해석 전문가입니다.

다음 설문 정보에 따라 각 문항의 분석 방식과 전반적인 통계 분석 방향을 제안해주세요:
- 각 문항의 데이터 유형에 적합한 분석법 제시 (빈도 분석, 교차분석, 평균 비교 등)
- 분석 시 유의할 점 또는 제한사항도 함께 언급
- 분석 목적에 따라 활용할 수 있는 통계 기법 예시 포함

📌 조사 주제: {topic}
📌 조사 목적: {objective}
📌 설문 구조:
{structure}
📌 문항:
{questions}

---

📊 분석 제안 및 고려사항:
""",

    "English": """
You are a data analyst and survey interpretation expert.

Based on the following survey details, suggest appropriate analysis methods:
- For each question, recommend suitable methods (e.g., frequency, cross-tab, mean comparison)
- Mention considerations or limitations in the analysis
- Suggest statistical techniques relevant to the overall research goal

📌 Topic: {topic}
📌 Objective: {objective}
📌 Structure:
{structure}
📌 Questions:
{questions}

---

📊 Suggested Analysis and Considerations:
"""
}

# ✅ LangGraph-compatible Node Function
def planner_analysis_agent_fn(state):
    topic = state["topic"]
    objective = state["objective"]
    structure = state["structure"]
    questions = state["questions"]
    lang = state.get("lang", "한국어")

    prompt = ANALYSIS_SUGGESTION_PROMPT[lang].format(
        topic=topic,
        objective=objective,
        structure=structure,
        questions=questions
    )
    response = llm.invoke(prompt)
    return {
        **state,
        "analysis": response.content.strip()
    }

analysis_agent_node = RunnableLambda(planner_analysis_agent_fn)