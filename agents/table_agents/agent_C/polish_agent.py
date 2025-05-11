import os
import openai

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

POLISHING_PROMPT = """
당신은 한국어 데이터 리포트의 문체와 문장 흐름을 다듬는 전문 에디터입니다.

아래는 통계 데이터를 기반으로 작성된 요약문입니다.  
문장이 너무 단절적 (~했음. ~했음. 반복) 이거나, 의미가 중복되거나, 어색하게 나열된 부분이 있다면, 의미를 바꾸지 않고 자연스럽고 읽기 쉽게 개선할 것.

✅ 반드시 지켜야 할 규칙
1. 내용 추가, 삭제 절대 금지
2. '음슴체' 스타일 유지 (예: ~했음, ~로 나타났음)
3. 의미상 유사하거나 연관된 그룹은 연결어(그리고, 또한, ~와 같이)를 활용해 한 문장으로 묶을 것
4. 단조로운 문장 (~했음. ~했음. 반복)을 피하고, 문장 구조를 다양하게 조합할 것
5. 동일 의미 표현 반복 (“더 높았음”, “높게 나타났음”, “높은 관심이 나타났음”)을 피하고, 다음과 같이 다양한 표현을 섞어 쓸 것:
   - 두드러진 경향 보였음
   - 뚜렷한 차이를 나타냈음
   - 관심이 가장 두드러졌음
   - 상대적으로 높은 값을 보였음
   - ~에서 가장 높게 확인됐음
6. 중복 표현은 과감하게 제거하여 가독성을 높일 것
7. 통일성 있게 간결하고 명확한 문장으로 작성할 것

📝 기존 요약:
{raw_summary}

---

🎯 개선된 최종 요약문:
"""


def sentence_polish_fn(state):
    print("*" * 10, "Start sentence polishing", "*" * 10)

    hallucination_reject_num = state["hallucination_reject_num"]
    
    if hallucination_reject_num == 0:
        response = llm.invoke(POLISHING_PROMPT.format(
            raw_summary = state["table_analysis"]
        ))
    else:
        response = llm.invoke(POLISHING_PROMPT.format(
            raw_summary = state["revised_analysis"]
        ))

    polishing_result = response.content.strip()

    return {**state, "polishing_result": polishing_result}

sentence_polish_node = RunnableLambda(sentence_polish_fn)