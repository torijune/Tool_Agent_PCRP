import os
import openai

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)


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

이 요약이 위의 표와 수치 분석 결과를 **크게 벗어나지 않고 전반적으로 일관성 있게** 반영하고 있는지 평가해주세요.

⚠️ 주의:
- 약간의 표현 차이, 어순 변화, 경미한 해석적 표현은 허용됩니다.
- 다만 **중요 수치, 주요 경향, 그룹 간 순위** 등 핵심적인 사실 왜곡이 있으면 reject 하세요.

🎯 평가 방식:
- 요약이 전체적으로 신뢰할 만하고 사실 기반이면 "accept"라고만 출력하세요.
- 요약에서 **명확한 사실 오류, 수치 왜곡, 잘못된 결론**이 있으면 "reject: [이유]" 형식으로 출력하세요.
"""

def hallucination_check_node_fn(state):
    print("*" * 10, "Start table analysis hallucination check", "*" * 10)
    
    hallucination_reject_num = state.get("hallucination_reject_num", 0)

    if hallucination_reject_num == 0:
        prompt = HALLUCINATION_CHECK_PROMPT.format(
            selected_question=state["selected_question"],
            linearized_table=state["linearized_table"],
            numeric_anaylsis=state["numeric_anaylsis"],
            table_analysis=state["table_analysis"]
        )
    else:
        prompt = HALLUCINATION_CHECK_PROMPT.format(
            selected_question=state["selected_question"],
            linearized_table=state["linearized_table"],
            numeric_anaylsis=state["numeric_anaylsis"],
            table_analysis=state["revised_analysis"]
        )

    response = llm.invoke(prompt)
    result = response.content.strip()

    # "reject: 이유" 혹은 "accept"
    if result.lower().startswith("reject"):
        decision = "reject"
        feedback = result[len("reject"):].strip(": ").strip()
        hallucination_reject_num = hallucination_reject_num + 1
        print("Hallucination Check 결과: ", decision)
        print("\nLLM Feedback: ", feedback)
    else:
        decision = "accept"
        print("Hallucination Check 결과: ", decision)
        feedback = ""

    return {**state, 
            "hallucination_check": decision, 
            "feedback": feedback,
            "hallucination_reject_num": hallucination_reject_num
            }

hallucination_check_node = RunnableLambda(hallucination_check_node_fn)