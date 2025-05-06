import os
import openai

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

PLANNER_PROMPT = """
You are a planning assistant. Based on the user query below, decide the most appropriate tool to use (calculator, python, search, etc.)
Respond with a one-line plan like: "Use calculator to compute compound interest."

User query: {query}
"""

def planner_fn(state: dict) -> dict:
    query = state["query"]
    response = llm.invoke(PLANNER_PROMPT.format(query=query))
    # print("Plan Decision:", response.content)
    return {**state, "plan": response.content.strip()}

planner_node = RunnableLambda(planner_fn)