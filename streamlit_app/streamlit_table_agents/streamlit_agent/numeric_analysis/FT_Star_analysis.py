from scipy.stats import f_oneway, ttest_ind
from langchain_core.runnables import RunnableLambda
import streamlit as st

def assign_significance_stars(p):
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""

def ft_star_analysis_node_fn(state):
    st.info("✅ [F/T 검정 Agent] Start")

    raw_data_mapped = state["raw_data_mapped"]
    selected_key = state["selected_key"]       # 예: 'A1', 'B5_2' 등
    major_str = state["major_str"]             # 예: '성별', '연령', '생활권역' 등

    result_dict = state.get("ft_test_result", {})

    # ✅ 예외 처리: 컬럼 존재 여부
    if major_str not in raw_data_mapped.columns not in raw_data_mapped.columns:
        msg = f"❗ '{major_str}' 컬럼이 raw_data_mapped에 없습니다."
        result_dict[major_str] = msg
        state["ft_test_result"] = result_dict
        st.error(msg)
        return state

    groups = raw_data_mapped.groupby(major_str)[selected_key].apply(list)

    # ✅ 그룹 수에 따라 t-test 또는 ANOVA
    if len(groups) == 2:
        stat, p = ttest_ind(groups.iloc[0], groups.iloc[1], nan_policy='omit')
        method = "T-test"
    elif len(groups) >= 3:
        stat, p = f_oneway(*groups)
        method = "F-test (ANOVA)"
    else:
        msg = f"❗ '{major_str}' 기준 그룹이 하나라서 테스트 불가."
        result_dict[major_str] = msg
        state["ft_test_result"] = result_dict
        st.warning(msg)
        return state

    result_str = (
        f"### 🎯 [F/T 검정 결과] `{major_str}` 기준\n\n"
        f"- 검정 방법: **{method}**\n"
        f"- F/T 값: **{abs(stat):.3f}**\n"
        f"- p-value: **{p:.4f}** → {assign_significance_stars(p)}\n"
    )

    # ✅ 결과 저장 + Streamlit 출력
    result_dict[major_str] = result_str
    state["ft_test_result"] = result_dict

    st.markdown(result_str)

    return state

# ✅ LangGraph node로 생성
streamlit_ft_star_analysis_node = RunnableLambda(ft_star_analysis_node_fn)