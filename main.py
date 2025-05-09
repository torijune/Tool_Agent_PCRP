from graph.workflow_graph import build_workflow_graph

def make_response(query):
    workflow = build_workflow_graph()
    result = workflow.invoke({
        "query": query
    })
    # # Mermaid 기반 그래프 시각화
    # with open("workflow_graph.png", "wb") as f:
    #     f.write(workflow.get_graph(xray=True).draw_mermaid_png())

    return result.get("final_answer", "⚠️ final_answer가 존재하지 않습니다.")

if __name__ == "__main__":
    query = str(input("질문을 입력하세요. : \n"))
    result = make_response(query)
    print(result)