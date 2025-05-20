from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini", openai_api_key=os.getenv("OPENAI_API_KEY"))

AUDIENCE_ANALYSIS_PROMPT = {
    "한국어": """
당신은 전문적인 조사 설계 전문가입니다. 아래 조사 주제와 목적을 바탕으로 다양한 타겟 응답자 집단을 도출하고, 각 집단이 유의미한 이유를 함께 제시해주세요.

또한, 제시한 응답자 집단별로 사용할 수 있는 대표적인 표본 추출 방법(예: 단순무작위, 층화추출 등)과 통계적으로 신뢰도 95% 이상을 확보하기 위해 필요한 최소 표본 크기를 간략히 추정해주세요.

🧩 목표: 조사 목적에 따라 특성화된 응답자 프로필을 다양하게 제시하고, 사용자가 선택 가능하도록 제안하며 통계적으로 설계 가능한 기반 제공

📚 참고 정보: 주요 표본 추출 방법 요약

다음은 설문 조사 및 통계에서 자주 사용되는 표본 추출 방법입니다. 응답자 프로필을 설계할 때 참고하여 각 프로필에 적절한 표본 추출 방식을 추천하세요.

1. **단순무작위추출법**: 모든 모집단 구성원이 동일한 확률로 선택됨. 동질적이고 작은 모집단에 적합.  
2. **체계적 추출법**: 일정한 간격으로 선택. 명부가 정렬되어 있을 때 사용.  
3. **층화추출법**: 모집단을 성별/연령 등으로 나눈 뒤 각 층에서 무작위 추출. 이질적인 모집단에 적합.  
4. **군집추출법**: 지역, 조직 등으로 나눈 군집 중 일부를 선택하여 전체를 조사.  
5. **다단계 추출법**: 군집 추출 + 군집 내 무작위 추출을 조합. 대규모 지역조사에 유용.  
6. **편의추출법**: 접근 가능한 대상만 조사. 시간·비용 제약 시 사용하되 일반화 어려움.  
7. **판단추출법**: 조사자가 판단하여 선택. 전문가 의견 수집 시 적합.  
8. **할당추출법**: 인구 비율을 고려하여 할당된 수 만큼 각 집단에서 추출.  
9. **비례할당추출법**: 모집단 비율에 맞게 정확히 비례하여 추출함.

다음 단계를 따라주세요:

1. 조사 주제를 분석하여 관련된 주요 사회적/행동적/심리적 요인을 식별  
2. 각 요인과 관련 있는 인구통계학적 세그먼트를 기반으로 다양한 응답자 프로필(최소 10개 이상)을 작성  
3. 각 프로필마다 다음 항목을 포함할 것:  
   - (1) 응답자 정의  
   - (2) 조사 목적과의 관련성  
   - (3) 해당 프로필과 조사 목적/주제를 고려한 적절한 표본 추출 방법 및 그 이유  
   - (4) 통계적 유의성을 위해 필요한 최소 표본 크기 (대략적 추정, 이유 포함)  
4. 가능한 한 다양한 연령, 성별, 지역, 직업, 생활 패턴을 반영할 것

📌 조사 주제: {topic}
📌 조사 목적: {generated_objective}

---

📋 후보 응답자 프로필 + 표본 정보 목록:
""",

    "English": """
You are a professional survey planner. Based on the given topic and objective, generate a diverse set of target audience profiles, each with a short explanation of why it would be meaningful for the research.

Additionally, for each audience profile, recommend a suitable sampling method (e.g., simple random, stratified) and estimate the minimum sample size required to achieve statistical significance at the 95% confidence level.

🧩 Goal: Present specialized audience profiles based on the research objective, along with statistical guidance for implementation

📚 Reference: Overview of Sampling Methods

The following are common sampling methods used in surveys and statistics. Use these descriptions to help recommend appropriate sampling methods for each respondent profile.

1. **Simple Random Sampling**: Every population member has an equal chance of being selected. Best for small and homogeneous populations.  
2. **Systematic Sampling**: Select every N-th member from a list. Suitable when a list is available.  
3. **Stratified Sampling**: Divide population into strata (e.g., by gender, age) and sample from each. Good for heterogeneous populations.  
4. **Cluster Sampling**: Divide population into clusters (e.g., schools, regions), randomly select clusters, and survey all or some within.  
5. **Multi-Stage Sampling**: Combine cluster sampling with further sampling within clusters. Ideal for large-scale area surveys.  
6. **Convenience Sampling**: Survey accessible individuals. Fast and low-cost but lacks generalizability.  
7. **Judgmental Sampling**: Select samples based on researcher’s judgment. Used in expert-based studies.  
8. **Quota Sampling**: Select samples to meet predefined demographic quotas.  
9. **Proportionate Quota Sampling**: Quotas set in exact proportion to the population structure.

Please follow these steps:

1. Analyze the topic to identify key social/behavioral/psychological factors  
2. Create at least 10 respondent profiles based on demographic/lifestyle variables  
3. For each profile, include the following:  
   - (1) Profile definition  
   - (2) Why this group is relevant to the objective  
   - (3) Recommended sampling method tailored to the profile and research topic/objective (with justification)  
   - (4) Estimated minimum sample size needed for statistical confidence (with justification)  
4. Ensure diversity in age, gender, region, occupation, and lifestyle

📌 Topic: {topic}
📌 Objective: {generated_objective}

---

📋 Suggested Target Audience Profiles with Sampling Info:
"""
}

# ✅ LangGraph-compatible Node Function
def planner_audience_agent_fn(state):
    topic = state["topic"]
    generated_objective = state["generated_objective"]
    lang = state.get("lang", "한국어")

    prompt = AUDIENCE_ANALYSIS_PROMPT[lang].format(topic=topic, 
                                                   generated_objective=generated_objective)
    response = llm.invoke(prompt)
    import streamlit as st
    st.markdown("### 🧑‍🤝‍🧑 타겟 응답자 (Target Audience)" if lang == "한국어" else "### 🧑‍🤝‍🧑 Target Audience")
    st.info(response.content.strip())
    return {
        **state,
        "audience": response.content.strip()
    }

audience_agent_node = RunnableLambda(planner_audience_agent_fn)