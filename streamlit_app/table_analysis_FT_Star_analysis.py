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
def summarize_ft_test(result_df: pd.DataFrame, lang: str = "한국어") -> str:
    # 유의성 있는 항목(별이 하나 이상 붙은 항목) 필터링
    significant = result_df[result_df["유의성"] != ""]
    non_significant = result_df[result_df["유의성"] == ""]

    summary = []

    if not significant.empty:
        sig_items = significant["대분류"].tolist()
        if len(sig_items) == len(result_df):
            summary.append("모든 항목에서 통계적으로 유의미한 차이가 관찰되었음. 대분류 전반에 걸쳐 의미 있는 차이가 존재함." if lang == "한국어" else "All categories showed statistically significant differences. Broad variation was observed across major groups.")
        else:
            summary.append(f"{', '.join(sig_items)}는 통계적으로 유의한 차이를 보였음." if lang == "한국어" else f"{', '.join(sig_items)} showed statistically significant differences.")
    else:
        # 유의한 항목이 전혀 없을 경우 → p-value 기준 상위 3개 언급
        if not result_df.empty:
            top3 = result_df.nsmallest(3, "p-value")[["대분류", "p-value"]]
            top3_text = ", ".join(f"{row['대분류']} (p={row['p-value']})" for _, row in top3.iterrows())
            summary.append(f"통계적으로 유의한 항목은 없었지만, 상대적으로 p-value가 낮은 항목은 {top3_text} 순이었음." if lang == "한국어" else f"No items reached statistical significance, but the ones with the lowest p-values were: {top3_text}.")

    return "  ".join(summary)

def run_statistical_tests(test_type, df, question_key, demo_dict):
    # ✅ F/T-test 실행 함수
    def run_ft_test_df(df: pd.DataFrame, question_key: str, demo_dict: dict) -> pd.DataFrame:
        question_key = question_key.strip()
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
    
    def run_chi_square_test_df(df: pd.DataFrame, question_key: str, demo_dict: dict) -> pd.DataFrame:
        question_key = question_key.strip()
        if question_key not in df.columns:
            st.error(f"❌ 질문 항목 '{question_key}' 이(가) 데이터에 존재하지 않습니다.")
            return pd.DataFrame([])

        rows = []

        for demo_col, label in demo_dict.items():
            if demo_col not in df.columns:
                st.warning(f"❌ DEMO 컬럼 누락: {demo_col}")
                continue

            try:
                contingency_table = pd.crosstab(df[demo_col], df[question_key])

                if contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
                    st.info(f"⚠️ 스킵됨: {label} - 교차표 크기 부족")
                    continue

                chi2, p, dof, expected = stats.chi2_contingency(contingency_table)

                row = {
                    "대분류": label,
                    "통계량": round(chi2, 3),
                    "p-value": round(p, 4),
                    "유의성": assign_significance_stars(p)
                }
                rows.append(row)

            except Exception as e:
                st.error(f"❌ Chi-square 실패: {label} / {str(e)}")
                continue

        return pd.DataFrame(rows)
    
    if test_type == "ft_test":
        return run_ft_test_df(df, question_key, demo_dict)
    elif test_type =="chi_square":
        return run_chi_square_test_df(df, question_key, demo_dict)
    else:
        raise ValueError(f"❌ 잘못된 test_type: {test_type}")




# ✅ LangGraph 노드 함수
def ft_star_analysis_node_fn(state: dict) -> dict:
    try:

        raw_data_file = state["raw_data_file"]
        question_key = state["selected_key"].strip()
        test_type = state["test_type"]
        lang = state.get("lang", "한국어")

        st.info(f"✅ [FT-Test Agent] {test_type} 분석을 시작합니다..." if lang == "한국어" else f"✅ [FT-Test Agent] Starting {test_type} analysis...")

        with st.spinner("🔍 F/T 분석 진행 중..." if lang == "한국어" else "🔍 Running F/T analysis..."):

            raw_data = pd.read_excel(raw_data_file, sheet_name="DATA")
            demo_df = pd.read_excel(raw_data_file, sheet_name="DEMO")

            # ✅ 컬럼명 정규화: '-' → '_', 그리고 양쪽 공백 제거
            raw_data.columns = [col.replace("-", "_").strip() for col in raw_data.columns]

            demo_mapping = extract_demo_mapping_from_dataframe(demo_df)

            result_df = run_statistical_tests(test_type = test_type,
                                            df = raw_data,
                                            question_key=question_key,
                                            demo_dict=demo_mapping)

            # ✅ Streamlit 출력
            st.markdown("### ✅ F/T 검정 결과" if lang == "한국어" else "### ✅ F/T Test Results")
            st.dataframe(result_df)

            # ✅ 자연어 요약 출력
            summary_text = summarize_ft_test(result_df, lang=lang)
            st.markdown("### 📄 자연어 요약 결과" if lang == "한국어" else "### 📄 Natural Language Summary")
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
        st.error(f"❌ 분석 중 오류 발생: {e}" if lang == "한국어" else f"❌ Error during analysis: {e}")
        return {**state, "ft_test_result": {}, "ft_error": str(e)}

# ✅ LangGraph 노드 등록
streamlit_ft_star_analysis_node = RunnableLambda(ft_star_analysis_node_fn)