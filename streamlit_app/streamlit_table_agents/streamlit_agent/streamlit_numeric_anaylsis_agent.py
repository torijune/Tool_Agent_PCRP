import pandas as pd
import streamlit as st

from langchain_core.runnables import RunnableLambda

def analyze_by_category(df: pd.DataFrame) -> dict:
    numeric_cols = df.select_dtypes(include=["number"]).columns
    results = {}

    for category in df["대분류"].unique():
        group_df = df[df["대분류"] == category]
        group_result = {}

        for col in numeric_cols:
            if "사례수" in col:
                continue

            col_data = group_df[col]
            if col_data.isnull().all():
                continue

            max_val = round(col_data.max(), 2)
            min_val = round(col_data.min(), 2)
            std_val = round(col_data.std(), 2)

            max_group = group_df.loc[col_data.idxmax(), "소분류"]
            min_group = group_df.loc[col_data.idxmin(), "소분류"]

            group_result[col.strip()] = {
                "max_group": str(max_group),
                "min_group": str(min_group),
                "range": round(max_val - min_val, 2),
                "std": std_val
            }

        results[category.strip()] = group_result

    return results

def extract_insightful_analysis(grouped_stats: dict, range_threshold=5.0, std_threshold=3.0):
    insightful_data = {}
    for category, col_dict in grouped_stats.items():
        category_result = {}
        for col, stats in col_dict.items():
            if stats["range"] >= range_threshold or stats["std"] >= std_threshold:
                category_result[col] = stats
        if category_result:
            insightful_data[category] = category_result
    return insightful_data

def format_insightful_analysis_to_text(insightful_data: dict) -> str:
    summary_sentences = []
    for category, stats in insightful_data.items():
        summary_sentences.append(f"[{category}] 항목에서는 다음과 같은 특이점이 관찰되었습니다.")
        for col, detail in stats.items():
            max_group = detail["max_group"]
            min_group = detail["min_group"]
            range_val = detail["range"]
            std_val = detail["std"]
            sentence = (
                f"- '{col}' 항목은 '{max_group}' 그룹에서 가장 높고, "
                f"'{min_group}' 그룹에서 가장 낮았습니다. "
                f"해당 항목의 값 범위는 {range_val}이며, 표준편차는 {std_val}입니다."
            )
            summary_sentences.append(sentence)
        summary_sentences.append("")
    return "\n".join(summary_sentences)

def streamlit_numeric_analysis_node_fn(state):
    st.info("✅ [Numeric Analysis Agent] Start table numeric analysis")
    selected_table = state["selected_table"]

    with st.spinner("표 데이터 분석 중..."):
        grouped = analyze_by_category(selected_table)
        insights = extract_insightful_analysis(grouped)
        numeric_analysis_text = format_insightful_analysis_to_text(insights)

    # 🎯 ✅ 개선된 출력: 카테고리별 expander + markdown
    st.markdown("### ✅ Generated Numeric Analyses")
    current_category = None
    buffer = ""

    for line in numeric_analysis_text.split("\n"):
        # 새로운 카테고리 시작
        if line.startswith("[") and line.endswith("] 항목에서는 다음과 같은 특이점이 관찰되었습니다."):
            # 기존 카테고리 출력
            if current_category and buffer:
                with st.expander(current_category, expanded=False):
                    st.markdown(buffer)
            # 새로운 카테고리 준비
            current_category = line.replace(" 항목에서는 다음과 같은 특이점이 관찰되었습니다.", "")
            buffer = ""
        else:
            buffer += line + "\n"

    # 마지막 카테고리 출력
    if current_category and buffer:
        with st.expander(current_category, expanded=False):
            st.markdown(buffer)

    return {**state, "numeric_anaylsis": numeric_analysis_text}

streamlit_numeric_analysis_node = RunnableLambda(streamlit_numeric_analysis_node_fn)