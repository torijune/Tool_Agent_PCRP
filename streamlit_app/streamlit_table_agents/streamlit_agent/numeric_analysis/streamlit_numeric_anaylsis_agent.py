import pandas as pd
import numpy as np
import streamlit as st
from langchain_core.runnables import RunnableLambda
from scipy.stats import f_oneway, ttest_ind

# ✅ Table type 분류
def classify_table_type(df: pd.DataFrame):
    if any(col in df.columns for col in ["평균(5점척도)", "평균(4점척도)"]):
        return "anchor"
    elif "소분류" not in df.columns or df["소분류"].isna().all():
        return "simple"
    else:
        return "unknown"

# ✅ Anchor table 분석
def anchor_table_analysis(df: pd.DataFrame):
    anchor_col = "평균(5점척도)" if "평균(5점척도)" in df.columns else "평균(4점척도)"
    overall_value = df.loc[
        df["대분류"].astype(str).str.contains("전체|전 체|전", na=False), 
        anchor_col
    ].mean()

    results = {}
    valid_categories = (
        df.dropna(subset=["대분류", "소분류"])
          .groupby("대분류")["소분류"]
          .nunique()
          .loc[lambda x: x >= 2]
          .index.tolist()
    )

    for category in valid_categories:
        group_df = df[df["대분류"] == category].dropna(subset=["소분류"])
        groups = [vals[anchor_col].dropna().values for _, vals in group_df.groupby("소분류")]
        valid_groups = [g for g in groups if len(g) >= 2]
        f_value, p_value, sig = None, None, "-"

        if len(valid_groups) >= 2:
            try:
                f_value, p_value = f_oneway(*valid_groups)
            except:
                pass

        if p_value is not None:
            if p_value < 0.001:
                sig = "***"
            elif p_value < 0.01:
                sig = "**"
            elif p_value < 0.05:
                sig = "*"

        insights = []
        for _, row in group_df.iterrows():
            subgroup = row["소분류"]
            value = row[anchor_col]
            if pd.isna(value):
                continue
            diff = round(value - overall_value, 2)
            if abs(diff) >= 0.1:
                trend = "높음" if diff > 0 else "낮음"
                insights.append({
                    "소분류": subgroup,
                    "값": value,
                    "차이": diff,
                    "트렌드": trend
                })

        if insights:
            results[category] = {
                "f_value": round(f_value, 3) if f_value else None,
                "p_value": round(p_value, 4) if p_value else None,
                "sig": sig,
                "insights": insights
            }

    return format_anchor_analysis(results, anchor_col, overall_value)

# ✅ Simple table 분석
def simple_table_analysis(df: pd.DataFrame):
    lines = ["✅ 간단 Table 분석 결과입니다.\n"]
    numeric_cols = df.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        lines.append(f"- **{col}**: 평균={df[col].mean():.2f}, 표준편차={df[col].std():.2f}")
    return "\n".join(lines)

def unknown_table_analysis(df: pd.DataFrame):
    return "❌ 테이블 유형을 판단할 수 없어 분석을 건너뜁니다."

# ✅ Formatting 함수
def format_anchor_analysis(results, anchor_col, overall_value):
    lines = [f"✅ 전체 '{anchor_col}' 평균값은 **{overall_value}** 입니다.\n"]
    for category, data in results.items():
        lines.append(f"### [{category}] (F={data['f_value']}, p={data['p_value']}, {data['sig']})")
        for item in data["insights"]:
            lines.append(
                f"- '{item['소분류']}' 그룹의 '{anchor_col}' 값은 {item['값']}로 "
                f"전체 평균 대비 **{item['트렌드']}** (차이 {item['차이']})"
            )
        lines.append("")
    return "\n\n".join(lines)

# ✅ F/T test helper
def assign_significance_stars(p):
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    else:
        return "-"

def test_question_by_strata(df, strata_col, question_col):
    groups = df.groupby(strata_col)[question_col].apply(list)

    if len(groups) == 2:
        stat, p = ttest_ind(groups.iloc[0], groups.iloc[1], nan_policy='omit')
        method = "T-test"
    elif len(groups) >= 3:
        stat, p = f_oneway(*groups)
        method = "F-test (ANOVA)"
    else:
        return None

    return {
        "method": method,
        "statistic": stat,
        "p_value": p,
        "stars": assign_significance_stars(p)
    }

# ✅ 분석 handler 등록
analysis_handlers = {
    "anchor": anchor_table_analysis,
    "simple": simple_table_analysis,
    "unknown": unknown_table_analysis
}

# ✅ streamlit 노드 함수 (최종 통합)
def streamlit_numeric_analysis_node_fn(state):
    st.info("✅ [Numeric Analysis Agent] Start table numeric analysis")

    selected_table = state["selected_table"]
    raw_data_mapped = state.get("raw_data_mapped", None)
    selected_key = state["selected_key"]

    # ✅ 기존 anchor/simple 분석
    table_type = classify_table_type(selected_table)
    analysis_fn = analysis_handlers.get(table_type, unknown_table_analysis)
    basic_analysis = analysis_fn(selected_table)

    # ✅ ✅ ✅ streamlit 화면에 numeric analysis 출력
    st.subheader("📊 기본 Numeric Analysis 결과")
    st.markdown(basic_analysis)

    # ✅ 추가 F/T 분석
    ft_test_result = {}
    if raw_data_mapped is not None and selected_key in raw_data_mapped.columns:
        major_categories = selected_table["대분류"].dropna().unique()

        for major in major_categories:
            if major not in raw_data_mapped.columns:
                continue
            try:
                result = test_question_by_strata(raw_data_mapped, major, selected_key)
                if result:
                    result_str = (
                        f"[F/T 검정] {major} 기준: {result['method']} "
                        f"(F/T={abs(result['statistic']):.3f}, p={result['p_value']:.4f}) → {result['stars']}"
                    )
                    ft_test_result[major] = result_str
            except Exception as e:
                ft_test_result[major] = f"- [Error] {major} 검정 실패: {str(e)}"

    # ✅ ✅ ✅ streamlit 화면에 F/T 분석 결과 출력
    if ft_test_result:
        st.subheader("🎯 추가 F/T 검정 결과")
        for key, result in ft_test_result.items():
            st.markdown(f"- {key}: {result}")

    return {**state, "numeric_anaylsis": basic_analysis, "ft_test_result": ft_test_result}

# ✅ 노드 생성
streamlit_numeric_analysis_node = RunnableLambda(streamlit_numeric_analysis_node_fn)