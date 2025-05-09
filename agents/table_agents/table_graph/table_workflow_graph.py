from langgraph.graph import StateGraph, END
from typing import Annotated, TypedDict
from langchain_core.runnables import Runnable
from pandas import DataFrame

from agents.table_agents.agent_C.numeric_anaylsis_agent import numeric_analysis_node
from agents.table_agents.agent_C.table_analysis_agent import table_anaylsis_node
from agents.table_agents.agent_C.table_parser import table_parser_node
from agents.table_agents.agent_C.retrieval_file_agent import retrieval_table_node
from agents.table_agents.agent_C.hallucination_check_agent import hallucination_check_node
from agents.table_agents.agent_C.revision_agent import revise_table_analysis


class AgentState(TypedDict):
    query: Annotated[str,"User input query"]
    file_path: Annotated[str, "table file path formatted csv"]
    # table: Annotated[DataFrame, "Loaded Table formatted pandas DataFrames"]
    # question_texts: Annotated[str, "question_texts"]
    selected_question: Annotated[str, "selected_question"]
    selected_table: Annotated[DataFrame, "Selected Table formatted pandas DataFrame"]
    linearized_table: Annotated[str, "Linearized table sentences"]
    numeric_anaylsis: Annotated[str, "Numeric analysis results"]
    table_analysis: Annotated[str, "Final table analysis reulste"]
    hallucination_check: Annotated[str, "table_analysis hallucination_check"]
    feedback: Annotated[str, "LLM feedback"]


def build_table_graph() -> Runnable:
    builder = StateGraph(state_schema=AgentState)

    # 노드 정의
    builder.add_node("retrieval_table_node", retrieval_table_node)
    builder.add_node("numeric_analyzer", numeric_analysis_node)
    builder.add_node("table_analyzer", table_anaylsis_node)
    builder.add_node("table_parser", table_parser_node)
    builder.add_node("hallucination_check_node", hallucination_check_node)
    builder.add_node("revise_table_analysis", revise_table_analysis)

    # Input | Output
    # query | file_path
    builder.set_entry_point("retrieval_table_node")

    # file_path | selected_table, table, selected_question, question_keys, linearized_table
    builder.add_edge("retrieval_table_node", "table_parser")

    # selected_table | numeric_anaylsis
    builder.add_edge("table_parser", "numeric_analyzer")

    # linearized_table, numeric_anaylsis, selected_question | table_analysis
    builder.add_edge("numeric_analyzer", "table_analyzer")

    # linearized_table, numeric_anaylsis, selected_question, table_analysis | hallucination_check, feedback
    builder.add_edge("table_analyzer", "hallucination_check_node")

    def route_hallucination(state):
        hallucination_check = state.get("hallucination_check", "")
        if hallucination_check == "accept":
            return END
        elif hallucination_check == "reject":
            return "revise_table_analysis"
        else:
            raise ValueError(f"Unexpected decision: {hallucination_check}")

    builder.add_conditional_edges("hallucination_check_node", route_hallucination, [END,"revise_table_analysis"])


    graph = builder.compile()
    return graph

