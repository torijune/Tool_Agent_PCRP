import os
import openai

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

ANSWER_PROMPT = """
당신은 유능한 AI 비서입니다.

사용자의 질문은 다음과 같습니다:
"{query}"

아래는 관련된 논문 검색 결과입니다:

{retrieved_doc}

위 논문 정보를 참고하여 사용자 질문에 대해 정확하고 간결한 답변을 생성해주세요.
"""

def answer_gen_node(state: dict) -> dict:
    query = state["query"]
    retrieved_doc = state.get("retrieved_doc", "")

    print("💬 Answer Generation 시작")
    print(f"📝 사용자 질문:\n{query}")
    print(f"📄 검색된 논문 요약 (미리보기):\n{retrieved_doc[:300]}...")

    response = llm.invoke(ANSWER_PROMPT.format(query=query, retrieved_doc=retrieved_doc))
    generated_answer = response.content.strip()

    print(f"✅ 생성된 답변:\n{generated_answer}")
    print("-" * 60)

    return {**state, "generated_answer": generated_answer}

answer_gen_node = RunnableLambda(answer_gen_node)