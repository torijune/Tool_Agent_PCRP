import os
import streamlit as st

from langchain_openai import OpenAIEmbeddings
import numpy as np
from langchain_core.runnables import RunnableLambda

TABLE_DIR = "agents/table_agents/table_list"

embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)

def find_most_similar_table(query: str, filenames: list) -> str:
    query_vec = embedding_model.embed_query(query)
    file_vecs = [embedding_model.embed_query(fname) for fname in filenames]
    scores = [cosine_similarity(query_vec, v) for v in file_vecs]
    best_idx = int(np.argmax(scores))
    return filenames[best_idx], scores[best_idx]

def retrieval_table_node_fn(state: dict) -> dict:
    st.info("🔎 테이블 파일 자동 검색 또는 직접 선택")

    raw_query = state.get("query", "")

    # ✅ query가 dict로 wrapping 되어 있으면 내부 query만 사용
    if isinstance(raw_query, dict):
        query = raw_query.get("query", "")
    else:
        query = raw_query

    # ✅ Streamlit에서 직접 선택 or 자동 검색 옵션
    option = st.radio(
        "테이블 파일 선택 방법",
        ("자동 검색 (query 기반)", "수동 선택 (파일 리스트)"),
        index=0
    )

    file_list = os.listdir(TABLE_DIR)
    file_list = [f for f in file_list if f.endswith(".xlsx") or f.endswith(".csv")]

    if option == "자동 검색 (query 기반)":
        if query.strip() == "":
            st.warning("❗ query가 비어있어 자동 검색이 불가능합니다. 직접 선택을 권장합니다.")
            return state
        best_file, score = find_most_similar_table(query, file_list)
        st.success(f"✅ 선택된 파일: {best_file} (유사도: {score:.4f})")
        file_path = os.path.join(TABLE_DIR, best_file)
    else:
        selected_file = st.selectbox("📂 파일을 선택하세요", file_list)
        file_path = os.path.join(TABLE_DIR, selected_file)
        st.success(f"✅ 선택된 파일: {selected_file}")

    return {
        **state,
        "file_path": file_path
    }

streamlit_retrieval_table_node_st = RunnableLambda(retrieval_table_node_fn)