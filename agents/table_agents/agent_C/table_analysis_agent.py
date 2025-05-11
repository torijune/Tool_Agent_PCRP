import os
import openai

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

TABLE_PROMPT = """
당신은 통계 데이터를 바탕으로 인구집단 간 패턴과 경향성을 객관적으로 요약하는 데이터 분석 전문가입니다.

📝 설문 조사 질문:
{selected_question}

📊 표 데이터 (선형화된 형태):
{linearized_table}

📈 수치 분석 결과 (대분류별 항목별 최고/최저 값, 표준편차, 범위 등):
{numeric_anaylsis}

💡 데이터 기반 자동 생성 가설 목록 (참고용):
{generated_hypotheses}

---

Let's think step by step

🎯 분석 및 요약 지침:

1. 주요 대분류 (예: 연령대, 기저질환 여부, 대기오염 배출사업장 유무, 주요 체류 공간 등)를 중심으로 분석할 것
2. 세부 소분류 (예: 성별, 20대/30대 등 세부 연령 구간)는 명확한 차이가 없을 경우 절대 언급하지 말 것
3. 의미 있는 차이가 나타나는 주요 그룹만 선택적으로 언급할 것
4. 모든 세부 그룹을 나열하지 말고, 특징적인 그룹과 주요 차이를 중심으로 요약할 것
5. 외부 배경지식, 주관적 해석 없이 오직 수치 기반의 사실만 작성할 것
6. 숫자 기반의 경향을 중심으로 "상대적으로 더 높은 경향 보였음", "낮은 값을 나타냈음" 등 **음슴체**로 작성할 것
7. 문장은 평서문이 아닌, **보고서 음슴체 스타일**로 작성할 것 (예: ~했음, ~로 나타났음)
8. 지나치게 단절적 (~했음. ~했음. 반복) 표현을 지양하고, 관련된 그룹들은 **연결어를 활용해 한 문장으로 묶을 것**
9. 가독성을 높이기 위해 동일한 의미의 그룹이 중복되지 않도록 주의할 것
10. 보고서에 정확한 수치는 쓰지 말고, 수치 차이에 기반한 경향만 서술할 것
11. 위의 '데이터 기반 가설'을 참고해 해당 가설을 검증하거나 관련 경향성을 발견하려 노력할 것

---

📝 출력 형식:

- 제목, 불릿, 리스트 없이 서술형으로 작성할 것
- 짧고 명확하게 분석 결과만 요약할 것
- 아래 예시처럼 작성할 것

예시:
대기환경 문제 관심 정도, 연령대 높을수록 더 높은 경향 보였음. 기저질환 있는 그룹, 대기오염 배출사업장 주변 거주 그룹, 실외 체류시간 많은 그룹도 상대적으로 높은 관심 보였음.
"""

def table_anaylsis_node_fn(state):
    print("*" * 10, "Start table anaylzing", "*" * 10)
    linearized_table = state["linearized_table"]
    numeric_anaylsis = state["numeric_anaylsis"]
    selected_question = state["selected_question"]
    generated_hypotheses = state["generated_hypotheses"]

    response = llm.invoke(TABLE_PROMPT.format(selected_question = selected_question,
                                               linearized_table=linearized_table,
                                                 numeric_anaylsis=numeric_anaylsis,
                                                 generated_hypotheses = generated_hypotheses))
    table_analysis = response.content.strip()

    # print("💬 Table Anaylsis 시작")
    # print(f"📝 Linearlized Table:\n{linearized_table}")
    # print(f"📄 검색된 논문 요약 (미리보기):\n{retrieved_doc[:300]}...")
    print("생성된 보고서 초안 :", table_analysis)
    return {**state, "table_analysis": table_analysis}

table_anaylsis_node = RunnableLambda(table_anaylsis_node_fn)