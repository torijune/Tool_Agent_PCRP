from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini", openai_api_key=os.getenv("OPENAI_API_KEY"))

ANALYSIS_SUGGESTION_PROMPT = {
    "한국어": """
당신은 데이터 분석 및 설문조사 해석 전문가입니다.

다음 정보를 바탕으로 각 설문 문항에 가장 적합한 통계 분석 방법을 추천해주세요:
- 각 문항이 측정하는 개념(태도, 행동, 인식 등)에 따라 적절한 분석 기법을 제시
- 응답 유형(객관식, 리커트 척도, 주관식 등)을 고려하여 적합한 통계 분석 또는 검정 방법(빈도분석, 교차분석, t-test, ANOVA, 상관분석 등)을 설명
- 문항별 추천 이유와 함께 분석 시 유의해야 할 점도 간단히 기술
- 전체 조사 목적과의 연관성도 반영

📌 조사 주제: {topic}
📌 조사 목적: {generated_objective}
📌 문항 목록:
{questions}

---

📊 문항별 분석 제안:
""",

    "English": """
You are a data analyst and survey interpretation expert.

Based on the following information, recommend the most appropriate statistical analysis or test method for each survey question:
- Consider the conceptual focus of each question (e.g., attitude, behavior, awareness)
- Suggest analysis methods (e.g., frequency, cross-tabulation, t-test, ANOVA, correlation) that match the question type (multiple choice, Likert scale, open-ended)
- For each question, explain why the method is appropriate and what the user should be cautious about
- Align the analysis plan with the overall research objective

📌 Topic: {topic}
📌 Objective: {generated_objective}
📌 Question List:
{questions}

---

📊 Suggested Statistical Methods for Each Question:
"""
}

# ✅ LangGraph-compatible Node Function
def planner_analysis_agent_fn(state):
    topic = state["topic"]
    generated_objective = state["generated_objective"]
    structure = state["structure"]
    questions = state["questions"]
    lang = state.get("lang", "한국어")

    prompt = ANALYSIS_SUGGESTION_PROMPT[lang].format(
        topic=topic,
        generated_objective=generated_objective,
        structure=structure,
        questions=questions
    )
    response = llm.invoke(prompt)
    import streamlit as st
    st.markdown("### 📊 분석 제안 및 고려사항" if lang == "한국어" else "### 📊 Suggested Analysis and Considerations")
    st.code(response.content.strip(), language="markdown")
    return {
        **state,
        "analysis": response.content.strip()
    }

analysis_agent_node = RunnableLambda(planner_analysis_agent_fn)