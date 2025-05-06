import os
import openai
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Critic LLM 설정: 적당한 다양성과 판단 허용을 위해 temperature = 0.5
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

# ✅ 판단 기준을 강화한 Critic Prompt
CRITIC_PROMPT = """
You are a critical evaluator of an LLM-based agent system.
Your task is to decide whether the tool's result sufficiently answers the user query, in accordance with the plan.

Respond with:
- "accept" if the tool result is correct, relevant, and matches the user's intent.
- "reject" if the result is incorrect, incomplete, or unrelated.

Only return one word: accept or reject.

Query: {query}
Plan: {plan}
Tool Result: {tool_result}
"""

def critic_fn(state: dict) -> dict:
    query = state.get("query", "")
    plan = state.get("plan", "")
    result = state.get("tool_result", "")
    
    # ✅ 전체 입력 로그 확인용
    # print("\n--- Critic Input ---")
    # print(f"Query: {query}")
    # print(f"Plan: {plan}")
    # print(f"Tool Result: {result}")
    
    response = llm.invoke(CRITIC_PROMPT.format(query=query, plan=plan, tool_result=result))
    decision = response.content.strip().lower()

    # print("🔍 Critic Decision:", decision)

    # ✅ fail-safe: 허용된 값 외의 출력은 강제 reject
    if decision not in ["accept", "reject"]:
        decision = "reject"

    return {**state, "decision": decision}

critic_node = RunnableLambda(critic_fn)