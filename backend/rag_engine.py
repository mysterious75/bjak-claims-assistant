"""RAG Engine - Retrieval Augmented Generation for FAQ"""

import os
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader

from .llm_client import LLMClient


class RAGEngine:
    """RAG pipeline for insurance FAQ retrieval."""
    
    def __init__(self, llm_client: LLMClient, vectorstore_path: str = "./vectorstore"):
        self.llm = llm_client
        self.vectorstore_path = vectorstore_path
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
        self.vectorstore: Optional[Chroma] = None
    
    def ingest_documents(self, docs_dir: str = "./data/faq") -> int:
        """Load and ingest FAQ documents into vector store."""
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)
            return 0
        
        loader = DirectoryLoader(
            docs_dir,
            glob="**/*.txt",
            loader_cls=TextLoader,
            show_progress=True
        )
        
        documents = loader.load()
        if not documents:
            return 0
        
        # Split documents
        chunks = self.text_splitter.split_documents(documents)
        
        # Create/update vector store
        self.vectorstore = Chroma.from_documents(
            chunks,
            self.embeddings,
            persist_directory=self.vectorstore_path
        )
        
        return len(chunks)
    
    def load_vectorstore(self) -> bool:
        """Load existing vector store."""
        if os.path.exists(self.vectorstore_path):
            self.vectorstore = Chroma(
                persist_directory=self.vectorstore_path,
                embedding_function=self.embeddings
            )
            return True
        return False
    
    def query(
        self,
        question: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Query the RAG system."""
        if not self.vectorstore:
            if not self.load_vectorstore():
                return {"answer": "No knowledge base available.", "sources": []}
        
        # Retrieve relevant chunks
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": top_k}
        )
        
        docs = retriever.get_relevant_documents(question)
        
        if not docs:
            return {"answer": "No relevant information found.", "sources": []}
        
        # Build context
        context = "\n\n---\n\n".join([doc.page_content for doc in docs])
        sources = [
            {
                "content": doc.page_content[:200],
                "source": doc.metadata.get("source", "unknown"),
                "relevance": doc.metadata.get("score", 0)
            }
            for doc in docs
        ]
        
        # Generate answer
        prompt = f"""You are a helpful insurance FAQ assistant for BJAK.
Answer the question based ONLY on the context provided below.
If the context doesn't contain the answer, say "I don't have enough information to answer this."

Context:
{context}

Question: {question}

Answer:"""
        
        answer = self.llm.generate(prompt, temperature=0.2)
        
        return {
            "answer": answer,
            "sources": sources,
            "num_chunks": len(docs)
        }
    
    def add_document(self, content: str, metadata: Optional[Dict] = None) -> bool:
        """Add a single document to the vector store."""
        if not self.vectorstore:
            self.load_vectorstore()
        
        if not self.vectorstore:
            os.makedirs(self.vectorstore_path, exist_ok=True)
            self.vectorstore = Chroma.from_texts(
                [content],
                self.embeddings,
                persist_directory=self.vectorstore_path,
                metadatas=[metadata or {}]
            )
        else:
            self.vectorstore.add_texts(
                [content],
                metadatas=[metadata or {}]
            )
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        if not self.vectorstore:
            return {"status": "not_loaded", "document_count": 0}
        
        collection = self.vectorstore._collection
        return {
            "status": "loaded",
            "document_count": collection.count(),
            "vectorstore_path": self.vectorstore_path
        }
