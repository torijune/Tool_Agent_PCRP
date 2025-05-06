from langchain_core.runnables import RunnableLambda
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.schema.document import Document
from typing import List
from dotenv import load_dotenv
from tqdm import tqdm
import json, os

load_dotenv()
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

DATA_PATH = "agents/abstract_agents/data/EMNLP_ACL_NAACL_Abstracts.json"
FAISS_PATH = "agents/abstract_agents/data/faiss_index"

# 🔹 문서 로딩 함수
def load_documents(path: str) -> List[Document]:
    print(f"📄 문서 로딩 중: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    filtered = [
        Document(
            page_content=item["abstract"],
            metadata={"title": item.get("title", ""), "url": item.get("url", "")}
        )
        for item in data if item.get("abstract") and item.get("title")
    ]
    print(f"✅ 총 유효 문서 수: {len(filtered)}")
    return filtered

if os.path.exists(FAISS_PATH):
    print("📁 기존 FAISS 인덱스를 로드합니다.")
    vectorstore = FAISS.load_local(FAISS_PATH, 
                                   embeddings=embedding_model, 
                                   index_name="papers", 
                                   allow_dangerous_deserialization=True)
else:
    print("🆕 새로 임베딩하고 FAISS 인덱스를 생성합니다.")
    documents = load_documents(DATA_PATH)

    class TrackedEmbedding(OpenAIEmbeddings):
        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            print(f"🔍 총 문서 수: {len(texts)} → 임베딩 시작")
            for _ in tqdm(range(len(texts)), desc="📦 Embedding 진행 중", unit="docs"):
                pass
            return super().embed_documents(texts)

    tracked_model = TrackedEmbedding(model="text-embedding-3-small")
    vectorstore = FAISS.from_documents(documents, tracked_model)
    vectorstore.save_local(FAISS_PATH, index_name="papers")
    print("✅ FAISS 인덱스 저장 완료")

# 🔹 Retriever 구성
print("🔗 Retriever 구성 완료")
retriever = vectorstore.as_retriever(search_type="similarity", k=3)

# 🔹 LangGraph용 node로 사용될 함수 정의
def retriever_node(state: dict) -> dict:
    query = state["query"]
    print(f"🔎 질의 처리 중: \"{query}\"")
    docs = retriever.get_relevant_documents(query)
    print(f"📚 관련 문서 수: {len(docs)}")

    combined = "\n\n".join([
        f"제목: {doc.metadata['title']}\n요약: {doc.page_content}"
        for doc in docs
    ])
    return {**state, "retrieved_doc": combined}

retriever_node = RunnableLambda(retriever_node)