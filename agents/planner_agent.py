import os
import openai

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

PLANNER_PROMPT = """
You are a smart tool-planning assistant. Based on the user query below, select the most appropriate tool to handle the task.

You can choose from the following tools:
1. "search": Use this for general information retrieval from the web (e.g., current events, websites, product info).
2. "abstract analyzer": Use this for understanding or answering questions using academic paper abstracts (e.g., questions related to research topics or technical summaries).

Instructions:
- Respond with a one-line plan that includes the tool name and task description.
- Format: "Use [tool_name] to [task description]."
- Do not explain or justify your answer. Output only the plan.

Examples:
- Query: "What are the latest trends in generative AI?"  
  → "Use search to find recent trends in generative AI."

- Query: "Explain what Retrieval-Augmented Generation is."  
  → "Use abstract analyzer to summarize Retrieval-Augmented Generation."

- Query: "Find a paper that compares GPT-4 with open-source models."  
  → "Use abstract analyzer to analyze papers comparing GPT-4 with open-source models."

Now, given the query below, respond with the correct tool and task:

User query: {query}
"""

def planner_fn(state: dict) -> dict:
    query = state["query"]
    response = llm.invoke(PLANNER_PROMPT.format(query=query))
    print("Plan Decision:", response.content)
    selected_plan = response.content.strip()
    return {**state, "plan": selected_plan}

planner_node = RunnableLambda(planner_fn)