import pandas as pd
import re
from collections import defaultdict

import streamlit as st
from langchain_core.runnables import RunnableLambda

def load_survey_tables(file_obj, sheet_name: str = "통계표"):
    df = pd.read_excel(file_obj, sheet_name=sheet_name, header=None)
    pattern = r"^[A-Z]+\d*[-.]?\d*\."
    question_indices = df[df[0].astype(str).str.match(pattern)].index.tolist()

    tables, question_texts, question_keys = {}, {}, []
    key_counts = defaultdict(int)

    for i, start in enumerate(question_indices):
        end = question_indices[i + 1] if i + 1 < len(question_indices) else len(df)
        title = str(df.iloc[start, 0]).strip()
        match = re.match(pattern, title)
        if not match:
            continue
        base_key = match.group().rstrip(".")
        key_counts[base_key] += 1
        suffix = f"_{key_counts[base_key]}" if key_counts[base_key] > 1 else ""
        final_key = base_key + suffix

        question_texts[final_key] = title + "(전체 단위 : %)"
        question_keys.append(final_key)

        table = df.iloc[start + 1:end].reset_index(drop=True)
        if len(table) >= 2:
            new_columns = table.iloc[0].fillna('').astype(str) + " " + table.iloc[1].fillna('').astype(str)
            new_columns.iloc[0] = "대분류"
            if len(new_columns) > 1:
                new_columns.iloc[1] = "소분류"
            table = table.drop([0, 1]).reset_index(drop=True)
            table.columns = new_columns
            table["대분류"] = table["대분류"].ffill()
            table = table.dropna(axis=1, how='all').dropna(axis=0, how='all')
            table = table.drop(index=0).reset_index(drop=True)
            if len(table) > 2:
                table = table.iloc[:-2].reset_index(drop=True)

            for col in table.columns:
                try:
                    numeric_col = pd.to_numeric(table[col], errors='coerce')
                    if numeric_col.notna().any():
                        table[col] = numeric_col.round(1)
                except Exception:
                    continue

            tables[final_key] = table

    return tables, question_texts, question_keys

def linearize_row_wise(df):
    return " | ".join(
        ["; ".join([f"{col}: {val}" for col, val in row.items()]) for _, row in df.iterrows()]
    )

def table_parser_node_fn(state):
    analysis_type = state.get("analysis_type", True)
    uploaded_file = state.get("uploaded_file", None)
    selected_key = state.get("selected_key", None)   # ✅ app.py에서 넘긴 selected_key 사용

    if uploaded_file is None:
        st.warning("⚠️ 파일이 업로드되지 않았습니다. 파일을 먼저 업로드하세요.")
        st.stop()

    tables, question_texts, question_keys = load_survey_tables(uploaded_file)

    # ✅ selected_key가 state에 있다면 그대로 사용
    if selected_key is not None:
        selected_table = tables[selected_key]
        selected_question = question_texts[selected_key]

    # ✅ 단일 선택 모드 (streamlit에서 선택 → 비권장, 호환용)
    elif analysis_type:
        options = [f"[{key}] {question_texts[key]}" for key in question_keys]
        selected_option = st.selectbox("📝 질문 목록", options)
        selected_index = options.index(selected_option)
        selected_key = question_keys[selected_index]
        selected_table = tables[selected_key]
        selected_question = question_texts[selected_key]

    # ✅ batch 모드 → 전체 파일에서 첫 번째 테이블로 설정
    else:
        selected_key = question_keys[0]
        selected_table = tables[selected_key]
        selected_question = question_texts[selected_key]

    linearized_table = linearize_row_wise(selected_table)

    return {
        **state,
        "tables": tables,
        "question_texts": question_texts,
        "selected_table": selected_table,
        "table": tables,
        "selected_question": selected_question,
        "question_keys": question_keys,
        "selected_key": selected_key,
        "linearized_table": linearized_table,
    }

streamlit_table_parser_node = RunnableLambda(table_parser_node_fn)