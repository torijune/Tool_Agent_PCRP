import os
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

HALLUCINATION_PROMPT = """당신은 정확한 정보를 판단하는 전문가입니다.

다음은 사용자 질문(query), 그에 대한 검색된 논문 정보(retrieved_doc), 그리고 그 정보를 기반으로 생성된 AI의 응답(answer)입니다.

질문:
{query}

검색된 논문 요약:
{retrieved_doc}

AI 응답:
{answer}

위의 AI 응답이 검색된 논문 요약(retrieved_doc)에 명확하게 근거하고 있으면 'accept'라고 출력하고, 근거 없이 생성된 내용(hallucination)이 포함되어 있다면 'reject'라고 출력하세요.

단답으로 only 'accept' 또는 'reject'만 출력하세요.
"""

def hallucination_check_node(state: dict) -> dict:
    query = state["query"]
    retrieved_doc = state["retrieved_doc"]
    answer = state["generated_answer"]

    print("🧠 Hallucination Check 시작")
    print(f"❓ 사용자 질문:\n{query}")
    print(f"📄 검색된 논문 요약 (미리보기):\n{retrieved_doc[:300]}...")
    print(f"💬 AI 응답:\n{answer}")

    decision = llm.invoke(
        HALLUCINATION_PROMPT.format(query=query, retrieved_doc=retrieved_doc, answer=answer)
    ).content.strip().lower()

    print(f"✅ 판단 결과: {decision}")
    print("-" * 60)

    return {**state, "hallucination_decision": decision}

hallucination_check_node = RunnableLambda(hallucination_check_node)