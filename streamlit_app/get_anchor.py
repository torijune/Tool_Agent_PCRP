import pandas as pd
import streamlit as st
from langchain_core.runnables import RunnableLambda

def get_anchor(df):
    exclude_cols = list(set([
        "대분류", "소분류", "사례수", 
        "관심없다 %", "보통 %", "관심있다 %",
        "관심없다%", "보통%", "관심있다%",
        "불만족 %", "만족 %",
        "불만족%", "만족%",
        "평균(5점척도)", "평균(4점척도)",
        "평균 (5점척도)", "평균 (4점척도)",
        "대분류_소분류"
    ]))

    # "전 체" -> "전체"와 같이 공백 제거 및 정규화
    total_row = df[df["대분류"].astype(str).str.strip().str.replace(" ", "") == "전체"]

    if total_row.empty:
        raise ValueError("❌ '전 체' 또는 '전체'에 해당하는 행이 존재하지 않습니다.")

    total_row = total_row.iloc[0]

    candidate_cols = [col for col in df.columns if col not in exclude_cols]
    values = total_row[candidate_cols]
    values_numeric = pd.to_numeric(values, errors='coerce')

    high_value_cols = values_numeric.dropna().sort_values(ascending=False)

    cumulative_sum = 0
    selected_cols = []
    for col, val in high_value_cols.items():
        cumulative_sum += val
        selected_cols.append(col)
        if cumulative_sum >= 60:
            break

    return selected_cols

def get_anchor_fn(state):
    selected_table = state.get("selected_table")
    if selected_table is None:
        st.error("❌ 'selected_table'이 state에 없습니다.")
        return state

    anchor = get_anchor(selected_table)
    st.text("선택된 anchor들: " + ", ".join(anchor))
    return {
        **state,
        "anchor": anchor
    }

get_anchor_node = RunnableLambda(get_anchor_fn)