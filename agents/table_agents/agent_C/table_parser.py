import pandas as pd
import re
from collections import defaultdict

from langchain_core.runnables import RunnableLambda

'''
사용법: 
# 함수 사용법
tables, question_texts, question_keys = load_survey_tables("YOUR_FILE_PATH")

# 결과 확인
print("질문 Key 목록:", question_keys)
    e.g. [A1,A2,A2-1,A2_2, ...]

Question: question_texts.get("QUESTION_KEY"))
    e.g. A2에 대한 질문: question_texts.get("A2")
Table: tables["QUESTION_KEY"]
    e.g. A2에 대한 table: tables["A2"]
'''

def load_survey_tables(file_path: str, sheet_name: str = "통계표"):
    """
    엑셀 파일에서 서울시 대기환경 조사 설문표를 파싱하여
    테이블, 질문 문장, 질문 키 목록을 반환합니다.

    Args:
        file_path (str): 엑셀 파일 경로
        sheet_name (str): 읽어올 시트 이름 (기본값: "통계표")

    Returns:
        tables (dict): {질문 key: 설문 결과 테이블}
        question_texts (dict): {질문 key: 질문 전체 문장}
        question_keys (list): 질문 key 목록
    """

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

            table = table.dropna(axis=1, how='all')
            table = table.dropna(axis=0, how='all')

            table = table.drop(index=0).reset_index(drop=True)
            if len(table) > 2:
                table = table.iloc[:-2].reset_index(drop=True)

            # ✅ 소수점 첫째 자리까지 반올림 (숫자형으로 변환 후 처리)
            for col in table.columns:
                try:
                    numeric_col = pd.to_numeric(table[col], errors='coerce')
                    if numeric_col.notna().any():
                        table[col] = numeric_col.round(1)
                except:
                    continue

            tables[final_key] = table

    return tables, question_texts, question_keys

def linearize_row_wise(df):
    return " | ".join(["; ".join([f"{col}: {val}" for col, val in row.items()]) for _, row in df.iterrows()])

def select_table(tables, question_keys, question_texts, index):

    if index.isdigit():
        choice = int(index) - 1
        if choice < 0 or choice >= len(question_keys):
            raise ValueError("올바른 질문 번호를 입력하세요.")
        selected_key = question_keys[choice]
    elif index in question_keys:
        selected_key = index
    else:
        raise ValueError("입력한 값이 올바른 질문 번호 또는 키가 아닙니다.")

    selected_table = tables[selected_key]
    selected_question = question_texts[selected_key]
    return selected_table, selected_question

def table_parser_node_fn(state):
    analysis_type = state.get("analysis_type", True)   # ✅ 기본값 False
    print("*" * 10, "Start table parsing", "*" * 10)
    file_path = state["file_path"]
    table, question_texts, question_keys = load_survey_tables(file_path)

    # type = True -> each qeustion 따로 하나씩
    if analysis_type:
        # ✅ 모든 질문 목록 보여주기
        print("\n📝 질문 목록:")
        for idx, key in enumerate(question_keys):
            print(f"{idx + 1}. [{key}] {question_texts[key]}")

        # ✅ 특정 table 선택
        index = str(input("질문 index를 입력하세요: \n"))
        selected_table, selected_question = select_table(table, question_keys, question_texts, index)
    # type = False -> 모든 table questions 한번에 진행
    else:
        selected_table, selected_question = state["selected_table"], state["selected_question"]

    linearized_table = linearize_row_wise(selected_table)

    return {
        **state,
        "question_texts": question_texts,
        "selected_table": selected_table,
        "table": table,
        "selected_question": selected_question,
        "question_keys": question_keys,
        "linearized_table": linearized_table,
    }

table_parser_node = RunnableLambda(table_parser_node_fn)