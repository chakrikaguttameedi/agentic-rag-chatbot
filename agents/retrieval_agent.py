from typing import List, Dict, Any
from core.mcp_protocol import mcp
from core.vector_store import VectorStore

class RetrievalAgent:
    """Agent responsible for embedding and semantic retrieval"""
    
    def __init__(self):
        self.name = "RetrievalAgent"
        self.vector_store = VectorStore()
        self.is_initialized = False
    
    def process_ingestion_message(self, trace_id: str):
        """Process ingestion complete message and build vector store"""
        print(f"🔄 {self.name}: Waiting for ingestion message...")
        
        # Check for message from IngestionAgent
        message = mcp.receive_message(self.name)
        
        if message and message.type == "INGESTION_COMPLETE":
            print(f"📨 {self.name}: Received ingestion complete message")
            
            processed_documents = message.payload["processed_documents"]
            
            # Build vector store
            self.vector_store.add_documents(processed_documents)
            self.is_initialized = True
            
            print(f"✅ {self.name}: Vector store built successfully")
            
            # Send confirmation back
            mcp.send_message(
                sender=self.name,
                receiver="CoordinatorAgent",
                message_type="RETRIEVAL_READY",
                trace_id=trace_id,
                payload={
                    "status": "ready",
                    "vector_store_stats": self.vector_store.get_stats()
                }
            )
            
            return True
        return False
    
    def search_documents(self, query: str, top_k: int = 5, trace_id: str = None) -> List[Dict[str, Any]]:
        """Search for relevant document chunks"""
        if not self.is_initialized:
            print(f"❌ {self.name}: Vector store not initialized")
            return []
        
        print(f"🔍 {self.name}: Searching for: '{query}'")
        
        # Perform semantic search
        results = self.vector_store.search(query, top_k=top_k)
        
        # Format results for MCP message
        retrieved_chunks = []
        for result in results:
            chunk_info = {
                "text": result["chunk"],
                "filename": result["metadata"]["filename"],
                "score": result["score"],
                "chunk_id": result["metadata"]["chunk_id"]
            }
            retrieved_chunks.append(chunk_info)
        
        print(f"✅ {self.name}: Found {len(retrieved_chunks)} relevant chunks")
        
        # Send to LLMResponseAgent if trace_id provided
        if trace_id:
            mcp.send_message(
                sender=self.name,
                receiver="LLMResponseAgent",
                message_type="CONTEXT_RESPONSE",
                trace_id=trace_id,
                payload={
                    "retrieved_context": retrieved_chunks,
                    "query": query,
                    "total_results": len(retrieved_chunks)
                }
            )
        
        return retrieved_chunks
    
    def get_vector_store_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        if self.is_initialized:
            return self.vector_store.get_stats()
        return {"status": "not_initialized"}
    
    def clear_vector_store(self):
        """Clear the vector store"""
        self.vector_store.clear()
        self.is_initialized = False
        print(f"🗑️ {self.name}: Vector store cleared") 
