# mapping_workflow_graph.py
# variable_semantics_inference_agent.py -> mapping_planning_agent.py -> mapping_rule_reasoning_agent.py -> mapping_function_generator.py 순서로 진행되도록 LangGraph 코드 작성

from langgraph.graph import StateGraph
from typing import TypedDict

import pandas as pd

# ✅ 당신이 작성한 각 agent import
from streamlit_table_agents.streamlit_agent.numeric_analysis.numeric_mapping_agents.variable_semantics_inference_agent import variable_semantics_node
from streamlit_table_agents.streamlit_agent.numeric_analysis.numeric_mapping_agents.mapping_planning_agent import mapping_planning_node
from streamlit_table_agents.streamlit_agent.numeric_analysis.numeric_mapping_agents.mapping_rule_reasoning_agent import mapping_rule_reasoning_node
from streamlit_table_agents.streamlit_agent.numeric_analysis.numeric_mapping_agents.mapping_function_generator import mapping_function_generator_node

# ✅ State 정의 (당신 스타일 + 연결 필드 포함)
class MappingWorkflowState(TypedDict):
    major_str: str
    minor_str: str
    code_guide_str: str
    raw_variables: str
    semantics_result: str
    mapping_plan_result: str
    mapping_rule_result: str
    generated_code: str
    raw_data: pd.DataFrame               # ✅ 추가 (중요)
    raw_data_mapped: pd.DataFrame        # ✅ 추가 (중요)

# ✅ LangGraph workflow 작성
def get_mapping_workflow():
    workflow = StateGraph(MappingWorkflowState)

    # 4개 node 연결
    workflow.add_node("variable_semantics", variable_semantics_node)
    workflow.add_node("mapping_planning", mapping_planning_node)
    workflow.add_node("mapping_rule_reasoning", mapping_rule_reasoning_node)
    workflow.add_node("mapping_function_generator", mapping_function_generator_node)

    # ✅ 연결 순서 정의
    workflow.set_entry_point("variable_semantics")
    workflow.add_edge("variable_semantics", "mapping_planning")
    workflow.add_edge("mapping_planning", "mapping_rule_reasoning")
    workflow.add_edge("mapping_rule_reasoning", "mapping_function_generator")

    return workflow.compile()

# # ✅ 실행 예시
# if __name__ == "__main__":
#     workflow = get_mapping_workflow()
    
#     # 예시 input (당신이 원하는 실제 값으로 교체 가능)
#     initial_state = MappingWorkflowState(
#         major_str="['A', 'B']",
#         minor_str="['X', 'Y']",
#         code_guide_str="코드 가이드 예시",
#         raw_variables="raw data 변수 설명 예시",
#         semantics_result="",
#         mapping_plan_result="",
#         mapping_rule_result="",
#         generated_code=""
#     )

#     result = workflow.invoke(initial_state)
#     print("\n✅ 최종 mapping_function 코드:")
#     print(result["generated_code"])