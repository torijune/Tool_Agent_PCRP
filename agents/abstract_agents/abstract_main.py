from abstract_graph.abstract_workflow_graph import build_abstract_graph

workflow = build_abstract_graph()
result = workflow.invoke({
    "query": "Structured data retrieval의 최신 논문들의 경향에 대해서 알려줘."
})

print(result.get("retrieved_doc", "⚠️ generated_analysis 존재하지 않습니다."))

# # Mermaid 기반 그래프 시각화
# with open("abstract_agent_workflow.png", "wb") as f:
#     f.write(workflow.get_graph(xray=True).draw_mermaid_png())