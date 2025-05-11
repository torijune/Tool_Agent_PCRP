import os
import openai

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

POLISHING_PROMPT = """
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
"""

def hypothesis_generate_fn(state):
    selected_table = state["selected_table"]
    selected_question = state["selected_question"]

    print("*" * 10, "Start hypothesis generation", "*" * 10)

    # ✅ row와 column name 추출 (대분류 + 소분류 조합)
    if "대분류" in selected_table.columns and "소분류" in selected_table.columns:
        selected_table["row_name"] = selected_table["대분류"].astype(str) + "_" + selected_table["소분류"].astype(str)
        row_names = selected_table["row_name"].dropna().tolist()
    else:
        # 대분류/소분류 없을 경우 index 사용
        row_names = list(selected_table.index)

    column_names = list(selected_table.columns)

    # ✅ row, column 이름을 문자열로 변환
    row_names_str = ", ".join(map(str, row_names))
    column_names_str = ", ".join(map(str, column_names))
    print("\n 주어진 rows: ", row_names_str)
    print("\n 주어진 columns: ", column_names_str)

    # ✅ LLM 호출
    response = llm.invoke(POLISHING_PROMPT.format(
        row_names=row_names_str,
        column_names=column_names_str,
        selected_question=selected_question
    ))

    hypotheses = response.content.strip()

    print(("\n=== 생성된 가설 ===\n"), hypotheses)
    # ✅ 결과 저장
    return {**state, "generated_hypotheses": hypotheses}

hypothesis_generate_node = RunnableLambda(hypothesis_generate_fn)