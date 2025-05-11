from agents.table_agents.table_graph.table_workflow_graph import build_table_graph

def get_result(query: str):
    workflow = build_table_graph()
    result = workflow.invoke({"query": query})
    
    hallucination_check = result.get("hallucination_check", "")
    
    if hallucination_check == "accept":
        output = result.get("table_analysis", "⚠️ table_analysis 존재하지 않습니다.")
        return output
    elif hallucination_check == "reject":
        output = result.get("revised_analysis", "⚠️ revised_analysis 존재하지 않습니다.")
        return output
    else:
        return "⚠️ hallucination_check 값이 유효하지 않습니다."

# ⚠️ 아래 코드는 테스트 용도로만 사용되며 import 시 실행되지 않도록 보호됨
if __name__ == "__main__":
    # query = input("질문을 입력하세요: ")
    query = "고양시에서 수행하는 도시 주거 개발 계획에 대해서 궁금해"
    output = get_result(query)
    print(output)

    # # Mermaid 기반 그래프 시각화 (옵션)
    # with open("table_agent_workflow.png", "wb") as f:
    #     f.write(build_table_graph().get_graph(xray=True).draw_mermaid_png())