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

            # Per-question analysis plan UI for batch mode
            if not analysis_type_flag and tables is not None:
                st.subheader("📌 질문별 분석 방식 설정")
                st.markdown("아래 표에서 각 질문별로 통계 분석 실행 여부와 분석 타입을 설정하세요.")
                st.info("💡 '집단간 차이 분석 실행 여부'를 체크하면 해당 질문에 대한 추천 분석 방식이 자동으로 표시됩니다.")

                user_analysis_plan = {}

                # 초기 데이터 준비 (추천 분석 방식 미리 계산)
                recommendations = {}
                for key in question_keys:
                    try:
                        selected_table = tables.get(key)
                        from table_analysis_decision_test_type import rule_based_test_type_decision
                        llm_result = rule_based_test_type_decision(selected_table.columns, question_texts.get(key, ""))
                        
                        if llm_result == "ft_test":
                            recommendations[key] = "추천 (F/T Test)"
                        elif llm_result == "chi_square":
                            recommendations[key] = "추천 (Chi-Square)"
                        else:
                            recommendations[key] = "추천 (임의 분석)"
                    except Exception as e:
                        logger.error(f"통계 검정 추천 오류 (key: {key}): {traceback.format_exc()}")
                        recommendations[key] = "추천 (임의 분석)"

                # 초기 세션 상태 설정 (한 번만)
                if "analysis_plan_state" not in st.session_state:
                    st.session_state["analysis_plan_state"] = {
                        key: {
                            "do_analyze": True,
                            "analysis_type": recommendations[key]
                        } for key in question_keys
                    }

                # 현재 상태 기반으로 테이블 데이터 구성
                plan_table_data = []
                for key in question_keys:
                    current_state = st.session_state["analysis_plan_state"][key]
                    
                    # 체크가 안 되어 있으면 분석 방식은 빈 문자열로 설정
                    analysis_type_display = current_state["analysis_type"] if current_state["do_analyze"] else ""
                    
                    plan_table_data.append({
                        "질문 Key": key,
                        "질문 내용": question_texts.get(key, ""),
                        "집단간 차이 분석 실행 여부": current_state["do_analyze"],
                        "통계 분석 방식": analysis_type_display
                    })

                import pandas as pd
                plan_df = pd.DataFrame(plan_table_data)

                # 데이터 에디터
                edited_df = st.data_editor(
                    plan_df,
                    column_config={
                        "질문 Key": st.column_config.TextColumn("질문 Key", width="small", disabled=True),
                        "질문 내용": st.column_config.TextColumn("질문 내용", width="large", disabled=True),
                        "집단간 차이 분석 실행 여부": st.column_config.CheckboxColumn("집단간 차이 분석 실행 여부", width="medium"),
                        "통계 분석 방식": st.column_config.SelectboxColumn(
                            "통계 분석 방식", 
                            options=["", "F/T Test", "Chi-Square", "임의 분석", "추천 (F/T Test)", "추천 (Chi-Square)", "추천 (임의 분석)"],
                            required=False,
                            width="medium"
                        )
                    },
                    use_container_width=True,
                    hide_index=True,
                    key="plan_editor"   
                )

                # 상태 업데이트 및 조건부 분석 방식 설정
                updated_state = {}
                for idx, row in edited_df.iterrows():
                    key = row["질문 Key"]
                    do_analyze = row["집단간 차이 분석 실행 여부"]
                    analysis_type = row["통계 분석 방식"]
                    
                    if do_analyze:
                        # 체크가 되어 있는데 분석 방식이 비어있으면 추천값으로 자동 설정
                        if not analysis_type or analysis_type == "":
                            analysis_type = recommendations[key]
                        updated_state[key] = {
                            "do_analyze": True,
                            "analysis_type": analysis_type
                        }
                    else:
                        # 체크가 해제되면 분석 방식도 빈 문자열로 초기화
                        updated_state[key] = {
                            "do_analyze": False,
                            "analysis_type": ""
                        }

                # 세션 상태 업데이트
                st.session_state["analysis_plan_state"] = updated_state

                # 최종 사용자 분석 계획 구성
                user_analysis_plan = {
                    key: {
                        "do_analyze": state["do_analyze"],
                        "analysis_type": state["analysis_type"]
                    }
                    for key, state in updated_state.items()
                }

                # 세션 상태에 저장
                st.session_state["user_analysis_plan"] = user_analysis_plan

                # 요약 정보 표시
                selected_count = sum(1 for state in updated_state.values() if state["do_analyze"])
                if selected_count > 0:
                    st.success(f"✅ 총 {selected_count}개 질문이 분석 대상으로 선택되었습니다.")
                else:
                    st.warning("⚠️ 분석할 질문이 선택되지 않았습니다.")

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
                        plan = st.session_state.get("user_analysis_plan", {}).get(key, {})
                        if not plan.get("do_analyze", True):
                            continue  # skip if not selected

                        analysis_type_value = plan.get("analysis_type", "자동")
                        override_type = None
                        if analysis_type_value == "F/T Test":
                            override_type = "ft_test"
                        elif analysis_type_value == "Chi-Square":
                            override_type = "chi_square"

                        init_state_loop = {
                            "analysis_type": False,
                            "selected_key": key.strip(),
                            "uploaded_file": io.BytesIO(uploaded_file_content),
                            "raw_data_file": io.BytesIO(raw_data_content),
                            "lang": lang
                        }

                        # If override_type is None, determine LLM-based test type and inject to init_state_loop
                        if override_type is None:
                            # 자동 결정 시 LLM 기반 통계 검정 방법 추천
                            selected_table = tables.get(key)
                            selected_key = normalize_key(key)

                            # test_type 추론을 위한 state 구성
                            llm_state = {
                                "analysis_type": False,
                                "selected_key": selected_key,
                                "selected_table": selected_table,
                                "lang": lang,
                                "user_analysis_plan": user_analysis_plan
                            }

                            # LLM 기반 test_type 결정 함수 호출
                            try:
                                from table_analysis_decision_test_type import streamlit_test_type_decision_fn
                                
                                llm_result = streamlit_test_type_decision_fn(llm_state)
                                inferred_test_type = llm_result.get("test_type", None)
                                if inferred_test_type in ["ft_test", "chi_square"]:
                                    init_state_loop["test_type_override"] = inferred_test_type
                                    # Update user_analysis_plan to show display-friendly type
                                    test_type_label = "F/T Test" if inferred_test_type == "ft_test" else "Chi-Square"
                                    user_analysis_plan[key]["analysis_type"] = f"추천 ({test_type_label})"
                                    st.session_state["user_analysis_plan"] = user_analysis_plan
                            except Exception as e:
                                logger.error(f"LLM test type decision error for key {key}: {traceback.format_exc()}")
                                # continue without test_type_override if error

                        else:
                            init_state_loop["test_type_override"] = override_type

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