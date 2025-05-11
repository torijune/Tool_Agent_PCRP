import os
import openai

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

REVISION_PROMPT = """
당신은 통계 데이터를 바탕으로 인구집단 간 패턴과 경향성을 객관적으로 요약하는 데이터 분석 전문가입니다.

아래는 테이블 분석 결과에 대해 일부 잘못된 해석이 포함된 요약입니다. 피드백과 사전에 생성된 가설을 참고하여 잘못된 내용을 제거하고, 원본 데이터를 기반으로 수치 기반의 객관적 분석을 다시 작성할 것.

📝 설문 조사 질문:
{selected_question}

📊 표 데이터 (선형화된 형태):
{linearized_table}

📈 수치 분석 결과 (대분류별 항목별 최고/최저 값, 표준편차, 범위 등):
{numeric_anaylsis}

💡 사전에 생성된 가설 (참고용):
{generated_hypotheses}

📝 기존 요약 (잘못된 부분 포함):
{table_analysis}

❗ 피드백 (수정이 필요한 이유 또는 잘못된 부분):
{feedback}

---

Let's think step by step

🎯 수정 및 재작성 지침:

1. 주요 대분류 (예: 연령대, 기저질환 여부, 대기오염 배출사업장 유무, 주요 체류 공간 등)를 중심으로 분석할 것
2. 세부 소분류 (예: 성별, 20대/30대 등 세부 연령 구간)는 명확한 차이가 없을 경우 절대 언급하지 말 것
3. 의미 있는 차이가 나타나는 주요 그룹만 선택적으로 언급할 것
4. 모든 세부 그룹을 나열하지 말고, 특징적인 그룹과 주요 차이를 중심으로 요약할 것
5. 외부 배경지식, 주관적 해석 없이 오직 수치 기반의 사실만 작성할 것
6. 숫자 기반의 경향을 중심으로 "상대적으로 더 높은 경향 보였음", "낮은 값을 나타냈음" 등 **음슴체**로 작성할 것
7. 문장은 평서문이 아닌, **보고서 음슴체 스타일**로 작성할 것 (예: ~했음, ~로 나타났음)
8. 정확한 수치값은 쓰지 말고, 수치 차이에 기반한 경향만 서술할 것
9. 지나치게 단절적 (~했음. ~했음. 반복) 표현을 지양하고, 관련된 그룹들은 **자연스럽게 연결어를 사용해 한 문장으로 묶을 것**
10. 동일 의미의 그룹이 중복되지 않도록 주의할 것

---

📝 출력 형식:

- 제목, 불릿, 리스트 없이 서술형으로 작성할 것
- 짧고 명확하게 분석 결과만 요약할 것
- 아래 예시처럼 작성할 것

예시:
대기환경 문제 관심 정도, 연령대 높을수록 더 높은 경향 보였음. 기저질환 있는 그룹, 대기오염 배출사업장 주변 거주 그룹, 실외 체류시간 많은 그룹도 상대적으로 높은 관심 보였음.
"""

def revise_table_analysis_fn(state):
    print("\n********** Start table analysis revision **********")

    if state["hallucination_reject_num"] == 0:
        prompt = REVISION_PROMPT.format(
            selected_question=state["selected_question"],
            linearized_table=state["linearized_table"],
            numeric_anaylsis=state["numeric_anaylsis"],
            table_analysis=state["table_analysis"],
            feedback=state["feedback"],
            generated_hypotheses=state.get("generated_hypotheses", "해당 없음")
        )
    else:
        prompt = REVISION_PROMPT.format(
            selected_question=state["selected_question"],
            linearized_table=state["linearized_table"],
            numeric_anaylsis=state["numeric_anaylsis"],
            table_analysis=state["revised_analysis"],
            feedback=state["feedback"],
            generated_hypotheses=state.get("generated_hypotheses", "해당 없음")
        )

    response = llm.invoke(prompt)
    revised_analysis = response.content.strip()

    print("\n✅ 수정된 보고서:")
    print(revised_analysis)

    return {
        **state,
        "revised_analysis": revised_analysis
    }

revise_table_analysis_node = RunnableLambda(revise_table_analysis_fn)