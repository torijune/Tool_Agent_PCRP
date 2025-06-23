def rule_based_test_type_decision(columns, question_text=""):
    """
    컬럼명과 질문 텍스트를 기반으로 임의 분석/ft_test/chi_square를 rule 기반으로 판단
    """
    import re

    # 1️⃣ 임의 분석 판단: 복수 응답 또는 순위 응답 패턴 존재 여부
    multi_response_keywords = [
        "1+2", "1+2+3", "복수", "다중", "multiple", "rank", "ranking", "우선순위"
    ]
    text_to_check = (" ".join(columns) + " " + question_text).lower()
    if any(keyword.lower() in text_to_check for keyword in multi_response_keywords):
        return "manual"

    # 2️⃣ ft_test 판단 기준: 전형적인 범주형 표현이 있는 경우
    categorical_patterns = [
        # 관심도 관련
        r"전혀\s*관심", r"관심\s*없(다|는)", r"관심\s*있(다|는)", r"매우\s*관심", r"관심",

        # 만족도 관련
        r"매우\s*만족", r"만족", r"불만족", r"매우\s*불만족", r"보통",

        # 찬반 관련
        r"찬성", r"반대", r"매우\s*찬성", r"매우\s*반대", r"대체로\s*찬성", r"대체로\s*반대",

        # 중요도 관련
        r"매우\s*중요", r"중요", r"그다지\s*중요하지\s*않", r"전혀\s*중요하지\s*않",

        # 심각성 인식
        r"매우\s*심각", r"심각", r"심각하지\s*않", r"전혀\s*심각하지\s*않",

        # 빈도 관련
        r"자주", r"가끔", r"거의\s*없", r"전혀\s*없",

        # 안전성 관련
        r"안전", r"매우\s*안전", r"위험", r"매우\s*위험",

        # 인지/경험 여부
        r"들어본\s*적", r"사용한\s*적", r"경험했", r"인지",

        # 태도/의향 관련
        r"의향", r"생각", r"예정", r"계획", r"할\s*것",

        # 정도 표현
        r"매우", r"약간", r"보통", r"그다지", r"전혀"
    ]
    if any(any(re.search(pattern, col) for pattern in categorical_patterns) for col in columns):
        return "ft_test"

    # 3️⃣ 나머지는 chi_square
    return "chi_square"
import os
import openai
import streamlit as st

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

# ✅ 환경 변수 로드 및 API 키 설정
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# ✅ LLM 설정
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)


TEST_TYPE_PROMPT = """
당신은 통계 전문가입니다.

아래는 설문 응답 결과 테이블의 열 이름 목록입니다. 이 열들은 응답자들이 선택하거나 평가한 설문 문항의 결과로 구성된 통계표입니다.

당신의 임무는, 이 테이블이 **어떤 통계 검정(F/T-test 또는 Chi-square)** 에 적합한지를 판단하는 것입니다.

📋 열 이름 목록:
{column_names}

---
Let's think step by step

판단 기준:

- `ft_test` (연속형 수치 응답):
    - 문항이 1~5점 척도, 평균, 비율, 점수 등 숫자 기반으로 요약되어 있다면 F-test 또는 T-test가 적절합니다.
    - 예시 열 이름: "평균", "만족도 점수", "~% 비율", "5점 척도", "평균 점수", "관심도 평균"
    - "전혀 관심이 없다", "매우 관심 있다" 등은 실제로는 선택지이지만, 빈도나 비율로 수치화되었을 경우 → 연속형으로 판단

- `chi_square` (범주형 선택 응답):
    - 문항이 응답자들이 특정 항목을 **선택**하거나 **다중선택**한 결과일 경우, 범주형 응답으로 보고 카이제곱 검정이 적합합니다.
    - 예시 열 이름: "주요 이용시설", "선택 이유", "가장 많이 선택한 장소", "다중 응답"

❗ 오판 주의:
- 응답 선택지 이름(예: "전혀 관심 없다", "매우 관심 있다")가 열 이름에 포함되더라도, **비율, 평균 등의 수치형 요약**이면 `ft_test`로 간주합니다.
- 테이블이 전체적으로 평균값 또는 %비율 중심이면 `ft_test` 선택이 더 적절합니다.

---

📌 답변 형식: 아래의 형식처럼 선택의 이유에 대해서 답변하지 말고 "적합한 통계 검정의 방법만" 출력하세요.

- 반드시 다음 중 하나로만 답해주세요 (소문자):
    - ft_test
    - chi_square

적합한 통계 방법: (ft_test 또는 chi_square)
"""

def normalize_test_type(llm_output: str) -> str:
    if "chi" in llm_output.lower():
        return "chi_square"
    elif "ft" in llm_output.lower():
        return "ft_test"
    else:
        return "unknown"

def streamlit_test_type_decision_fn(state):
    lang = state.get("lang", "한국어")
    selected_table = state["selected_table"]

    IGNORE_COLUMNS = {"대분류", "소분류", "사례수", "row_name"}
    filtered_columns = [col for col in selected_table.columns if col not in IGNORE_COLUMNS]

    question_text = state.get("selected_question", "")
    manual_check = rule_based_test_type_decision(filtered_columns, question_text)
    if manual_check == "manual":
        return {**state, "test_type": "manual"}


    question_key = state.get("selected_key", "")
    user_analysis_plan = state.get("user_analysis_plan", {})
    user_decision = user_analysis_plan.get(question_key, {})

    if isinstance(user_decision, dict) and user_decision.get("use_stat") is False:
        return {**state, "test_type": None}

    if isinstance(user_decision, dict) and user_decision.get("test_type") in ["ft_test", "chi_square"]:
        return {**state, "test_type": user_decision["test_type"]}

    column_names_str = ", ".join(filtered_columns)

    prompt = TEST_TYPE_PROMPT.format(
        column_names=column_names_str
    )

    if state.get("analysis_type", True):
        st.info("🤖 LLM에게 적절한 통계 검정 방식을 문의합니다..." if lang == "한국어" else "🤖 Asking the LLM to determine the appropriate statistical test...")

    if state.get("analysis_type", True):
        with st.spinner("LLM 판단 중..." if lang == "한국어" else "Determining test type..."):
            response = llm.invoke(prompt)
    else:
        response = llm.invoke(prompt)

    test_type = response.content.strip()
    test_type = normalize_test_type(test_type)

    if state.get("analysis_type", True):
        st.success(f"📌 LLM 결정: `{test_type}` 검정 방식 선택됨" if lang == "한국어" else f"📌 LLM decision: `{test_type}` test selected")

    return {
        **state,
        "test_type": test_type
    }


streamlit_test_type_decision_node = RunnableLambda(streamlit_test_type_decision_fn)