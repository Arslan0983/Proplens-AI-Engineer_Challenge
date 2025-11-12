"""
Processes brochures (PDF/DOCX), chunks them, embeds them, and stores in ChromaDB for RAG.
"""

import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from django.conf import settings
from django.core.files.storage import default_storage
from PyPDF2 import PdfReader
import docx


class DocumentService:
    """Handles brochure processing - extracts text, chunks it, embeds it, stores it."""
    
    def __init__(self):
        self.chroma_client = chromadb.CloudClient(
            api_key=settings.CHROMADB_API_KEY,
            tenant=settings.CHROMADB_TENANT,
            database=settings.CHROMADB_DATABASE
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="brochures",
            metadata={"hnsw:space": "cosine"}
        )
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def extract_text(self, file_path: str, file_type: str) -> str:
        """Pull text out of PDF or DOCX files."""
        text = ""
        
        try:
            if file_type == 'pdf':
                reader = PdfReader(file_path)
                text = "\n".join([page.extract_text() for page in reader.pages])
            elif file_type in ['doc', 'docx']:
                doc = docx.Document(file_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            else:
                # Try to read as plain text
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
        
        return text
    
    def process_document(self, file_path: str, filename: str) -> int:
        """Process a document: extract, chunk, embed, and store in ChromaDB."""
        file_type = Path(filename).suffix.lower().lstrip('.')
        
        # Extract text
        text = self.extract_text(file_path, file_type)
        if not text:
            raise ValueError(f"Could not extract text from {filename}")
        
        # Split into chunks
        chunks = self.text_splitter.split_text(text)
        chunk_count = len(chunks)
        
        # Generate embeddings and store in ChromaDB
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{filename}_{uuid.uuid4()}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "filename": filename,
                "chunk_index": i,
                "file_type": file_type,
                "total_chunks": chunk_count
            })
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(documents).tolist()
        
        # Store in ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        return chunk_count
    
    def search_documents(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search documents using semantic search."""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else None
                })
        
        return formatted_results


# Singleton instance (lazy-loaded to avoid startup timeout)
_document_service: Optional[DocumentService] = None

def get_document_service() -> DocumentService:
    """Get or create document service instance (lazy-loaded)."""
    global _document_service
    if _document_service is None:
            logger.info("Initializing Document service (first use)...")
        _document_service = DocumentService()
    return _document_service

