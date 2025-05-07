from langchain_core.runnables import RunnableLambda
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema.document import Document
from typing import List
from dotenv import load_dotenv
import numpy as np
import json, os

load_dotenv()
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

DATA_PATH = "agents/abstract_agents/data/EMNLP_ACL_NAACL_Abstracts.json"
FAISS_PATH = "agents/abstract_agents/data/faiss_index"

def load_documents(path: str) -> List[Document]:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [
        Document(
            page_content=item["abstract"],
            metadata={"title": item.get("title", ""), "url": item.get("url", "")}
        )
        for item in data if item.get("abstract") and item.get("title")
    ]

if os.path.exists(FAISS_PATH):
    vectorstore = FAISS.load_local(FAISS_PATH,
                                   embeddings=embedding_model,
                                   index_name="papers",
                                   allow_dangerous_deserialization=True)
else:
    documents = load_documents(DATA_PATH)
    vectorstore = FAISS.from_documents(documents, embedding_model)
    vectorstore.save_local(FAISS_PATH, index_name="papers")

retriever = vectorstore.as_retriever(search_type="similarity", k=10)

# 🔹 수정된 retriever_node
def retriever_node(state: dict) -> dict:
    query = state["query"]
    plan_desc = state.get("plan_desc", "")

    # 두 쿼리 임베딩
    query_emb = embedding_model.embed_query(query)
    plan_emb = embedding_model.embed_query(plan_desc)

    # 전체 인덱스에서 벡터 추출
    faiss_index = vectorstore.index
    stored_vectors = faiss_index.reconstruct_n(0, faiss_index.ntotal)

    # cosine similarity 계산
    def cosine_sim(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)

    query_scores = [cosine_sim(query_emb, v) for v in stored_vectors]
    plan_scores = [cosine_sim(plan_emb, v) for v in stored_vectors]

    combined_scores = [(i, (q + p) / 2) for i, (q, p) in enumerate(zip(query_scores, plan_scores))]

    top_k = sorted(combined_scores, key=lambda x: x[1], reverse=True)[:5]

    # Top 5 문서 로깅
    print("\n Top 5 문서들과 Score 분석:")
    for i, combined_score in top_k:
        doc = vectorstore.docstore._dict[vectorstore.index_to_docstore_id[i]]
        print(f"- 제목: {doc.metadata['title']}")
        print(f"  ⤷ Query Score: {query_scores[i]:.4f}")
        print(f"  ⤷ Plan Score : {plan_scores[i]:.4f}")
        print(f"  ⤷ 평균 Score  : {combined_score:.4f}")

    docs = [vectorstore.docstore._dict[vectorstore.index_to_docstore_id[i]] for i, _ in top_k]

    combined = "\n\n".join([
        f"제목: {doc.metadata['title']}\n요약: {doc.page_content}"
        for doc in docs
    ])
    return {**state, "retrieved_doc": combined}

retriever_node = RunnableLambda(retriever_node)