import os
import openai

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)


PLANNER_PROMPT = """당신은 유능한 AI 비서입니다. 
사용자의 질문은 다음과 같고:

질문: {query}

이에 대해 도구(tool)를 사용한 결과는 다음과 같습니다:

도구 결과: {tool_result}

이 결과를 바탕으로 자연스러운 사용자 응답을 생성해주세요.
"""


def responder_fn(state: dict) -> dict:
    query = state["query"]
    tool_result = state["tool_result"]
    response = llm.invoke(PLANNER_PROMPT.format(query = query, tool_result = tool_result))
    return {**state, "final_answer": response.content}

responder_node = RunnableLambda(responder_fn)