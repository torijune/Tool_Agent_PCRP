import os

from langchain_openai import OpenAIEmbeddings
import numpy as np
from langchain_core.runnables import RunnableLambda

TABLE_DIR = "agents/table_agents/table_list"
available_tables = os.listdir(TABLE_DIR)

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
    print("*" * 10, "Start table retrieval", "*" * 10)
    raw_query = state.get("query", "")

    # query가 dict로 wrapping 되어 있으면 내부 query만 사용
    if isinstance(raw_query, dict):
        query = raw_query.get("query", "")
    else:
        query = raw_query

    best_file, score = find_most_similar_table(query, available_tables)
    file_path = os.path.join(TABLE_DIR, best_file)

    return {
        **state,
        "file_path": file_path
    }

retrieval_table_node = RunnableLambda(retrieval_table_node_fn)