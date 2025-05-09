import os
import openai

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)


HALLUCINATION_CHECK_PROMPT = """
당신은 통계 해석 결과를 검증하는 전문가입니다.

아래의 테이블 데이터와 수치 분석 결과, 그리고 해당 테이블을 기반으로 생성된 요약 결과가 주어집니다.

📝 설문 문항:
{selected_question}

📊 선형화된 테이블:
{linearized_table}

📈 수치 분석 결과:
{numeric_anaylsis}

🧾 생성된 요약:
{table_analysis}

이 요약이 위의 표와 수치 분석 결과를 정확히 반영하고 있는지 평가해주세요.

- 표에서 유추할 수 없는 근거 없는 내용이 있다면 "reject: [이유]" 형식으로 출력하세요.
- 만약 요약이 충분히 객관적이고 수치 기반이면 "accept"라고만 출력하세요.
"""

def hallucination_check_node_fn(state):
    print("*" * 10, "Start table analysis hallucination check", "*" * 10)
    prompt = HALLUCINATION_CHECK_PROMPT.format(
        selected_question=state["selected_question"],
        linearized_table=state["linearized_table"],
        numeric_anaylsis=state["numeric_anaylsis"],
        table_analysis=state["table_analysis"]
    )

    response = llm.invoke(prompt)
    result = response.content.strip()

    # "reject: 이유" 혹은 "accept"
    if result.lower().startswith("reject"):
        decision = "reject"
        feedback = result[len("reject"):].strip(": ").strip()
        print("Hallucination Check 결과: ", decision)
        print("\nLLM Feedback: ", feedback)
    else:
        decision = "accept"
        print("Hallucination Check 결과: ", decision)
        feedback = ""

    return {**state, "hallucination_check": decision, "feedback": feedback}

hallucination_check_node = RunnableLambda(hallucination_check_node_fn)