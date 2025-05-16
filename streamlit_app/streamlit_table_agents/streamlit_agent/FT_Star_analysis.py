# FT_Star_analysis.py
from langchain_core.runnables import RunnableLambda
import pandas as pd
import scipy.stats as stats
import io
import re
import streamlit as st

# ✅ 유의성 별 부여 함수
def assign_significance_stars(p_value):
    if p_value < 0.001:
        return "***"
    elif p_value < 0.01:
        return "**"
    elif p_value < 0.05:
        return "*"
    else:
        return ""

# ✅ DEMO 매핑 추출 함수
def extract_demo_mapping_from_dataframe(df, column="Unnamed: 0"):
    col = df[column].dropna().astype(str).reset_index(drop=True)
    cut_idx = None
    for i, val in enumerate(col):
        if val.strip() == 'DEMO1':
            cut_idx = i
            break
    sliced = col[:cut_idx] if cut_idx is not None else col

    demo_dict = {}
    for entry in sliced:
        entry = str(entry).strip()
        match = re.match(r"(DEMO\d+)[\s'\"]+(.+?)['\"\s\.]*$", entry)
        if match:
            key = match.group(1)
            label = match.group(2).strip()
            demo_dict[key] = label

    return demo_dict

# ✅ 자연어 요약 생성 함수
def summarize_ft_test(result_df: pd.DataFrame) -> str:
    significant = result_df[result_df["유의성"] != ""]
    non_significant = result_df[result_df["유의성"] == ""]

    strong = significant[significant["유의성"] == "***"]["대분류"].tolist()
    moderate = significant[significant["유의성"] == "**"]["대분류"].tolist()
    weak = significant[significant["유의성"] == "*"]["대분류"].tolist()

    summary = []

    if strong or moderate:
        items = strong + moderate
        summary.append(f"{', '.join(items)}는 통계적으로 유의한 차이를 보였음.")
    if weak:
        summary.append(f"{', '.join(weak)}도 유의미한 차이를 보였으나, 유의 수준은 상대적으로 낮았음.")

    # ✅ 유의한 항목이 전혀 없을 경우 → p-value 상위 3개 언급
    if significant.empty and not result_df.empty:
        top3 = result_df.nsmallest(3, "p-value")[["대분류", "p-value"]]
        top3_text = ", ".join(f"{row['대분류']} (p={row['p-value']})" for _, row in top3.iterrows())
        summary.append(f"통계적으로 유의한 항목은 없었지만, 상대적으로 p-value가 낮은 항목은 {top3_text} 순이었음.")

    return "  ".join(summary)

# ✅ F/T-test 실행 함수
def run_ft_test_df(df: pd.DataFrame, question_key: str, demo_dict: dict) -> pd.DataFrame:
    rows = []

    for demo_col, label in demo_dict.items():
        if demo_col not in df.columns:
            continue

        try:
            groups = df.groupby(demo_col)[question_key].apply(list)
            group_values = [pd.Series(values).dropna().tolist() for values in groups]

            if len(group_values) < 2:
                continue

            levene_stat, levene_p = stats.levene(*group_values)

            if len(group_values) == 2:
                test_stat, test_p = stats.ttest_ind(
                    group_values[0], group_values[1],
                    equal_var=(levene_p > 0.05)
                )
            else:
                test_stat, test_p = stats.f_oneway(*group_values)

            row = {
                "대분류": label,
                "통계량": round(abs(test_stat), 3),
                "p-value": round(test_p, 4),
                "유의성": assign_significance_stars(test_p)
            }
            rows.append(row)

        except Exception:
            continue

    result_df = pd.DataFrame(rows)
    return result_df

# ✅ LangGraph 노드 함수
def ft_star_analysis_node_fn(state: dict) -> dict:
    try:
        st.info("✅ [FT-Test Agent] 분석을 시작합니다...")

        raw_data_file = state["raw_data_file"]
        question_key = state["selected_key"]

        with st.spinner("🔍 F/T 분석 진행 중..."):

            raw_data = pd.read_excel(raw_data_file, sheet_name="DATA")
            demo_df = pd.read_excel(raw_data_file, sheet_name="DEMO")

            demo_mapping = extract_demo_mapping_from_dataframe(demo_df)
            result_df = run_ft_test_df(raw_data, question_key=question_key, demo_dict=demo_mapping)

            # ✅ Streamlit 출력
            st.markdown("### ✅ F/T 검정 결과")
            st.dataframe(result_df)

            # ✅ 자연어 요약 출력
            summary_text = summarize_ft_test(result_df)
            st.markdown("### 📄 자연어 요약 결과")
            st.write(summary_text)

            print("✅ F/T 분석 완료")

        return {
            **state,
            "raw_data": raw_data,
            "ft_test_result": result_df,
            "ft_test_summary": summary_text,
        }

    except Exception as e:
        print("❌ F/T 분석 중 오류:", e)
        st.error(f"❌ 분석 중 오류 발생: {e}")
        return {**state, "ft_test_result": {}, "ft_error": str(e)}

# ✅ LangGraph 노드 등록
streamlit_ft_star_analysis_node = RunnableLambda(ft_star_analysis_node_fn)