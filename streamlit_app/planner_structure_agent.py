from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini", openai_api_key=os.getenv("OPENAI_API_KEY"))

STRUCTURE_PLANNING_PROMPT = {
    "한국어": """
당신은 고급 설문조사 설계 전문가입니다. 아래 조사 주제, 목적, 타겟 응답자 정보를 바탕으로 구조화된 설문 문항을 설계하세요.

다음의 Chain of Thought를 순차적으로 따라가며 사고하고 설계하세요:

Step 1️⃣: 조사 목적에서 측정하고자 하는 핵심 개념 또는 변수들을 추출  
Step 2️⃣: 타겟 응답자의 특성과 맥락을 고려하여, 응답자가 이해하고 응답하기 쉬운 방식으로 구성할 수 있는 문항 유형을 판단  
Step 3️⃣: 각 핵심 개념에 대응되는 구체적인 문항을 설계하고, 질문 유형을 괄호로 표시 (예: 객관식, 리커트 척도, 주관식 등)  
Step 4️⃣: 질문 간 논리적 흐름이 자연스럽도록 배열하고, 중복되거나 유도적인 질문은 제거  
Step 5️⃣: 각 문항 옆에 그 문항이 조사 목적에서 어떤 기능을 수행하는지를 주석처럼 간략히 설명

📌 조사 주제: {topic}  
📌 조사 목적: {generated_objective}  
📌 타겟 응답자 정보: {audience}

---

✍️ 구조화된 설문 문항 목록:
""",

    "English": """
You are a professional survey design expert. Based on the topic, objective, and audience, design a structured list of survey questions.

Follow the step-by-step Chain of Thought reasoning below to construct meaningful questions:

Step 1️⃣: Identify core concepts or constructs derived from the survey objective  
Step 2️⃣: Consider the characteristics and context of the target audience to select suitable question formats  
Step 3️⃣: Draft specific questions for each concept, annotating question type (e.g., Multiple Choice, Likert Scale, Open-ended)  
Step 4️⃣: Organize questions logically to minimize fatigue and avoid leading or redundant items  
Step 5️⃣: Add brief annotations to each question to clarify its role in the overall research purpose

📌 Topic: {topic}  
📌 Objective: {generated_objective}  
📌 Target Audience: {audience}

---

✍️ Structured Survey Questions:
"""
}

# ✅ LangGraph-compatible Node Function
def planner_structure_agent_fn(state):
    topic = state["topic"]
    generated_objective = state["generated_objective"]
    audience = state["audience"]
    lang = state.get("lang", "한국어")

    prompt = STRUCTURE_PLANNING_PROMPT[lang].format(topic=topic, generated_objective=generated_objective, audience=audience)
    response = llm.invoke(prompt)
    import streamlit as st
    st.markdown("### 🧱 설문 구조 (Survey Structure)" if lang == "한국어" else "### 🧱 Survey Structure")
    st.code(response.content.strip(), language="markdown")
    return {
        **state,
        "structure": response.content.strip()
    }

structure_agent_node = RunnableLambda(planner_structure_agent_fn)