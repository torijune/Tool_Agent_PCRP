import pandas as pd

def analyze_by_category(df: pd.DataFrame) -> dict:
    """
    대분류별로 소분류에 따른 수치 변화를 분석합니다.
    """
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
    """
    그룹별 통계 분석 결과를 LLM에게 전달하기 위한 자연어 설명 형태로 변환
    """
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

        summary_sentences.append("")  # 줄바꿈

    return "\n".join(summary_sentences)

def numeric_analysis_node(state):

    selected_table = state["selected_table"]

    grouped = analyze_by_category(selected_table)
    insights = extract_insightful_analysis(grouped)

    numeric_anaylsis = format_insightful_analysis_to_text(insights)

    state["numeric_anaylsis"] = numeric_anaylsis
    
    return {**state, "numeric_anaylsis": numeric_anaylsis}