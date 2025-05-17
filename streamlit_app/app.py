import streamlit as st
import io
import os

from dotenv import load_dotenv
from streamlit_table_agents.table_graph.streamlit_table_workflow_graph import build_table_graph
from streamlit_table_agents.streamlit_agent.utils.streamlit_table_parser import load_survey_tables

# 🔑 환경 변수 로딩 (.env 로컬 + st.secrets 배포용)
load_dotenv()
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

def normalize_key(key: str) -> str:
    return key.replace("-", "_").lower()

def main():
    st.set_page_config(page_title="Table Analysis Agent", layout="wide")
    st.title("📊 Table Analysis Multi-Agent Demo")

    st.markdown("""
    - Excel 통계표 기반 분석 자동화
    - Upload File → Parsing → Hypothesis → Numeric Analysis → Table Analysis → Hallucination Check → Revision → Polishing
    """)

    # ✅ 사이드바: 업로드
    with st.sidebar:
        st.header("1️⃣ 분석용 Excel 파일 업로드 (통계표)")
        uploaded_file = st.file_uploader("📥 분석용 Excel 파일을 선택하세요", type=["xlsx", "xls"])

        st.header("2️⃣ 원시 데이터 Excel 파일 업로드 (Raw DATA, 변수, 코딩가이드, 문항 포함)")
        raw_data_file = st.file_uploader("📥 원시 데이터 Excel 파일을 선택하세요", type=["xlsx", "xls"], key="raw_data")

        st.header("3️⃣ 분석 방식 선택")
        analysis_type = st.radio(
            "분석 방식",
            ["단일 질문 선택 - 직접 선택", "전체 질문 batch - 전체 자동 분석"],
            index=0
        )
        analysis_type_flag = analysis_type.startswith("단일")

    selected_question_key = None
    selected_table = None

    if uploaded_file:
        try:
            tables, question_texts, question_keys = load_survey_tables(uploaded_file)
        except Exception as e:
            st.error(f"❌ 업로드된 통계표 파일에서 테이블을 읽는 중 오류 발생: {e}")
            st.stop()

        if analysis_type_flag:
            st.subheader("4️⃣ 분석할 질문 선택")
            st.info("📋 업로드한 분석용 Excel 파일의 질문 목록입니다. 분석할 질문을 선택하세요.")

            # ✅ 정규화된 키 기반 옵션 생성
            normalized_question_texts = {
                normalize_key(k): v for k, v in question_texts.items()
            }

            options = []
            for key in question_keys:
                norm_key = normalize_key(key)
                if norm_key in normalized_question_texts:
                    label = normalized_question_texts[norm_key]
                    options.append(f"[{key}] {label}")
                else:
                    st.warning(f"⚠️ 질문 텍스트 누락: '{key}'")

            if not options:
                st.error("❌ 유효한 질문 텍스트가 없습니다.")
                st.stop()

            selected_option = st.selectbox("질문 목록", options)
            selected_index = options.index(selected_option)
            selected_question_key = question_keys[selected_index]
            selected_table = tables[selected_question_key]

            st.success(f"✅ 선택된 질문: {question_texts.get(selected_question_key, selected_question_key)}")
            st.dataframe(selected_table.head(), use_container_width=True)
        else:
            st.info("📌 전체 batch 분석을 수행합니다. 각 질문은 자동 분석됩니다.")

    run = st.button("🚀 분석 시작", use_container_width=True)

    if run:
        if uploaded_file is None:
            st.error("❗ 분석용 Excel 파일을 먼저 업로드하세요.")
            st.stop()
        if raw_data_file is None:
            st.error("❗ 원시 데이터 Excel 파일도 반드시 업로드해야 합니다.")
            st.stop()

        workflow = build_table_graph()

        init_state = {
            "analysis_type": analysis_type_flag,
            "uploaded_file": uploaded_file,
            "raw_data_file": raw_data_file,
        }

        if analysis_type_flag and selected_question_key is not None:
            init_state["selected_key"] = selected_question_key

        try:
            result = workflow.invoke(init_state)
        except Exception as e:
            st.error(f"❌ 분석 실행 중 오류 발생: {e}")
            st.stop()

        st.success("🎉 분석 완료!")

        # 결과 보여주기 (선택)
        if "polishing_result" in result:
            st.markdown("### 🔍 최종 요약 결과")
            st.text_area("Polished Report", result["polishing_result"], height=300)

        st.markdown("### 📝 전체 상태 보기")
        st.json(result)

if __name__ == "__main__":
    main()