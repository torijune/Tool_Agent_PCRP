from abstract_graph.abstract_workflow_graph import build_workflow_graph

workflow = build_workflow_graph()
result = workflow.invoke({
    "query": "Structured data retrieval"
})

print(result)

# Mermaid 기반 그래프 시각화
with open("abstract_agent_workflow.png", "wb") as f:
    f.write(workflow.get_graph(xray=True).draw_mermaid_png())