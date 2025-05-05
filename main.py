from graph.workflow_graph import build_workflow_graph

workflow = build_workflow_graph()
result = workflow.invoke({
    "query": "파이썬으로 factorial(5)을 계산하는 코드를 실행해줘"
    })

print(result)