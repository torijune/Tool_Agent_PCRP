# streamlit_auto_mapping.py (개선판: LangGraph 기반으로 변경)

import pandas as pd
import numpy as np
import os
import streamlit as st
from dotenv import load_dotenv

from streamlit_table_agents.streamlit_agent.numeric_analysis.numeric_analysis_graph.mapping_workflow_graph import get_mapping_workflow

load_dotenv()

def auto_mapping_with_graph(state):
    try:
        st.info("✅ [Auto Mapping Agent] Start (LangGraph version)")

        selected_table = state["selected_table"]
        raw_data = state["raw_data"]
        raw_code_guide = state["raw_code_guide"]
        raw_variables = state["raw_variables"]

        raw_code_guide['변수명'] = raw_code_guide['변수명'].ffill()

        major = selected_table["대분류"].dropna().unique().tolist()
        minor = selected_table["소분류"].dropna().unique().tolist()

        major_str = ", ".join(major)
        minor_str = ", ".join(minor)
        code_guide_str = raw_code_guide.to_string()

        workflow = get_mapping_workflow()
        result = workflow.invoke({
            "major_str": major_str,
            "minor_str": minor_str,
            "code_guide_str": code_guide_str,
            "raw_variables": raw_variables,
            "semantics_result": "",
            "mapping_plan_result": "",
            "mapping_rule_result": "",
            "generated_code": "",
            "raw_data": raw_data, 
            "raw_data_mapped": None,
        })

        generated_code = result["generated_code"]

        # ✅ 바로 코드 실행 + mapping 수행
        local_vars = {"pd": pd, "np": np}
        exec(generated_code, globals(), local_vars)
        mapping_function = local_vars["assign_strata"]
        mapped_raw_data = mapping_function(raw_data)

        # ✅ FT analysis에서 반드시 필요
        state["raw_data_mapped"] = mapped_raw_data

        st.subheader("📝 LLM이 생성한 Mapping Code")
        st.code(generated_code, language='python')

        st.subheader("📋 Mapping 이후 DataFrame")
        st.dataframe(mapped_raw_data)

        return {
            **state,
            "mapping_function_code": generated_code,
            "major_str": major_str
        }

    except Exception as e:
        st.error(f"❌ [Auto Mapping Error] {str(e)}")
        return state

# ✅ Agent 생성
from langchain_core.runnables import RunnableLambda
streamlit_auto_mapping_node = RunnableLambda(auto_mapping_with_graph)