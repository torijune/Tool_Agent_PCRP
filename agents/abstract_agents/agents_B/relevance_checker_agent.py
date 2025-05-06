from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 프롬프트 템플릿
RELEVANCE_PROMPT = """
당신은 논문 검색 시스템의 평가자입니다.
아래의 사용자 질문과 검색된 논문 정보가 주어졌을 때, 검색된 논문들이 사용자의 질문과 관련이 있는지 판단해주세요.

[사용자 질문]
{query}

[검색된 논문 요약]
{retrieved_doc}

이 논문들이 사용자 질문에 '직접적으로 관련이 있다면' "accept", '연관성이 부족하거나 틀린 방향이라면' "reject"라고 단독으로 출력해주세요.
"""

def relevance_check_node(state: dict) -> dict:
    query = state["query"]
    retrieved_doc = state.get("retrieved_doc", "")

    print("🧠 Relevance Check 시작")
    print(f"📝 사용자 질문:\n{query}")
    print(f"📄 검색된 논문 요약 (미리보기):\n{retrieved_doc[:300]}...")
    
    # LLM에게 판단 요청
    response = llm.invoke(RELEVANCE_PROMPT.format(query=query, retrieved_doc=retrieved_doc))
    decision = response.content.strip().lower()

    print(f"✅ 판단 결과: {decision}")
    print("-" * 60)

    # 결과 반환
    return {**state, "relevance_decision": decision}

relevance_check_node = RunnableLambda(relevance_check_node)