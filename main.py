from IPython.display import display, Image
from graph.workflow_graph import build_workflow_graph

workflow = build_workflow_graph()
result = workflow.invoke({
    "query": "파이썬으로 factorial(5)을 계산하는 코드를 실행해줘"
})

print(result)

# Mermaid 기반 그래프 시각화
with open("workflow_graph.png", "wb") as f:
    f.write(workflow.get_graph(xray=True).draw_mermaid_png())