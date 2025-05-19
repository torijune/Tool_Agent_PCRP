import streamlit as st

# ✅ 제일 먼저 페이지 설정
st.set_page_config(page_title="Table Analysis Agent", layout="wide")
import io
import os
import traceback
import logging

# 🌐 다국어 텍스트 (한-영)
lang = st.sidebar.radio("🌐 Language", ["English", "한국어"])

TEXT = {
    "page_selector": {
        "English": ["📖 Service Introduction", "🧪 Run Analysis"],
        "한국어": ["📖 서비스 소개", "🧪 분석 실행"]
    },
    "run_page": {
        "title": {
            "한국어": "📊 Table Statistical Analysis Multi-Agent",
            "English": "📊 Table Statistical Analysis Multi-Agent"
        },
        "filename_warning": {
            "한국어": "⚠️ **업로드할 파일 이름은 반드시 영문 또는 숫자로 구성되어야 합니다.**",
            "English": "⚠️ **The uploaded file name must consist only of English letters or numbers.**"
        },
        "filename_format": {
            "한국어": "한글, 공백, 특수문자가 포함된 경우 업로드가 실패할 수 있습니다. 예: `data_2024.xlsx` ✅",
            "English": "If your file name includes Korean, spaces, or special characters, upload may fail. Example: `data_2024.xlsx` ✅"
        },
        "flow_reminder": {
            "한국어": "- Excel 통계표 기반 분석 자동화\n- Upload File → Parsing → Hypothesis → Numeric Analysis → Table Analysis → Hallucination Check → Revision → Polishing",
            "English": "- Automated analysis of Excel-based summary tables\n- Upload File → Parsing → Hypothesis → Numeric Analysis → Table Analysis → Hallucination Check → Revision → Polishing"
        },
        "sidebar_file_upload": {
            "한국어": "1️⃣ 분석용 Excel 파일 업로드 (통계표)",
            "English": "1️⃣ Upload Excel File for Analysis (Summary Table)"
        },
        "sidebar_raw_upload": {
            "한국어": "2️⃣ 원시 데이터 Excel 파일 업로드 (Raw DATA, 변수, 코딩가이드, 문항 포함)",
            "English": "2️⃣ Upload Raw Data Excel File (Raw DATA, variables, code guide, questions)"
        },
        "sidebar_mode": {
            "한국어": "3️⃣ 분석 방식 선택",
            "English": "3️⃣ Select Analysis Mode"
        },
        "mode_options": {
            "English": ["Single Question - Manual Selection", "Batch All Questions - Full Auto Analysis"],
            "한국어": ["단일 질문 선택 - 직접 선택", "전체 질문 batch - 전체 자동 분석"]
        },
        "select_question_header": {
            "한국어": "4️⃣ 분석할 질문 선택",
            "English": "4️⃣ Select Question for Analysis"
        },
        "select_question_info": {
            "한국어": "📋 업로드한 분석용 Excel 파일의 질문 목록입니다. 분석할 질문을 선택하세요.",
            "English": "📋 This is a list of questions from the uploaded Excel. Please select one for analysis."
        },
        "no_valid_questions": {
            "한국어": "❌ 유효한 질문 텍스트가 없습니다.",
            "English": "❌ No valid question text found."
        },
        "selectbox_label": {
            "한국어": "질문 목록",
            "English": "Question List"
        },
        "selected_question": {
            "한국어": "✅ 선택된 질문:",
            "English": "✅ Selected Question:"
        },
        "run_button": {
            "한국어": "🚀 분석 시작",
            "English": "🚀 Start Analysis"
        },
        "error_missing_file": {
            "한국어": "❗ 분석용 Excel 파일을 먼저 업로드하세요.",
            "English": "❗ Please upload the analysis Excel file first."
        },
        "error_missing_raw": {
            "한국어": "❗ 원시 데이터 Excel 파일도 반드시 업로드해야 합니다.",
            "English": "❗ You must also upload the raw data Excel file."
        },
        "analyzing_spinner": {
            "한국어": "분석 중... 잠시만 기다려주세요",
            "English": "Analyzing... please wait a moment"
        },
        "analysis_done": {
            "한국어": "🎉 분석 완료!",
            "English": "🎉 Analysis complete!"
        },
        "final_result_title": {
            "한국어": "### 🔍 최종 요약 결과",
            "English": "### 🔍 Final Summary Result"
        },
        "no_result_warning": {
            "한국어": "⚠️ 최종 결과가 생성되지 않았습니다.",
            "English": "⚠️ No final result was generated."
        },
        "upload_table_error": {
            "한국어": "❌ 업로드된 통계표 파일에서 테이블을 읽는 중 오류 발생:",
            "English": "❌ Error reading tables from uploaded summary Excel file:"
        },
        "raw_file_processing_error": {
            "한국어": "❌ 원시 데이터 파일 처리 오류:",
            "English": "❌ Error processing raw data file:"
        },
        "workflow_build_error": {
            "한국어": "❌ 워크플로우 빌드 중 오류 발생:",
            "English": "❌ Error occurred while building the workflow:"
        },
        "workflow_execute_error": {
            "한국어": "❌ 분석 실행 중 오류 발생:",
            "English": "❌ Error occurred during workflow execution:"
        },
        "unexpected_error": {
            "한국어": "❌ 예상치 못한 오류가 발생했습니다:",
            "English": "❌ An unexpected error occurred:"
        },
        "file_uploader_table_label": {
            "한국어": "📥 분석용 Excel 파일을 선택하세요",
            "English": "📥 Select an Excel file for analysis"
        },
        "file_uploader_raw_label": {
            "한국어": "📥 원시 데이터 Excel 파일을 선택하세요",
            "English": "📥 Select a raw data Excel file"
        },
        "batch_analysis_info": {
            "한국어": "📌 전체 batch 분석을 수행합니다. 각 질문은 자동 분석됩니다.",
            "English": "📌 Batch analysis will be performed for all questions automatically."
        },
        "missing_question_warning": {
            "한국어": "⚠️ 질문 텍스트 누락:",
            "English": "⚠️ Missing question text:"
        }
    },
    "intro_title": {
        "한국어": "📖 Table Analysis Agent 소개",
        "English": "📖 Introduction to Table Analysis Agent"
    },
    "agent_overview": {
        "한국어": """
이 서비스는 통계 조사 결과표를 기반으로 자동으로 데이터를 분석하고 요약해주는 멀티 에이전트 기반 플랫폼입니다.

### ✅ 사용되는 주요 에이전트 구성:
- 📥 **Table Parser**: 업로드한 엑셀 파일에서 설문 문항과 통계 테이블을 자동으로 파싱
- ✏️ **Hypothesis Generator**: 테이블에 기반한 초기 분석 가설 자동 생성
- 🧭 **Test Type Decision**: 통계적 검정 방식(F-test, T-test 등) 자동 판단
- 📊 **F/T-Test Analyzer**: 수치 데이터를 기반으로 통계적 유의성 검정 수행
- 📌 **Anchor Extractor**: 테이블에서 가장 두드러진 대분류 항목(anchor)을 추출
- 📝 **Table Analyzer**: 수치와 anchor를 바탕으로 초기 요약 보고서 생성
- 🧠 **Hallucination Checker**: 보고서의 오류 여부 판단 (LLM 기반 검증)
- 🔁 **Reviser**: 잘못된 요약을 피드백 기반으로 수정
- 💅 **Polisher**: 최종 요약을 자연스럽고 간결하게 다듬는 역할
""",
        "English": """
This service is a multi-agent platform that analyzes and summarizes statistical survey tables using AI agents.

### ✅ Main agents used:
- 📥 **Table Parser**: Parses survey questions and summary tables from the uploaded Excel
- ✏️ **Hypothesis Generator**: Automatically generates initial hypotheses based on the table
- 🧭 **Test Type Decision**: Determines appropriate statistical tests (F-test, T-test, etc.)
- 📊 **F/T-Test Analyzer**: Performs statistical significance testing based on numerical data
- 📌 **Anchor Extractor**: Identifies salient categories (anchors) within the table
- 📝 **Table Analyzer**: Drafts initial summary based on stats and anchors
- 🧠 **Hallucination Checker**: Detects errors in LLM-generated reports
- 🔁 **Reviser**: Fixes inaccurate summaries based on LLM feedback
- 💅 **Polisher**: Refines the final summary to be fluent and concise
"""
    },
    "usage_guide": {
        "한국어": """
1. 사이드바에서 **분석용 통계표 파일**과 **원시 데이터 파일**을 업로드합니다.  
    - 두 파일은 모두 **엑셀(xlsx, xls)** 형식이며 파일명은 **영문** 형태여야 합니다.
    - 분석용 파일에는 설문 문항별 통계 요약 테이블이 포함되어 있어야 하며, 각 시트 이름은 문항 키(예: Q1, SQ3 등)로 되어 있어야 합니다.  
    - 원시 데이터 파일에는 최소한 다음 시트가 포함되어야 합니다: `DATA`, `DEMO`
        - `DATA`: 각 문항들(A1, A1_1, ...)에 대한 설문 조사 결과 + 표본 특성별로 전처리가 된 변수(DEMO1, DEMO2, ...)
        - `DEMO`: 표본 특성별 변수들(DEMO1, DEMO2, ...)에 대한 설명
    - 통계표는 범주형 값에 대한 빈도 및 비율을 포함하고 있어야 하며, 결측값은 제거되어 있어야 합니다.
2. 분석 방식으로 **단일 문항 분석** 또는 **전체 자동 분석(batch)** 중 하나를 선택합니다.
3. [🚀 분석 시작] 버튼을 클릭하면, 위의 에이전트들이 순차적으로 실행됩니다.
4. 분석 결과는 단계별로 출력되며, 마지막에는 polished된 최종 보고서를 확인할 수 있습니다.
5. 필요 시 최종 보고서를 복사하여 편집하거나 외부 보고서로 활용하세요.
""",
        "English": """
1. Upload the **statistical summary table** and the **raw data file** from the sidebar.  
    - Both files must be in **Excel format (xlsx, xls)**, and filenames should consist of **English characters only**.
    - The summary table should contain tabulated survey results, with each sheet named using the question key (e.g., Q1, SQ3).
    - The raw data file must include at least the following sheets: `DATA`, `DEMO`
        - `DATA`: Contains individual survey responses (e.g., A1, A1_1, ...) and preprocessed demographic variables (e.g., DEMO1, DEMO2, ...)
        - `DEMO`: Descriptions of the demographic variables (DEMO1, DEMO2, ...)
    - The summary tables must include frequency and percentage data for categorical variables and exclude missing values.
2. Choose either **single-question analysis** or **batch analysis for all questions**.
3. Click the [🚀 Start Analysis] button to run each agent in sequence.
4. The results will be shown step-by-step, and the final polished report will appear at the end.
5. Copy and edit the final report as needed for documentation or reporting.
"""
    },
    "usage_guide_title": {
        "한국어": "### 🛠️ 사용 방법 안내:",
        "English": "### 🛠️ How to Use This Service:"
    },
    "mermaid_diagram_title": {
        "한국어": "### 🧠 멀티에이전트 분석 흐름도 (Mermaid Diagram)",
        "English": "### 🧠 Multi-Agent Workflow Diagram (Mermaid)"
    }
}

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

        page = st.sidebar.radio("📄 Page", TEXT["page_selector"][lang])

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