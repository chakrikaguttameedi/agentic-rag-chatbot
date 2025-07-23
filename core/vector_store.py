import faiss
import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
import json
import os

class VectorStore:
    """FAISS-based vector store for semantic search"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize vector store with sentence transformer model"""
        self.model = SentenceTransformer(model_name)
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.chunks = []  # Store actual text chunks
        self.metadata = []  # Store metadata for each chunk
        
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the vector store"""
        all_chunks = []
        all_metadata = []
        
        for doc in documents:
            filename = doc['filename']
            chunks = doc['chunks']
            doc_metadata = doc['metadata']
            
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                chunk_metadata = {
                    'filename': filename,
                    'chunk_id': i,
                    'doc_metadata': doc_metadata,
                    'chunk_text': chunk[:100] + "..." if len(chunk) > 100 else chunk
                }
                all_metadata.append(chunk_metadata)
        
        if all_chunks:
            # Generate embeddings
            print(f"🔄 Generating embeddings for {len(all_chunks)} chunks...")
            embeddings = self.model.encode(all_chunks, convert_to_tensor=False)
            
            # Normalize embeddings for cosine similarity
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Add to FAISS index
            self.index.add(embeddings.astype('float32'))
            
            # Store chunks and metadata
            self.chunks.extend(all_chunks)
            self.metadata.extend(all_metadata)
            
            print(f"✅ Added {len(all_chunks)} chunks to vector store")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks using semantic similarity"""
        if self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_tensor=False)
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks):  # Valid index
                result = {
                    'chunk': self.chunks[idx],
                    'metadata': self.metadata[idx],
                    'score': float(score)
                }
                results.append(result)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        return {
            'total_chunks': self.index.ntotal,
            'dimension': self.dimension,
            'model': self.model.get_sentence_embedding_dimension()
        }
    
    def clear(self):
        """Clear the vector store"""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunks = []
        self.metadata = []
        print("🗑️ Vector store cleared") 
