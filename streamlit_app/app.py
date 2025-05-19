import streamlit as st

from text_dictionary import TEXT

# ✅ 제일 먼저 페이지 설정
st.set_page_config(page_title="Table Analysis Agent", layout="wide")
import io
import os
import traceback
import logging

# 🌐 다국어 텍스트 (한-영)
lang = st.sidebar.radio("🌐 Language", ["English", "한국어"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    # Try importing your custom modules with error handling
    try:
        from table_analysis_graph import build_table_graph
        from stable_analysis_table_parser import load_survey_tables
        from planner_graph import planner_graph
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
        page = st.sidebar.radio("📄 Page", TEXT["page_selector"][lang])

        ######### 기본 메인 화면 #########
        if page == TEXT["page_selector"][lang][0]:
            st.title(TEXT["intro_title"][lang])
            st.markdown(TEXT["agent_overview"][lang])
            st.markdown(TEXT["usage_guide_title"][lang])
            st.markdown(TEXT["usage_guide"][lang])
            st.markdown(TEXT["mermaid_diagram_title"][lang])
            mermaid_code = """
            <div class="mermaid">
            graph TD
                A[📥 table_parser] --> B[✏️ hypothesis_generate_node]
                B --> C[🧭 test_decision_node]
                C --> D[📊 FT_anlysis_node]
                D --> E[📌 get_anchor_node]
                E --> F[📝 table_analyzer]
                F --> G[🧠 hallucination_check_node]

                G -- accept --> H[💅 sentence_polish_node]
                G -- reject < 4 --> I[🔁 revise_table_analysis]
                I --> G
                G -- reject ≥ 4 --> H

                H --> Z([✅ END])
            </div>
            <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({ startOnLoad: true });
            </script>
            """
            st.components.v1.html(mermaid_code, height=800)
            return

        ######### 통계 설계 도우미 페이지 #########
        if page == TEXT["page_selector"][lang][2]:
            st.title(TEXT["planner_page"]["title"][lang])
            st.markdown(TEXT["planner_page"]["description"][lang])

            topic = st.text_input(
                TEXT["planner_page"]["survey_topic"][lang],
                placeholder=TEXT["planner_page"]["survey_topic_ph"][lang]
            )
            objective_input = st.text_area(
                TEXT["planner_page"]["research_objectives"][lang],
                placeholder=TEXT["planner_page"]["research_objectives_ph"][lang]
            )

            if st.button(TEXT["planner_page"]["generate"][lang]):
                if not topic:
                    st.warning("📝 조사 주제를 입력해주세요." if lang == "한국어" else "📝 Please enter a survey topic.")
                    st.stop()

                with st.spinner("🔍 설문조사 설계 중..." if lang == "한국어" else "🔍 Planning your survey..."):
                    planner_result = planner_graph.invoke({
                        "topic": topic,
                        "objective": objective_input,
                        "lang": lang
                    })

                st.success("✅ 설문조사 설계가 완료되었습니다!" if lang == "한국어" else "✅ Survey planning completed!")

                st.markdown("### 🎯 조사 목적 (Objective)")
                st.info(planner_result["objective"])

                st.markdown("### 🧑‍🤝‍🧑 타겟 응답자 (Target Audience)")
                st.info(planner_result["audience"])

                st.markdown("### 🧱 설문 구조 (Survey Structure)")
                st.code(planner_result["structure"], language="markdown")

                st.markdown("### ✍️ 섹션별 문항 제안 (Questions)")
                st.code(planner_result["questions"], language="markdown")

                st.markdown("### 📊 분석 제안 및 고려사항 (Analysis)")
                st.code(planner_result["analysis"], language="markdown")
            return

        ######### 테이블 분석 보고서 작성 실행 화면 #########
        if page == TEXT["page_selector"][lang][1]:
            st.title(TEXT["run_page"]["title"][lang])

            st.info(TEXT["run_page"]["filename_warning"][lang])
            st.markdown(TEXT["run_page"]["filename_format"][lang])

            st.markdown(TEXT["run_page"]["flow_reminder"][lang])

            # ✅ 사이드바: 업로드
            with st.sidebar:
                st.header(TEXT["run_page"]["sidebar_file_upload"][lang])
                uploaded_file = st.file_uploader(TEXT["run_page"]["file_uploader_table_label"][lang], type=None)

                st.header(TEXT["run_page"]["sidebar_raw_upload"][lang])
                raw_data_file = st.file_uploader(TEXT["run_page"]["file_uploader_raw_label"][lang], type=None, key="raw_data")

                st.header(TEXT["run_page"]["sidebar_mode"][lang])
                analysis_type = st.radio(
                    "분석 방식",
                    TEXT["run_page"]["mode_options"][lang],
                    index=0
                )
                # For both languages, "Single Question" is always first
                if lang == "한국어":
                    analysis_type_flag = analysis_type.startswith("단일")
                else:
                    analysis_type_flag = analysis_type.startswith("Single")

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
                    st.error(f"{TEXT['run_page']['upload_table_error'][lang]} {str(e)}")
                    st.stop()

                if analysis_type_flag and tables is not None:
                    st.subheader(TEXT["run_page"]["select_question_header"][lang])
                    st.info(TEXT["run_page"]["select_question_info"][lang])

                    normalized_question_texts = {normalize_key(k): v for k, v in question_texts.items()}
                    options = []
                    for key in question_keys:
                        norm_key = normalize_key(key)
                        if norm_key in normalized_question_texts:
                            label = normalized_question_texts[norm_key]
                            options.append(f"[{key}] {label}")
                        else:
                            st.warning(f"{TEXT['run_page']['missing_question_warning'][lang]} '{key}'")
                            logger.warning(f"Missing question text for key: {key}")

                    if not options:
                        st.error(TEXT["run_page"]["no_valid_questions"][lang])
                        logger.error("No valid question texts found")
                        st.stop()

                    selected_option = st.selectbox(TEXT["run_page"]["selectbox_label"][lang], options)
                    selected_index = options.index(selected_option)
                    selected_question_key = question_keys[selected_index]
                    selected_table = tables[selected_question_key]

                    st.success(f"{TEXT['run_page']['selected_question'][lang]} {question_texts.get(selected_question_key, selected_question_key)}")
                    st.dataframe(selected_table.head(), use_container_width=True)
                elif not analysis_type_flag:
                    st.info(TEXT["run_page"]["batch_analysis_info"][lang])

            run = st.button(TEXT["run_page"]["run_button"][lang], use_container_width=True)

            if run:
                if uploaded_file is None:
                    st.error(TEXT["run_page"]["error_missing_file"][lang])
                    logger.error("Analysis started without uploaded file")
                    st.stop()
                if raw_data_file is None:
                    st.error(TEXT["run_page"]["error_missing_raw"][lang])
                    logger.error("Analysis started without raw data file")
                    st.stop()

                try:
                    logger.info("Reading raw data file")
                    raw_data_stream = io.BytesIO(raw_data_file.read())
                    # Reset file pointer for future use
                    raw_data_file.seek(0)
                except Exception as e:
                    logger.error(f"Raw data file processing error: {traceback.format_exc()}")
                    st.error(f"{TEXT['run_page']['raw_file_processing_error'][lang]} {str(e)}")
                    st.stop()

                try:
                    logger.info("Building table graph workflow")
                    workflow = build_table_graph()
                except Exception as e:
                    logger.error(f"Error building workflow: {traceback.format_exc()}")
                    st.error(f"{TEXT['run_page']['workflow_build_error'][lang]} {str(e)}")
                    st.stop()

                init_state = {
                    "analysis_type": analysis_type_flag,
                    "uploaded_file": io.BytesIO(uploaded_file.read()),
                    "raw_data_file": raw_data_stream,
                    "lang": lang
                }

                if analysis_type_flag and selected_question_key is not None:
                    init_state["selected_key"] = selected_question_key

                try:
                    logger.info("Invoking workflow")
                    with st.spinner(TEXT["run_page"]["analyzing_spinner"][lang]):
                        result = workflow.invoke(init_state)
                    logger.info("Workflow completed successfully")
                except Exception as e:
                    logger.error(f"Workflow execution error: {traceback.format_exc()}")
                    st.error(f"{TEXT['run_page']['workflow_execute_error'][lang]} {str(e)}")
                    st.stop()

                st.success(TEXT["run_page"]["analysis_done"][lang])

                if "polishing_result" in result:
                    st.markdown(TEXT["run_page"]["final_result_title"][lang])
                    st.text_area("Polished Report", result["polishing_result"], height=300)
                else:
                    st.warning(TEXT["run_page"]["no_result_warning"][lang])
                    logger.warning("No polishing_result in workflow output")
    except Exception as e:
        logger.error(f"Unhandled exception: {traceback.format_exc()}")
        st.error(f"{TEXT['run_page']['unexpected_error'][lang]} {str(e)}")

if __name__ == "__main__":
    main()