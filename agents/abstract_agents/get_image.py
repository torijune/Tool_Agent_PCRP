from abstract_graph.abstract_workflow_graph import build_abstract_graph
import json
from pathlib import Path

# 그래프 생성
workflow = build_abstract_graph()

with open("abstract_workflow_graph.png", "wb") as f:
    f.write(workflow.get_graph(xray=True).draw_mermaid_png())