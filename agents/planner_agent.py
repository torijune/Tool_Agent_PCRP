import os
import openai
import json
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda
from agents.tools_schema import function_schema

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(
    model="gpt-4o",  # function calling은 gpt-4-0613, gpt-4o 등 지원 모델 필요
    temperature=0.2,
    model_kwargs={"functions": function_schema}
)

PLANNER_PROMPT = """
You are a smart tool-planning assistant. Based on the user query below, select the most appropriate tool to handle the task.

You can choose from the following tools:
1. "search": Use this for general information retrieval from the web (e.g., current events, websites, product info).
2. "abstract analyzer": Use this for understanding or answering questions using academic paper abstracts (e.g., questions related to research topics or technical summaries).

Return a function call to `use_tool` with:
- tool_name: either "search" or "abstract analyzer"
- task_description: one-line task description

Do not explain your answer. Only respond via function_call.
"""

def planner_fn(state: dict) -> dict:
    query = state["query"]
    messages = [
        {"role": "system", "content": PLANNER_PROMPT.strip()},
        {"role": "user", "content": query}
    ]

    response = llm.invoke(messages)
    function_call = response.additional_kwargs.get("function_call", {})

    tool_name = ""
    task_description = ""

    try:
        # 🧠 arguments는 JSON 문자열이므로 반드시 파싱해야 함
        arguments_raw = function_call.get("arguments", "{}")
        arguments = json.loads(arguments_raw)

        tool_name = arguments.get("tool_name", "")
        task_description = arguments.get("task_description", "")
    except Exception as e:
        print(f"❌ Function call 처리 중 오류 발생: {e}")

    print(f"🧭 선택된 도구: {tool_name} → {task_description}")
    return {**state, "plan": tool_name, "plan_desc": task_description}

planner_node = RunnableLambda(planner_fn)