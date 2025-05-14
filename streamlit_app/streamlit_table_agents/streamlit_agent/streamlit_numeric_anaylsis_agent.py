import pandas as pd
import streamlit as st
from langchain_core.runnables import RunnableLambda
from scipy.stats import f_oneway

# -------------------------------
# 🎯 테이블 타입 분류 함수
# -------------------------------
def classify_table_type(df: pd.DataFrame):
    if any(col in df.columns for col in ["평균(5점척도)", "평균(4점척도)"]):
        return "anchor"
    elif "소분류" not in df.columns or df["소분류"].isna().all():
        return "simple"
    else:
        return "unknown"

# -------------------------------
# 🎯 분석 핸들러들
# -------------------------------
def anchor_table_analysis(df: pd.DataFrame):
    anchor_col = None
    if "평균(5점척도)" in df.columns:
        anchor_col = "평균(5점척도)"
    elif "평균(4점척도)" in df.columns:
        anchor_col = "평균(4점척도)"
    else:
        raise ValueError("anchor column 없음")

    # 전체 평균: 대분류가 '전체', '전 체'인 경우
    overall_value = df.loc[
        df["대분류"].astype(str).str.contains("전체|전 체|전", na=False), 
        anchor_col
    ].mean()

    results = {}
    # 🎯 소분류 개수 2개 이상 대분류만 분석
    valid_categories = (
        df.dropna(subset=["대분류", "소분류"])
          .groupby("대분류")["소분류"]
          .nunique()
          .loc[lambda x: x >= 2]
          .index.tolist()
    )

    for category in valid_categories:
        group_df = df[df["대분류"] == category].dropna(subset=["소분류"])

        # 🎯 F-test 수행 조건
        groups = [
            vals[anchor_col].dropna().values
            for _, vals in group_df.groupby("소분류")
        ]
        valid_groups = [g for g in groups if len(g) >= 2]
        f_value, p_value, sig = None, None, "-"

        if len(valid_groups) >= 2:
            try:
                f_value, p_value = f_oneway(*valid_groups)
            except:
                f_value, p_value = None, None

        # 🎯 유의성 표시
        if p_value is not None:
            if p_value < 0.001:
                sig = "***"
            elif p_value < 0.01:
                sig = "**"
            elif p_value < 0.05:
                sig = "*"

        # 🎯 인사이트: 전체 평균 대비 소분류별 차이
        insights = []
        for _, row in group_df.iterrows():
            subgroup = row["소분류"]
            value = row[anchor_col]
            if pd.isna(value):
                continue
            diff = round(value - overall_value, 2)
            if abs(diff) >= 0.1:  # 의미 있는 차이만
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

def simple_table_analysis(df: pd.DataFrame):
    lines = ["✅ 간단 Table 분석 결과입니다.\n"]
    numeric_cols = df.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        lines.append(f"- **{col}**: 평균={df[col].mean():.2f}, 표준편차={df[col].std():.2f}")
    return "\n".join(lines)

def unknown_table_analysis(df: pd.DataFrame):
    return "❌ 테이블 유형을 판단할 수 없어 분석을 건너뜁니다."

# -------------------------------
# 🎯 공통 결과 포맷 함수
# -------------------------------
def format_anchor_analysis(results, anchor_col, overall_value):
    lines = [f"✅ 전체 '{anchor_col}' 평균값은 **{overall_value}** 입니다.\n"]
    for category, data in results.items():
        f_val = data["f_value"]
        p_val = data["p_value"]
        sig = data["sig"]
        lines.append(f"### [{category}] (F={f_val}, p={p_val}, {sig})")
        for item in data["insights"]:
            lines.append(
                f"- '{item['소분류']}' 그룹의 '{anchor_col}' 값은 {item['값']}로 "
                f"전체 평균 대비 **{item['트렌드']}** (차이 {item['차이']})"
            )
        lines.append("")
    return "\n\n".join(lines)

# -------------------------------
# 🎯 Dispatcher dictionary
# -------------------------------
analysis_handlers = {
    "anchor": anchor_table_analysis,
    "simple": simple_table_analysis,
    "unknown": unknown_table_analysis
}

# -------------------------------
# 🎯 Streamlit node
# -------------------------------
def streamlit_numeric_analysis_node_fn(state):
    st.info("✅ [Numeric Analysis Agent] Start table numeric analysis")
    df = state["selected_table"]

    with st.spinner("표 데이터 분석 중..."):
        try:
            table_type = classify_table_type(df)
            handler = analysis_handlers.get(table_type, unknown_table_analysis)
            result = handler(df)
        except Exception as e:
            result = f"❌ 분석 실패: {str(e)}"

    st.markdown("### 📊 Numeric Analysis 결과")
    st.markdown(result)

    return {**state, "numeric_anaylsis": result}

streamlit_numeric_analysis_node = RunnableLambda(streamlit_numeric_analysis_node_fn)