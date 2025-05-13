import pandas as pd
import streamlit as st

from langchain_core.runnables import RunnableLambda

def analyze_column_variation(df: pd.DataFrame, range_threshold=5.0, std_threshold=3.0):
    numeric_cols = df.select_dtypes(include=["number"]).columns
    results = {}

    # ✅ 1️⃣ 전체 평균이 가장 높은 anchor column 찾기
    col_means = df[numeric_cols].mean()
    anchor_col = col_means.idxmax()

    # ✅ 2️⃣ anchor_col을 중심으로 분석 진행
    for category in df["대분류"].unique():
        group_df = df[df["대분류"] == category]
        if anchor_col not in group_df.columns:
            continue

        group_result = {}
        col_data = group_df[anchor_col]
        if col_data.isnull().all():
            continue

        max_val = round(col_data.max(), 2)
        min_val = round(col_data.min(), 2)
        std_val = round(col_data.std(), 2)

        max_group = group_df.loc[col_data.idxmax(), "소분류"]
        min_group = group_df.loc[col_data.idxmin(), "소분류"]

        # ✅ 3️⃣ threshold 기반 filtering
        if (max_val - min_val) >= range_threshold or std_val >= std_threshold:
            group_result[anchor_col] = {
                "max_group": str(max_group),
                "min_group": str(min_group),
                "range": round(max_val - min_val, 2),
                "std": std_val
            }

        if group_result:
            results[category.strip()] = group_result

    return results, anchor_col

def format_anchor_analysis(insightful_data: dict, anchor_col: str) -> str:
    summary_sentences = []
    summary_sentences.append(f"✅ 전체 데이터에서 가장 비중이 높은 분석 anchor column은 **'{anchor_col}'** 입니다.\n")

    for category, stats in insightful_data.items():
        summary_sentences.append(f"### [{category}]")
        for col, detail in stats.items():
            max_group = detail["max_group"]
            min_group = detail["min_group"]
            range_val = detail["range"]
            std_val = detail["std"]
            sentence = (
                f"- '{col}' 항목은 '{max_group}' 그룹에서 가장 높고, "
                f"'{min_group}' 그룹에서 가장 낮았음. "
                f"(Range={range_val}, Std={std_val})"
            )
            summary_sentences.append(sentence)
        summary_sentences.append("")
    return "\n".join(summary_sentences)

def streamlit_numeric_analysis_node_fn(state):
    st.info("✅ [Numeric Analysis Agent] Start table numeric analysis")
    selected_table = state["selected_table"]

    with st.spinner("표 데이터 분석 중..."):
        insights, anchor_col = analyze_column_variation(selected_table)
        numeric_analysis_text = format_anchor_analysis(insights, anchor_col)

    # ✅ Streamlit 출력
    st.markdown("### 📊 Numeric Analysis 결과")
    st.markdown(numeric_analysis_text)

    return {**state, "numeric_anaylsis": numeric_analysis_text}

streamlit_numeric_analysis_node = RunnableLambda(streamlit_numeric_analysis_node_fn)