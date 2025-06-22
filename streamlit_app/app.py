import streamlit as st

from text_dictionary import TEXT

# ✅ 제일 먼저 페이지 설정
st.set_page_config(page_title="Table Analysis Agent", layout="wide")
import io
import os
import traceback
import logging

# 🌐 다국어 텍스트 (한-영)
lang = st.sidebar.radio("🌐 Language", ["English", "한국어"], index=1)

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

################################## 단일 index 분석 실행 (analysis_type_flag: True) ##################################
                if analysis_type_flag and tables is not None:
                    # 어떤 질문에 대해서 진행할지 물어보기
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

                    # 질문 선택창
                    selected_option = st.selectbox(TEXT["run_page"]["selectbox_label"][lang], options)
                    selected_index = options.index(selected_option)
                    selected_question_key = question_keys[selected_index].strip()
                    selected_key = normalize_key(selected_question_key)
                    normalized_tables = {normalize_key(k): v for k, v in tables.items()}
                    normalized_questions = {normalize_key(k): v for k, v in question_texts.items()}
                    
                    if selected_key not in normalized_tables:
                        st.error(f"❌ 선택된 질문 키 '{selected_key}' 에 해당하는 테이블이 존재하지 않습니다.")
                        st.stop()
                    
                    selected_table = normalized_tables[selected_key]
                    selected_question = normalized_questions[selected_key]

                    st.success(f"{TEXT['run_page']['selected_question'][lang]} {selected_question}")
                    st.dataframe(selected_table.head(), use_container_width=True)
################################## 전체 질문 분석 실행 (analysis_type_flag: False) ##################################
                # question_keys에 있는 모든 index들에 대해서 analysis 진행 -> 어떻게?
                elif not analysis_type_flag:
                    st.info(TEXT["run_page"]["batch_analysis_info"][lang])

            # flag에 따라서 분석 과정을 실행 
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

                uploaded_file_content = uploaded_file.read()
                uploaded_file.seek(0)
                raw_data_content = raw_data_file.read()
                raw_data_file.seek(0)

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

                # 최종적으로 LangGraph로 전달할 state 정의
                init_state = {
                    "analysis_type": analysis_type_flag,
                    "uploaded_file": io.BytesIO(uploaded_file.read()),
                    "raw_data_file": raw_data_stream,
                    "lang": lang
                }

                if analysis_type_flag and selected_question_key is not None:
                    init_state["selected_key"] = selected_question_key

                # Single Question analysis
                if analysis_type_flag:
                    try:
                        logger.info("Invoking workflow")
                        if init_state.get("analysis_type", True):
                            with st.spinner(TEXT["run_page"]["analyzing_spinner"][lang]):
                                result = workflow.invoke(init_state)
                        else:
                            result = workflow.invoke(init_state)
                        logger.info("Workflow completed successfully")
                    except Exception as e:
                        logger.error(f"Workflow execution error: {traceback.format_exc()}")
                        st.error(f"{TEXT['run_page']['workflow_execute_error'][lang]} {str(e)}")
                        st.stop()

                    if init_state.get("analysis_type", True):
                        st.success(TEXT["run_page"]["analysis_done"][lang])

                        if "polishing_result" in result:
                            st.markdown(TEXT["run_page"]["final_result_title"][lang])
                            st.text_area("Polished Report", result["polishing_result"], height=300)
                        else:
                            st.warning(TEXT["run_page"]["no_result_warning"][lang])
                            logger.warning("No polishing_result in workflow output")
                # Batch analysis for all questions
                elif not analysis_type_flag:
                    all_results = {}
                    for key in question_keys:
                        logger.info(f"Running batch analysis for question key: {key}")
                        init_state_loop = {
                            # Used to suppress logging and UI for batch mode
                            "analysis_type": False,  # Used to suppress logging and UI for batch mode
                            "selected_key": key.strip(),
                            "uploaded_file": io.BytesIO(uploaded_file_content),
                            "raw_data_file": io.BytesIO(raw_data_content),
                            "lang": lang
                        }
                        try:
                            result = workflow.invoke(init_state_loop)
                            if "polishing_result" in result:
                                all_results[key] = result["polishing_result"]
                        except Exception as e:
                            logger.error(f"Workflow execution error for key {key}: {traceback.format_exc()}")
                            st.error(f"❌ {key} 분석 중 오류 발생: {str(e)}")
                            continue

                    combined_result = "\n\n---\n\n".join(f"### [{k}]\n{v}" for k, v in all_results.items())
                    st.markdown(TEXT["run_page"]["final_result_title"][lang])
                    st.text_area("Combined Polished Report", combined_result, height=500)
                    return
    except Exception as e:
        logger.error(f"Unhandled exception: {traceback.format_exc()}")
        st.error(f"{TEXT['run_page']['unexpected_error'][lang]} {str(e)}")

if __name__ == "__main__":
    main()