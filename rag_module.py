# rag_module.py
import os
import pandas as pd
from typing import List, Dict
from langchain_gigachat.embeddings import GigaChatEmbeddings
from langchain_community.vectorstores import FAISS

class RAGManager:
    def __init__(self, gigachat_credentials: str, documents_path: str = "documents"):
        self.documents_path = documents_path
        self.embeddings = GigaChatEmbeddings(
            credentials=gigachat_credentials,
            verify_ssl_certs=False
        )
        self.vectorstore = None

    def add_documents_from_csv(self, csv_path: str, text_columns: List[str]) -> bool:
        try:
            if not os.path.exists(csv_path):
                return False
            df = pd.read_csv(csv_path)
            documents = []
            for _, row in df.iterrows():
                parts = [str(row[col]) for col in text_columns if col in df.columns and pd.notna(row[col])]
                if parts:
                    documents.append(" ".join(parts))
            if not documents:
                return False
            self.vectorstore = FAISS.from_texts(documents, self.embeddings)
            return True
        except Exception as e:
            print(f"RAG error: {e}")
            return False

    def search_qa_pairs(self, query: str, k: int = 2) -> List[Dict[str, str]]:
        if self.vectorstore is None:
            return []
        try:
            results = self.vectorstore.similarity_search(query, k=k)
            return [{"question": "N/A", "answer": doc.page_content} for doc in results]
        except:
            return []