from langgraph.graph import StateGraph, END
from typing import Annotated, TypedDict
from langchain_core.runnables import Runnable
from pandas import DataFrame

from agent_C.numeric_anaylsis import numeric_analysis_node
from agent_C.table_analysis_agent import table_anaylsis_node
from agent_C.table_parser import table_parser_node

class AgentState(TypedDict):
    file_path: Annotated[str, "table file path formatted csv"]
    # table: Annotated[DataFrame, "Loaded Table formatted pandas DataFrames"]
    selected_question: Annotated[str, "selected_question"]
    selected_table: Annotated[DataFrame, "Selected Table formatted pandas DataFrame"]
    linearized_table: Annotated[str, "Linearized table sentences"]
    numeric_anaylsis: Annotated[str, "Numeric analysis results"]
    table_analysis: Annotated[str, "Final table analysis reulste"]


def build_table_graph() -> Runnable:
    builder = StateGraph(state_schema=AgentState)

    # 노드 정의
    builder.add_node("numeric_analyzer", numeric_analysis_node)
    builder.add_node("table_analyzer", table_anaylsis_node)
    builder.add_node("table_parser", table_parser_node)

    # 엣지 정의
    builder.set_entry_point("table_parser")
    builder.add_edge("table_parser", "numeric_analyzer")
    builder.add_edge("numeric_analyzer", "table_analyzer")
    builder.add_edge("table_analyzer", END)

    graph = builder.compile()
    return graph

