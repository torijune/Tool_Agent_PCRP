from table_graph.table_workflow_graph import build_table_graph

workflow = build_table_graph()
result = workflow.invoke({
    "file_path": "agents/table_agents/통계표_수정_서울시 대기환경 시민인식 조사_250421(작업용).xlsx"
})

print(result.get("table_analysis", "⚠️ table_analysis 존재하지 않습니다."))

# # Mermaid 기반 그래프 시각화
# with open("table_agent_workflow.png", "wb") as f:
#     f.write(workflow.get_graph(xray=True).draw_mermaid_png())