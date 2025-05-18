import streamlit as st
import io
import os
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    # Try importing your custom modules with error handling
    try:
        from streamlit_table_workflow_graph import build_table_graph
        from streamlit_table_parser import load_survey_tables
    except ImportError as e:
        st.error(f"❌ Failed to import required modules: {e}")
        logger.error(f"Import error: {e}")
        st.stop()
except ImportError as e:
    st.error(f"❌ Failed to import dotenv: {e}")
    logger.error(f"Dotenv import error: {e}")
    st.stop()

# 🔑 환경 변수 로딩 (.env 로컬 + st.secrets 배포용)
try:
    load_dotenv()
    # Log API key status (without revealing the key)
    if "OPENAI_API_KEY" in os.environ:
        logger.info("OPENAI_API_KEY found in environment variables")
    
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
        logger.info("OPENAI_API_KEY loaded from st.secrets")
    else:
        logger.warning("OPENAI_API_KEY not found in st.secrets")
        
    # Verify API key is set
    if "OPENAI_API_KEY" not in os.environ:
        st.warning("⚠️ OPENAI_API_KEY not set. Some features may not work.")
        logger.warning("OPENAI_API_KEY not set in environment")
except Exception as e:
    st.error(f"❌ Error loading environment variables: {e}")
    logger.error(f"Environment error: {e}")

def normalize_key(key: str) -> str:
    return key.replace("-", "_").lower()

def main():
    try:
        st.set_page_config(page_title="Table Analysis Agent", layout="wide")
        st.title("📊 Table Analysis Multi-Agent Demo")

        st.markdown("""
        - Excel 통계표 기반 분석 자동화
        - Upload File → Parsing → Hypothesis → Numeric Analysis → Table Analysis → Hallucination Check → Revision → Polishing
        """)

        # ✅ 사이드바: 업로드
        with st.sidebar:
            st.header("1️⃣ 분석용 Excel 파일 업로드 (통계표)")
            uploaded_file = st.file_uploader("📥 분석용 Excel 파일을 선택하세요", type=None)

            st.header("2️⃣ 원시 데이터 Excel 파일 업로드 (Raw DATA, 변수, 코딩가이드, 문항 포함)")
            raw_data_file = st.file_uploader("📥 원시 데이터 Excel 파일을 선택하세요", type=None, key="raw_data")

            st.header("3️⃣ 분석 방식 선택")
            analysis_type = st.radio(
                "분석 방식",
                ["단일 질문 선택 - 직접 선택", "전체 질문 batch - 전체 자동 분석"],
                index=0
            )
            analysis_type_flag = analysis_type.startswith("단일")

        selected_question_key = None
        selected_table = None
        tables = None
        question_texts = None
        question_keys = None

        if uploaded_file:
            try:
                logger.info("Loading tables from uploaded file")
                file_bytes = io.BytesIO(uploaded_file.read())
                # Reset file pointer for future use
                uploaded_file.seek(0)
                
                tables, question_texts, question_keys = load_survey_tables(file_bytes)
                logger.info(f"Successfully loaded {len(tables)} tables")
            except Exception as e:
                logger.error(f"Error loading tables: {traceback.format_exc()}")
                st.error(f"❌ 업로드된 통계표 파일에서 테이블을 읽는 중 오류 발생: {str(e)}")
                st.stop()

            if analysis_type_flag and tables is not None:
                st.subheader("4️⃣ 분석할 질문 선택")
                st.info("📋 업로드한 분석용 Excel 파일의 질문 목록입니다. 분석할 질문을 선택하세요.")

                normalized_question_texts = {normalize_key(k): v for k, v in question_texts.items()}
                options = []
                for key in question_keys:
                    norm_key = normalize_key(key)
                    if norm_key in normalized_question_texts:
                        label = normalized_question_texts[norm_key]
                        options.append(f"[{key}] {label}")
                    else:
                        st.warning(f"⚠️ 질문 텍스트 누락: '{key}'")
                        logger.warning(f"Missing question text for key: {key}")

                if not options:
                    st.error("❌ 유효한 질문 텍스트가 없습니다.")
                    logger.error("No valid question texts found")
                    st.stop()

                selected_option = st.selectbox("질문 목록", options)
                selected_index = options.index(selected_option)
                selected_question_key = question_keys[selected_index]
                selected_table = tables[selected_question_key]

                st.success(f"✅ 선택된 질문: {question_texts.get(selected_question_key, selected_question_key)}")
                st.dataframe(selected_table.head(), use_container_width=True)
            elif not analysis_type_flag:
                st.info("📌 전체 batch 분석을 수행합니다. 각 질문은 자동 분석됩니다.")

        run = st.button("🚀 분석 시작", use_container_width=True)

        if run:
            if uploaded_file is None:
                st.error("❗ 분석용 Excel 파일을 먼저 업로드하세요.")
                logger.error("Analysis started without uploaded file")
                st.stop()
            if raw_data_file is None:
                st.error("❗ 원시 데이터 Excel 파일도 반드시 업로드해야 합니다.")
                logger.error("Analysis started without raw data file")
                st.stop()

            try:
                logger.info("Reading raw data file")
                raw_data_stream = io.BytesIO(raw_data_file.read())
                # Reset file pointer for future use
                raw_data_file.seek(0)
            except Exception as e:
                logger.error(f"Raw data file processing error: {traceback.format_exc()}")
                st.error(f"❌ 원시 데이터 파일 처리 오류: {str(e)}")
                st.stop()

            try:
                logger.info("Building table graph workflow")
                workflow = build_table_graph()
            except Exception as e:
                logger.error(f"Error building workflow: {traceback.format_exc()}")
                st.error(f"❌ 워크플로우 빌드 중 오류 발생: {str(e)}")
                st.stop()

            init_state = {
                "analysis_type": analysis_type_flag,
                "uploaded_file": io.BytesIO(uploaded_file.read()),
                "raw_data_file": raw_data_stream,
            }

            if analysis_type_flag and selected_question_key is not None:
                init_state["selected_key"] = selected_question_key

            try:
                logger.info("Invoking workflow")
                with st.spinner("분석 중... 잠시만 기다려주세요"):
                    result = workflow.invoke(init_state)
                logger.info("Workflow completed successfully")
            except Exception as e:
                logger.error(f"Workflow execution error: {traceback.format_exc()}")
                st.error(f"❌ 분석 실행 중 오류 발생: {str(e)}")
                st.stop()

            st.success("🎉 분석 완료!")

            if "polishing_result" in result:
                st.markdown("### 🔍 최종 요약 결과")
                st.text_area("Polished Report", result["polishing_result"], height=300)
            else:
                st.warning("⚠️ 최종 결과가 생성되지 않았습니다.")
                logger.warning("No polishing_result in workflow output")

            st.markdown("### 📝 전체 상태 보기")
            st.json(result)
    except Exception as e:
        logger.error(f"Unhandled exception: {traceback.format_exc()}")
        st.error(f"❌ 예상치 못한 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    main()