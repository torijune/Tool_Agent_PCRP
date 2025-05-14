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

import pandas as pd
from collections import defaultdict
import re

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

        question_texts[final_key] = title + "(전체 단위 : %)"
        question_keys.append(final_key)

        table = df.iloc[start + 1:end].reset_index(drop=True)

        if len(table) >= 2:
            # 테이블 제목 제거 및 컬럼명 설정
            first_header = table.iloc[0].fillna('').astype(str)
            second_header = table.iloc[1].fillna('').astype(str)
            
            # 테이블 제목 식별하기
            title_text = None
            title_col_idx = None
            
            # 사례수 다음에 나오는 테이블 제목 찾기
            for idx, val in enumerate(first_header):
                if idx > 2 and isinstance(val, str) and len(val) > 0:  # 대분류, 소분류, 사례수 이후
                    # 이 값이 테이블 제목인지 확인 (다른 컬럼에는 없고 이 컬럼에만 있는 텍스트)
                    if val not in ['관심없다', '보통', '관심있다', '평균']:
                        title_text = val
                        title_col_idx = idx
                        break
            
            # 새로운 컬럼명 생성
            new_columns = []
            
            for idx in range(len(first_header)):
                if idx == 0:
                    new_columns.append("대분류")
                elif idx == 1:
                    new_columns.append("소분류")
                elif idx == 2:
                    new_columns.append("사례수")
                else:
                    # 테이블 제목이 있는 경우 제거
                    first_val = "" if (title_col_idx is not None and 
                                      first_header.iloc[idx] == title_text) else first_header.iloc[idx]
                    
                    # 두 헤더 결합
                    combined = (first_val + " " + second_header.iloc[idx]).strip()
                    combined = combined.replace('nan', '').strip()
                    
                    new_columns.append(combined)
            
            table = table.drop([0, 1]).reset_index(drop=True)
            table.columns = new_columns

            # 불필요한 빈 컬럼/행 제거
            table = table.dropna(axis=1, how='all')
            table = table.dropna(axis=0, how='all')

            # 대분류 채우기
            table["대분류"] = table["대분류"].ffill()

            # 마지막 요약행 (예: 합계 등) 제거
            if len(table) > 2:
                table = table.iloc[:-2].reset_index(drop=True)

            # 숫자 컬럼 반올림
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