import os
import openai
import streamlit as st

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=api_key)

HYPOTHESIS_PROMPT = {
    "한국어": """
당신은 통계 데이터를 해석하는 데이터 과학자입니다.
아래는 분석할 표의 row명 (index)과 column명입니다.

row: {row_names}
column: {column_names}

당신의 임무는, 사용자의 질문 ("{selected_question}")과 관련해  
데이터에서 확인할 수 있을 법한 가설(패턴, 관계)을 2~5개 정도 제안하는 것입니다.

예시:
1. 연령대가 높을수록 관심도가 높을 것이다.
2. 기저질환이 있는 경우 관심도가 높을 것이다.

- 데이터 기반으로 합리적인 가설만 생성할 것
- 외부 지식은 절대 사용 금지
- 문장 길이는 짧고, 번호 리스트로 작성
""",
    "English": """
You are a data scientist interpreting statistical tables.
Below are the row names (index) and column names of the table to be analyzed.

row: {row_names}
column: {column_names}

Your task is to propose 2 to 5 hypotheses (patterns or relationships) relevant to the user's question ("{selected_question}") that could be inferred from the data.

Example:
1. Older age groups may show higher interest.
2. Those with chronic illnesses may show higher concern.

- Only propose reasonable hypotheses based on the data
- Do not use external knowledge
- Keep sentences short and format as a numbered list
"""
}

def streamlit_hypothesis_generate_fn(state):
    if state.get("analysis_type", True):
        st.info("✅ [Hypothesis Agent] Start hypothesis generation")
    selected_table = state["selected_table"]
    selected_question = state["selected_question"]

    # ✅ row와 column name 추출
    if "대분류" in selected_table.columns and "소분류" in selected_table.columns:
        selected_table["row_name"] = selected_table["대분류"].astype(str) + "_" + selected_table["소분류"].astype(str)
        row_names = selected_table["row_name"].dropna().tolist()
    else:
        row_names = list(selected_table.index)

    column_names = list(selected_table.columns)

    row_names_str = ", ".join(map(str, row_names))
    column_names_str = ", ".join(map(str, column_names))

    # ✅ Streamlit - Table Overview 블록
    if state.get("analysis_type", True):
        with st.container():
            st.markdown("### ✅ 테이블 개요" if state.get("lang", "한국어") == "한국어" else "### ✅ Table Overview")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 📝 행 이름" if state.get("lang", "한국어") == "한국어" else "#### 📝 Row Names")
                preview_rows = ", ".join(row_names[:5]) + " ..." if len(row_names) > 5 else row_names_str
                st.markdown(f"**{'미리보기' if state.get('lang', '한국어') == '한국어' else 'Preview'}:** {preview_rows}")
                with st.expander("📋 전체 Row Names 보기"):
                    st.markdown(row_names_str)

            with col2:
                st.markdown("#### 📝 열 이름" if state.get("lang", "한국어") == "한국어" else "#### 📝 Column Names")
                preview_columns = ", ".join(column_names[:5]) + " ..." if len(column_names) > 5 else column_names_str
                st.markdown(f"**{'미리보기' if state.get('lang', '한국어') == '한국어' else 'Preview'}:** {preview_columns}")
                with st.expander("📋 전체 Column Names 보기"):
                    st.markdown(column_names_str)

    lang = state.get("lang", "한국어")

    # ✅ LLM 호출
    prompt = HYPOTHESIS_PROMPT[lang].format(
        row_names=row_names_str,
        column_names=column_names_str,
        selected_question=selected_question
    )

    if state.get("analysis_type", True):
        with st.spinner("Generating hypotheses..." if lang == "English" else "가설 생성 중..."):
            response = llm.invoke(prompt)
    else:
        response = llm.invoke(prompt)

    hypotheses = response.content.strip()

    # ✅ Hypothesis 블록 → 바로 전체 출력
    if state.get("analysis_type", True):
        with st.container():
            st.markdown("### ✅ 생성된 가설" if lang == "한국어" else "### ✅ Generated Hypotheses")
            st.markdown(hypotheses)

    return {**state, "generated_hypotheses": hypotheses}

streamlit_hypothesis_generate_node = RunnableLambda(streamlit_hypothesis_generate_fn)