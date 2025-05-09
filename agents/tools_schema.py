import os

# ✅ 테이블 디렉토리 경로
TABLE_DIR = "agents/table_agents/table_list"

# ✅ 실제 파일명 리스트 (확장자 제거)
available_tables = [
    os.path.splitext(f)[0]
    for f in os.listdir(TABLE_DIR)
    if f.endswith(".csv") or f.endswith(".xlsx")
]

# ✅ table_analyzer 설명에 통합
tool_description = "\n".join([
    "- web_search: 최신 정보나 웹 기반 일반 지식을 검색할 때 사용합니다. (예: 특정 사건의 최근 뉴스, 일반 상식)",
    "- paper_abstract: 논문 초록을 분석하여 사용자의 질문에 관련된 연구 내용을 요약할 때 사용합니다. (예: RAG 관련 최신 연구 동향 요약)",
    "- table_analyzer: 다음과 같은 통계표 데이터를 분석할 때 사용합니다:"
] + [
    f"    - '{name}'" for name in available_tables
])

# ✅ Function Calling 스키마 구성
tools_schema = [
    {
        "name": "use_tool",
        "description": "사용자의 질문에 가장 적절한 도구를 선택합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "enum": ["web_search", "paper_abstract", "table_analyzer"],
                    "description": tool_description
                },
                "reason": {
                    "type": "string",
                    "description": "해당 도구를 선택한 이유를 간결하게 기술하세요."
                }
            },
            "required": ["tool_name"]
        }
    }
]