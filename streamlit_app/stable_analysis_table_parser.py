import pandas as pd
import re
from collections import defaultdict
import streamlit as st
from langchain_core.runnables import RunnableLambda

# ✅ 정규화 함수
def normalize_key(key: str) -> str:
    return key.replace("-", "_").replace(".", "_")

def load_survey_tables(file_path: str, sheet_name: str = "통계표"):
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

    pattern = r"^[A-Z]+\d*[-.]?\d*\."
    question_indices = df[df[0].astype(str).str.match(pattern)].index.tolist()

    tables = {}
    question_texts = {}
    question_keys = []
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
        final_key_norm = normalize_key(final_key)

        question_texts[final_key_norm] = title + "(전체 단위 : %)"
        question_keys.append(final_key_norm)

        table = df.iloc[start + 1:end].reset_index(drop=True)

        if len(table) >= 2:
            first_header = table.iloc[0].fillna('').astype(str)
            second_header = table.iloc[1].fillna('').astype(str)

            title_text = None
            title_col_idx = None
            for idx, val in enumerate(first_header):
                if idx > 2 and isinstance(val, str) and len(val) > 0:
                    if val not in ['관심없다', '보통', '관심있다', '평균']:
                        title_text = val
                        title_col_idx = idx
                        break

            new_columns = []
            for idx in range(len(first_header)):
                if idx == 0:
                    new_columns.append("대분류")
                elif idx == 1:
                    new_columns.append("소분류")
                elif idx == 2:
                    new_columns.append("사례수")
                else:
                    first_val = "" if (title_col_idx is not None and first_header.iloc[idx] == title_text) else first_header.iloc[idx]
                    combined = (first_val + " " + second_header.iloc[idx]).strip().replace('nan', '').strip()
                    new_columns.append(combined)

            table = table.drop([0, 1]).reset_index(drop=True)
            table.columns = new_columns
            table = table.dropna(axis=1, how='all')
            table = table.dropna(axis=0, how='all')
            table["대분류"] = table["대분류"].ffill()
            table = table.dropna(subset=["대분류", "사례수"], how="all").reset_index(drop=True)
            if len(table) > 2:
                table = table.iloc[:-1].reset_index(drop=True)

            for col in table.columns:
                try:
                    numeric_col = pd.to_numeric(table[col], errors='coerce')
                    if numeric_col.notna().any():
                        table[col] = numeric_col.round(1)
                except:
                    continue

            tables[final_key_norm] = table

    return tables, question_texts, question_keys

def linearize_row_wise(df):
    return " | ".join(
        ["; ".join([f"{col}: {val}" for col, val in row.items()]) for _, row in df.iterrows()]
    )

def table_parser_node_fn(state):
    analysis_type = state.get("analysis_type", True)
    uploaded_file = state.get("uploaded_file", None)
    selected_key = state.get("selected_key", None)

    if uploaded_file is None:
        st.warning("⚠️ 통계표 엑셀 파일이 업로드되지 않았습니다. 파일을 먼저 업로드하세요.")
        st.stop()

    tables, question_texts, question_keys = load_survey_tables(uploaded_file)

    if selected_key is not None:
        selected_key = normalize_key(selected_key.strip())
        if selected_key not in tables:
            st.error(f"❌ 선택된 질문 키 '{selected_key}' 에 해당하는 테이블이 존재하지 않습니다.")
            st.stop()
        selected_table = tables[selected_key]
        selected_question = question_texts[selected_key]

    # 단일 질문일 경우
    elif analysis_type:
        options = [f"[{key}] {question_texts[key]}" for key in question_keys]
        selected_option = st.selectbox("📝 질문 목록", options)
        selected_index = options.index(selected_option)
        selected_key = normalize_key(question_keys[selected_index].strip())
        selected_table = tables[selected_key]
        selected_question = question_texts[selected_key]

    # 전체 질문에 대한 분석인 경우
    else:
        selected_key = normalize_key(question_keys[0].strip())
        selected_table = tables[selected_key]
        selected_question = question_texts[selected_key]

    linearized_table = linearize_row_wise(selected_table)

    return {
        **state,
        "tables": tables,
        "question_texts": question_texts,
        "selected_table": selected_table,
        "selected_question": selected_question,
        "question_keys": question_keys,
        "selected_key": selected_key,
        "linearized_table": linearized_table,
    }

streamlit_table_parser_node = RunnableLambda(table_parser_node_fn)