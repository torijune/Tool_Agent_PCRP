from h11 import Data
from langgraph.graph import StateGraph, END
from typing import Annotated, TypedDict, IO, Dict
from langchain_core.runnables import Runnable
from pandas import DataFrame

from streamlit_table_agents.streamlit_agent.numeric_analysis.streamlit_numeric_anaylsis_agent import streamlit_numeric_analysis_node
from streamlit_table_agents.streamlit_agent.streamlit_table_analysis_agent import streamlit_table_anaylsis_node
from streamlit_table_agents.streamlit_agent.utils.streamlit_table_parser import streamlit_table_parser_node
from streamlit_table_agents.streamlit_agent.streamlit_hallucination_check_agent import streamlit_hallucination_check_node
from streamlit_table_agents.streamlit_agent.streamlit_revision_agent import streamlit_revise_table_analysis_node
from streamlit_table_agents.streamlit_agent.streamlit_polish_agent import streamlit_sentence_polish_node
from streamlit_table_agents.streamlit_agent.streamlit_hypothesis_generation import streamlit_hypothesis_generate_node
from streamlit_table_agents.streamlit_agent.numeric_analysis.streamlit_auto_mapping import streamlit_auto_mapping_node
from streamlit_table_agents.streamlit_agent.numeric_analysis.streamlit_code_critic_agent import streamlit_code_critic_node
from streamlit_table_agents.streamlit_agent.numeric_analysis.FT_Star_analysis import streamlit_ft_star_analysis_node

class AgentState(TypedDict):
    query: Annotated[str,"User input query"]
    file_path: Annotated[str, "table file path formatted csv"]

    analysis_type: Annotated[bool, "select analysis type - True: manual selection, False: batch all"]

    selected_question: Annotated[str, "selected_question"]
    selected_table: Annotated[DataFrame, "Selected Table formatted pandas DataFrame"]
    selected_key: Annotated[str, "Selected table key for manual selection"]

    linearized_table: Annotated[str, "Linearized table sentences"]

    numeric_anaylsis: Annotated[str, "Numeric analysis results"]

    table_analysis: Annotated[str, "Final table analysis result"]
    revised_analysis: Annotated[str, "Revised analysis by revision LLM"]

    hallucination_check: Annotated[str, "table_analysis hallucination_check"]
    hallucination_reject_num: Annotated[int, "Number of hallucination rejections"]
    feedback: Annotated[str, "LLM feedback"]

    polishing_result: Annotated[str, "Final sentence polishing step output"]

    generated_hypotheses: Annotated[str, "Generated hypothesis for table"]

    uploaded_file: Annotated[IO[bytes], "Streamlit Uploaded File (file-like object)"]
    raw_data_file: Annotated[IO[bytes], "Streamlit Uploaded Raw Data File (file-like object)"]

    raw_data: Annotated[DataFrame, "Raw DATA sheet DataFrame"]
    raw_variables: Annotated[DataFrame, "변수 sheet DataFrame"]
    raw_code_guide: Annotated[DataFrame, "코딩가이드 sheet DataFrame"]
    raw_question: Annotated[DataFrame, "문항 sheet DataFrame"]

    major_str: Annotated[str, "Numeric Analysis를 진행할 table의 대분류"]
    raw_data_mapped: Annotated[DataFrame, "Raw Data를 LLM을 통해 auto mapping한 결과물"]
    mapping_function_code: Annotated[str, "Auto mapping 함수 코드"]
    code_evaluation: Annotated[Dict[str, any], "Code critic 평가 결과"]
    improved_mapping_code: Annotated[str, "개선된 mapping 함수 코드"]
    improved_raw_data_mapped: Annotated[DataFrame, "개선된 mapping 함수로 생성한 결과물"]
    ft_test_result: Annotated[Dict[str, str], "F/T 검정 결과 dict (e.g. {'성별': '...결과'})"]

def build_table_graph() -> Runnable:
    builder = StateGraph(state_schema=AgentState)

    # ✅ 노드 정의
    builder.add_node("table_parser", streamlit_table_parser_node)
    builder.add_node("hypothesis_generate_node", streamlit_hypothesis_generate_node)
    builder.add_node("numeric_analyzer", streamlit_numeric_analysis_node)
    builder.add_node("table_analyzer", streamlit_table_anaylsis_node)
    builder.add_node("hallucination_check_node", streamlit_hallucination_check_node)
    builder.add_node("revise_table_analysis", streamlit_revise_table_analysis_node)
    builder.add_node("sentence_polish_node", streamlit_sentence_polish_node)
    builder.add_node("auto_mapping_node", streamlit_auto_mapping_node)
    builder.add_node("code_critic_node", streamlit_code_critic_node)
    builder.add_node("FT_anlysis_node", streamlit_ft_star_analysis_node)

    # ✅ Entry Point
    builder.set_entry_point("table_parser")

    # ✅ Graph Flow
    builder.add_edge("table_parser", "hypothesis_generate_node")
    builder.add_edge("hypothesis_generate_node", "auto_mapping_node")
    builder.add_edge("auto_mapping_node", "code_critic_node")
    
    # Add conditional edge to handle code critic decisions
    def route_code_critic(state):
        evaluation = state.get("code_evaluation", {})
        decision = evaluation.get("decision", "UNKNOWN")
        score = evaluation.get("score", 0)
        
        print(f"💡 Code Critic Decision: {decision} | Score: {score}")
        
        # Check if improved mapping exists and is valid
        improved_data = state.get("improved_raw_data_mapped")
        if decision == "REJECT" and improved_data is not None:
            if all(col in improved_data.columns for col in ['대분류', '소분류']):
                # Update the raw_data_mapped with the improved version
                state["raw_data_mapped"] = improved_data
                print("✅ Using improved mapping data for further analysis")
            else:
                print("⚠️ Improved mapping data lacks required columns")
        
        # Always proceed to next step (we've already handled any improvements)
        return "FT_anlysis_node"
    
    builder.add_conditional_edges(
        "code_critic_node",
        route_code_critic,
        ["FT_anlysis_node"]
    )
    
    builder.add_edge("FT_anlysis_node", "numeric_analyzer")
    builder.add_edge("numeric_analyzer", "table_analyzer")
    builder.add_edge("table_analyzer", "hallucination_check_node")

    def route_hallucination(state):
        result = state.get("hallucination_check", "")
        reject_count = state.get("hallucination_reject_num", 0)
        print(f"💡 Hallucination Check: {result} | Reject Count: {reject_count}")

        if result == "accept":
            return "sentence_polish_node"
        elif result == "reject":
            if reject_count >= 3:
                print("⚠️ Reject count exceeded. Forcing END.")
                return END
            return "revise_table_analysis"
        else:
            raise ValueError(f"Unexpected decision: {result}")

    builder.add_conditional_edges(
        "hallucination_check_node",
        route_hallucination,
        ["sentence_polish_node", END, "revise_table_analysis"]
    )

    builder.add_edge("revise_table_analysis", "hallucination_check_node")
    builder.add_edge("sentence_polish_node", END)

    return builder.compile()