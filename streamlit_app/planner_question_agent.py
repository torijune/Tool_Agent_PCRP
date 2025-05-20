from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini", openai_api_key=os.getenv("OPENAI_API_KEY"))

QUESTION_SUGGESTION_PROMPT = {
    "한국어": """
당신은 고급 설문조사 설계 전문가입니다. 아래 조사 주제, 목적, 타겟 응답자 정보를 바탕으로 의미 있는 설문 문항을 생성하세요.

다음의 Chain of Thought를 순차적으로 따라가며 사고하고 설계하세요:

Step 1️⃣: 조사 목적에서 측정하고자 하는 핵심 개념 또는 변수들을 추출  
Step 2️⃣: 타겟 응답자의 특성을 고려하여, 어떤 방식으로 문항을 구성해야 효과적일지 판단  
Step 3️⃣: 각 핵심 개념에 대응하는 구체적인 문항을 설계하되, 가능한 한 다양한 질문 형식을 활용 (객관식, 5점 척도, 서술형 등)  
Step 4️⃣: 중복/편향/모호한 문항은 제거하고, 전체 흐름이 자연스럽도록 정렬  
Step 5️⃣: 각 문항 옆에 (문항 목적 및 유형)을 주석처럼 함께 기입

📌 조사 주제: {topic}  
📌 조사 목적: {generated_objective}  
📌 조사 설계: {structure}  
📌 타겟 응답자 정보: {audience}

---

✍️ 설계된 문항 목록:
""",

    "English": """
You are an expert in survey methodology. Based on the topic, objective, and audience information below, generate thoughtful and research-aligned survey questions.

Please reason step-by-step using the following Chain of Thought:

Step 1️⃣: Extract key constructs or variables based on the survey objective  
Step 2️⃣: Consider how the target audience may interpret or respond to those constructs  
Step 3️⃣: Create diverse question types (multiple choice, 5-point Likert, open-ended) for each construct  
Step 4️⃣: Remove redundancy, bias, or vague wording, and ensure a logical progression of questions  
Step 5️⃣: Annotate each question with its purpose and format in parentheses

📌 Topic: {topic}  
📌 Objective: {generated_objective}  
📌 Structure: {structure} 
📌 Target Audience: {audience}

---

✍️ Finalized Survey Questions:
"""
}

# ✅ LangGraph-compatible Node Function
def planner_question_agent_fn(state):
    topic = state["topic"]
    generated_objective = state["generated_objective"]
    audience = state["audience"]
    structure = state["structure"]
    lang = state.get("lang", "한국어")

    prompt = QUESTION_SUGGESTION_PROMPT[lang].format(
        topic=topic,
        generated_objective=generated_objective,
        audience=audience,
        structure=structure
    )
    response = llm.invoke(prompt)
    import streamlit as st
    st.markdown("### ✍️ 섹션별 문항 제안" if lang == "한국어" else "### ✍️ Suggested Questions by Section")
    st.code(response.content.strip(), language="markdown")
    return {
        **state,
        "questions": response.content.strip()
    }

question_agent_node = RunnableLambda(planner_question_agent_fn)