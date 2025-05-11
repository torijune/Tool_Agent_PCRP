from table_parser import table_parser_node

def test_table_selection():
    # ✅ 엑셀 파일 경로 넣기 (실제 파일 경로로 바꿔주세요)
    file_path = "/Users/jang-wonjun/Desktop/Dev/Tool_Agent_PCRP/agents/table_agents/table_list/고양시 도시주거환경정비기본계획 조사.xlsx"

    # ✅ 초기 state 전달
    state = {"file_path": file_path}

    # ✅ 실행
    result = table_parser_node.invoke(state)

    # ✅ 결과 확인
    print("\n✅ 선택된 질문:")
    print(result["selected_question"])
    print("\n✅ 선택된 테이블 (상위 5개 행만 출력):")
    print(result["selected_table"].head())

if __name__ == "__main__":
    test_table_selection()