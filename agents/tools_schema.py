function_schema = [
    {
        "name": "use_tool",
        "description": "사용자의 질문에 가장 적절한 도구를 선택합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "enum": ["web_search", "paper_abstract"]
                },
                "reason": {
                    "type": "string",
                    "description": "선택한 이유를 설명하세요."
                }
            },
            "required": ["tool_name"]
        }
    }
]