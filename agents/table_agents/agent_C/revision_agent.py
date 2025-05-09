import os
import openai

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)


REVISION_PROMPT = """
다음은 테이블 분석 결과에 대해 일부 잘못된 해석이 포함된 요약입니다. 아래의 피드백을 참고하여 잘못된 내용을 제거하고, 원본 데이터를 기반으로 다시 작성해주세요.

📝 설문 문항: {selected_question}

📊 선형화된 테이블:
{linearized_table}

📈 수치 분석 결과:
{numeric_anaylsis}

🧾 기존 요약 (잘못된 부분 포함):
{table_analysis}

❗ 피드백 (수정이 필요한 이유 또는 잘못된 부분):
{feedback}

📌 수정 조건:
- 피드백에 따라 잘못된 정보를 제거하거나 보완해주세요.
- 가능한 한 수치 기반의 객관적인 해석으로 서술해주세요.
- 1~2개의 간결한 단락으로 작성해주세요.
"""

def revise_table_analysis_fn(state):
    print("*" * 10, "Start table analysis revision", "*" * 10)
    prompt = REVISION_PROMPT.format(
        selected_question=state["selected_question"],
        linearized_table=state["linearized_table"],
        numeric_anaylsis=state["numeric_anaylsis"],
        table_analysis=state["table_analysis"],
        feedback=state.get("feedback", "피드백 없음")
    )

    response = llm.invoke(prompt)
    revised_analysis = response.content.strip()

    return {**state, "revised_analysis": revised_analysis }

revise_table_analysis = RunnableLambda(revise_table_analysis_fn)