import pandas as pd
import numpy as np
import re
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

# Create the critic agent node function
def code_critic_agent_node_fn(state):
    try:
        st.info("✅ [Code Critic Agent] Evaluating mapping code...")
        
        # Get necessary data from state
        raw_data = state.get("raw_data")
        mapping_function_code = state.get("mapping_function_code")
        raw_data_mapped = state.get("raw_data_mapped")
        raw_code_guide = state.get("raw_code_guide")
        raw_variables = state.get("raw_variables")
        selected_table = state.get("selected_table")
        major_str = state.get("major_str", "")
        
        if mapping_function_code is None:
            st.warning("⚠️ No mapping code to evaluate")
            return state
            
        # Initialize LLM
        llm = ChatOpenAI(model="gpt-4o", temperature=0.1, top_p=0.1)
        
        # Check if mapping added required columns
        column_check = all(col in raw_data_mapped.columns for col in ['대분류', '소분류'])
        
        # Calculate percentage of non-null values in mapped columns
        valid_mappings_pct = 0
        if column_check:
            valid_mappings_pct = (
                (raw_data_mapped['대분류'].notna().mean() + 
                raw_data_mapped['소분류'].notna().mean()) / 2 * 100
            )
        
        # Additional statistics for the prompt
        stats = {
            "총 데이터 행 수": len(raw_data),
            "매핑된 데이터 행 수": len(raw_data_mapped) if raw_data_mapped is not None else 0,
            "대분류,소분류 컬럼 존재": "Yes" if column_check else "No",
            "유효 매핑 비율(%)": f"{valid_mappings_pct:.2f}%" if column_check else "0%",
        }
        
        # Get unique values in mapped columns if they exist
        mapped_values = {}
        if column_check:
            mapped_values["대분류_유니크값"] = raw_data_mapped['대분류'].dropna().unique().tolist()
            mapped_values["소분류_유니크값"] = raw_data_mapped['소분류'].dropna().unique().tolist()
        
        # LLM Prompt for code evaluation
        prompt = f"""
        당신은 통계 설문 데이터 처리를 위한 mapping 코드를 평가하는 Code Critic입니다.
        주어진 매핑 함수를 분석하고 accept/reject 결정과 개선 제안을 제공해야 합니다.

        [매핑 함수 코드]
        ```python
        {mapping_function_code}
        ```

        [실행 통계]
        {stats}

        [매핑된 값들]
        {mapped_values}

        [평가 기준]
        1. 기능적 정확성: 대분류, 소분류 컬럼이 올바르게 생성되었는가?
        2. 매핑 완전성: 최소 80% 이상의 행이 매핑되었는가?
        3. 코드 품질: 효율적이고 가독성이 높은가? 논리 오류가 없는가?
        4. 예외 처리: 누락된 값이나 예외 상황에 대한 처리가 있는가?

        [최종 결정]
        위 기준을 바탕으로 하나를 선택해 주세요:
        - "ACCEPT": 코드가 모든 기준을 충족, 혹은 약간의 개선점만 있음
        - "REJECT": 코드에 중대한 문제가 있어 수정 필요

        [응답 형식]
        다음 형식으로 JSON 형태의 평가 결과를 제공해주세요:
        ```json
        {{
            "decision": "ACCEPT 또는 REJECT",
            "reasons": ["이유1", "이유2", "이유3"],
            "suggestions": ["제안1", "제안2"],
            "score": 80
        }}
        ```

        JSON 형식만 응답해 주세요.
        """
        
        # Get evaluation from LLM
        response = llm.invoke(prompt)
        
        # Extract JSON response
        json_pattern = r"\{[\s\S]*\}"
        match = re.search(json_pattern, response.content)
        
        if match:
            import json
            try:
                evaluation = json.loads(match.group(0))
                
                # Display evaluation results
                st.subheader("🔍 Code Critic Evaluation")
                
                # Decision with color coding
                decision = evaluation.get("decision", "UNKNOWN")
                if decision == "ACCEPT":
                    st.success(f"Decision: {decision} (Score: {evaluation.get('score', 'N/A')})")
                else:
                    st.error(f"Decision: {decision} (Score: {evaluation.get('score', 'N/A')})")
                
                # Reasons
                st.write("**Reasons:**")
                for reason in evaluation.get("reasons", []):
                    st.write(f"- {reason}")
                
                # Suggestions
                st.write("**Suggestions:**")
                for suggestion in evaluation.get("suggestions", []):
                    st.write(f"- {suggestion}")
                
                # Add evaluation to state
                state["code_evaluation"] = evaluation
                
                # If rejected, suggest improvements
                if decision == "REJECT" and evaluation.get("score", 0) < 60:
                    st.info("🔄 Generating improved mapping code...")
                    
                    # Prompt for improved code
                    improvement_prompt = f"""
                    당신은 통계 설문 데이터 매핑 전문가입니다. 아래 코드를 개선해야 합니다.

                    [기존 코드]
                    ```python
                    {mapping_function_code}
                    ```

                    [문제점]
                    {evaluation.get('reasons', [])}

                    [개선 제안]
                    {evaluation.get('suggestions', [])}

                    [원본 데이터 정보]
                    - 대분류 값 목록: {major_str}
                    - Raw Code Guide (일부): 
                    {raw_code_guide.to_string() if raw_code_guide is not None else "Not available"}

                    [요구사항]
                    - 위 문제점을 해결하는 개선된 mapping_function(df)을 작성하세요
                    - 코드만 제공하세요 (설명 없이)
                    - 반드시 마지막에 return df를 포함하세요
                    - df의 사본을 수정하지 말고 원본 df에 직접 컬럼을 추가하세요

                    ```python
                    def mapping_function(df):
                        # 개선된 코드를 여기에 작성
                        
                        return df
                    ```
                    """
                    
                    improved_response = llm.invoke(improvement_prompt)
                    
                    # Extract code
                    code_match = re.search(r"```(?:python)?(.*?)```", improved_response.content, re.DOTALL)
                    if code_match:
                        improved_code = code_match.group(1).strip()
                        
                        # Ensure return df is included
                        if not improved_code.strip().endswith("return df"):
                            improved_code += "\n\n    return df"
                        
                        st.subheader("✨ Improved Mapping Code")
                        st.code(improved_code, language='python')
                        
                        # Add to state
                        state["improved_mapping_code"] = improved_code
                        
                        try:
                            # Execute improved code
                            local_vars = {"pd": pd, "np": np}
                            exec(improved_code, globals(), local_vars)
                            improved_mapping_function = local_vars["mapping_function"]
                            
                            # Apply improved mapping
                            improved_mapped_data = improved_mapping_function(raw_data)
                            
                            # Output results
                            st.subheader("📋 Improved Mapping Results")
                            st.dataframe(improved_mapped_data)
                            
                            # Add to state
                            state["improved_raw_data_mapped"] = improved_mapped_data
                        except Exception as exec_error:
                            st.error(f"❌ Error executing improved code: {str(exec_error)}")
            except json.JSONDecodeError:
                st.error("❌ Failed to parse evaluation response as JSON")
        else:
            st.error("❌ Failed to get proper evaluation from LLM")
    
        return state
        
    except Exception as e:
        st.error(f"❌ [Code Critic Agent Error] {str(e)}")
        return state

# Create the agent
streamlit_code_critic_node = RunnableLambda(code_critic_agent_node_fn)