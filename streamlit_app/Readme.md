

# 📖 Table Analysis Agent: Automated Survey Reporting System

This tool provides an end-to-end automated pipeline for analyzing statistical survey tables using AI agents. Built with LangGraph and Streamlit, it transforms structured data into clean, readable summary reports.

---

## ✅ Core Components

- 📥 **Table Parser**: Extracts questions and statistical tables from uploaded Excel files.
- ✏️ **Hypothesis Generator**: Suggests plausible hypotheses based on table structure and question text.
- 🧭 **Test Type Selector**: Automatically determines the correct statistical test (F-test, T-test, etc.) to apply.
- 📊 **Statistical Analyzer**: Runs tests to detect significant patterns in numerical data.
- 📌 **Anchor Extractor**: Identifies key variables with the highest selection frequencies.
- 📝 **Table Summarizer**: Produces a first-draft summary based on anchors and statistical outcomes.
- 🧠 **Hallucination Checker**: Validates the accuracy of summaries using a secondary LLM agent.
- 🔁 **Reviser**: Iteratively corrects errors in the summary based on model feedback.
- 💅 **Polisher**: Refines the final report into a concise, coherent narrative.

---

## 🛠️ Getting Started

Follow these steps to begin analyzing your survey data with the Table Analysis Agent:

1. **Prepare and Upload Your Excel Files** via the sidebar:
   - 📊 **Summary Table File**: Should include sheet-wise frequency tables named after question identifiers (e.g., `Q1`, `SQ3`, etc.). Each table must summarize responses using counts and percentages.
   - 📂 **Raw Data File**: Must contain:
     - `DATA` — Row-wise raw responses and encoded demographic variables (e.g., `A1`, `DEMO1`, `DEMO2`)
     - `DEMO` — Human-readable descriptions of each demographic or derived variable
   - ✅ Ensure filenames are in English and contain no spaces or special characters to avoid upload issues.

2. **Select an Analysis Mode** from the sidebar:
   - 🧪 **Single-question analysis** — Choose a specific question to analyze manually
   - 📚 **Batch analysis** — Automatically process all questions in sequence

3. **Launch the Pipeline** by clicking the [🚀 Start Analysis] button.  
   Agents will execute in the following order: parsing → hypothesis generation → statistical testing → summarization → revision → polishing.

4. **Review Results**:
   - View intermediate outputs at each stage to understand the reasoning process.
   - Examine the final polished report, ready to be used in presentations or research documentation.