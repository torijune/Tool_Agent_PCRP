import os
import openai
import json
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda
from agents.tools_schema import tools_schema

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# 🔧 최신 도구 설명이 포함된 function_call 기반 모델 생성
llm = ChatOpenAI(
    model="gpt-4o",  # function calling 지원 모델
    temperature=0.2,
    model_kwargs={"functions": tools_schema}
)

# ✅ 프롬프트 수정: 도구 이름을 직접 쓰는 대신 함수 설명 기반으로 선택 유도
PLANNER_PROMPT = """
You are a smart tool-planning assistant. Based on the user query, select the best tool and explain your choice in the `reason` field.

Use the function schema provided to you.

Return only a function_call to `use_tool` with:
- tool_name: the selected tool (as defined in the schema)
- reason: short justification
"""

def planner_fn(state: dict) -> dict:
    query = state["query"]
    messages = [
        {"role": "system", "content": PLANNER_PROMPT.strip()},
        {"role": "user", "content": query}
    ]

    # ⏬ 함수 호출 유도
    response = llm.invoke(messages)
    function_call = response.additional_kwargs.get("function_call", {})

    try:
        arguments_raw = function_call.get("arguments", "{}")
        arguments = json.loads(arguments_raw)

        tool_name = arguments.get("tool_name", "")
        reason = arguments.get("reason", "")

        print(f"🧭 선택된 도구: {tool_name} → {reason}")
        return {**state, "plan": tool_name, "plan_desc": reason}
    except Exception as e:
        print(f"❌ Function call 처리 중 오류 발생: {e}")
        return {**state, "plan": "", "plan_desc": ""}
        
planner_node = RunnableLambda(planner_fn)