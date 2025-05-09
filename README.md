# Tool_Agent_PCRP

LangGraph 기반의 Tool-Using Agent 프로젝트입니다.  
이 에이전트는 다음과 같은 구조를 따릅니다:

> **P**lanning → **Tool Execution** → **Critic Evaluation** → (Re-)**Planning**
## System Overview

![System Overview](SystemOverview.png)

---

## 구성 개요

- **LangGraph**를 활용한 DAG 기반 에이전트 흐름
- **Planner**: LLM이 입력 질의에 대한 계획 수립
- **Tool Agent**: Function Calling 기반으로 적절한 도구 자동 실행
- **Critic**: 실행 결과 평가 및 accept/reject 판단
- **Replanning Loop**: 필요 시 다시 planner로 되돌아가 반복 수행

---

## Tool List

### Web Search Tool:
- Using duckduckgo_search API for web searching
    

### Top-Tier Conference Abstract Analysis Tool: 
- LangGraph Multi-Agent
    - Start → User Inpur Query → Abstracts Retrieval → Retrieved Documents Relevance Check → Critic Checker → Generation Output

![Abstract Analysis Tool Overview](AbstractFlow.png)

### Social Survey Structure data (like, table) analysis Tool: 
- LangGraph Multi-Agent
    - Start → User Inpur Query → Retrieval Survey File(excel, csv, ...) → Table Parser → Table Numeric Analysis(Pandas - mean, min, max , ...) → Table Analysis(Numeric + Linearlized Table + User Question) → Generated Analysis Result Hallucination Check → Critic Checker → Generation Output

![Social Survey Analysis Tool Overview](TableFlow.png)
---

Tool_Agent_PCRP/  
├── main.py  
├── graph/  
│   ├── workflow_graph.py  
│   └── table_workflow_graph.py  
│
├── agents/  
│   ├── tools.py  
│   ├── tools_schema.py  
│   ├── planner_agent.py  
│   ├── critic_agent.py  
│   ├── responder_agent.py  
│   ├── abstract_agents/  
│   │   ├── abstract_main.py  
│   │   ├── agents_B/  
│   │   │   ├── retriever_agent.py  
│   │   │   ├── relevance_checker_agent.py  
│   │   │   ├── answer_generator_agent.py  
│   │   │   └── hallucination_checker_agent.py  
│   │   └── abstract_graph/  
│   │       └── abstract_workflow_graph.py  
│   │
│   └── table_agents/  
│       ├── table_main.py  
│       ├── table_list/  
│       │   ├── 서울시_환경조사_2023.csv  
│       │   └── ...  
│       ├── agent_C/  
│       │   ├── retrieval_file_agent.py  
│       │   ├── table_parser.py  
│       │   ├── table_numeric_analyzer.py  
│       │   ├── table_analyzer.py  
│       │   ├── hallucination_checker.py  
│       │   └── revision_agent.py  
│       └── table_graph/  
│           └── table_workflow_graph.py  
│
├── tools/  
│   └── duckduckgo_search.py  
│
└── README.md  