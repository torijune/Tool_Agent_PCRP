import os
import openai

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)


Responder_PROMPT = """당신은 유능한 AI 비서입니다.

아래는 사용자의 요청에 대한 전체 처리 과정입니다:

질문: {query}

수립된 계획 (도구 선택 이유 포함): {plan}

도구 실행 결과: {tool_result}

평가 결과 (도구 결과의 신뢰성 등): {decision}

---

이제 다음의 내부 사고 과정을 거쳐, 사용자에게 전달할 **최종 응답만** 작성하세요. 사고 과정은 출력하지 말고 응답 품질 향상을 위한 내부 판단에만 사용하세요:

1. 사용자의 질문을 다시 한 번 이해합니다.
2. 왜 이 계획(plan)이 적절한지 판단합니다.
3. 도구 결과(tool_result)의 핵심 정보를 요약합니다.
4. 평가(decision) 결과가 응답에 어떤 영향을 주는지 고려합니다.

위 사항들을 종합하여 사용자에게 제공할 친절하고 정확한 **최종 응답만 출력하세요**.
"""

def responder_fn(state: dict) -> dict:
    query = state.get("query", "")
    plan = state.get("plan", "")
    tool_result = state.get("tool_result", "")
    decision = state.get("decision", "")

    response = llm.invoke(
        Responder_PROMPT.format(
            query=query,
            plan=plan,
            tool_result=tool_result,
            decision=decision,
        )
    )

    return {**state, "final_answer": response.content}

responder_node = RunnableLambda(responder_fn)