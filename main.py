from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from agents.ingestion_agent import IngestionAgent
from agents.retrieval_agent import RetrievalAgent
from agents.llm_response_agent import LLMResponseAgent
from core.mcp_protocol import mcp

# Load environment variables
load_dotenv()

class CoordinatorAgent:
    """Main coordinator that orchestrates all agents"""
    
    def __init__(self):
        self.name = "CoordinatorAgent"
        self.ingestion_agent = IngestionAgent()
        self.retrieval_agent = RetrievalAgent()
        self.llm_agent = LLMResponseAgent()
        self.documents_processed = False
        
    def process_documents(self, file_paths: List[str]) -> bool:
        """Process documents through the agent pipeline"""
        print(f"🚀 {self.name}: Starting document processing pipeline...")
        
        # Generate trace ID for this operation
        trace_id = mcp.generate_trace_id()
        
        try:
            # Step 1: Ingestion Agent processes documents
            processed_docs = self.ingestion_agent.process_documents(file_paths, trace_id)
            
            # Step 2: Retrieval Agent builds vector store
            success = self.retrieval_agent.process_ingestion_message(trace_id)
            
            if success:
                self.documents_processed = True
                print(f"✅ {self.name}: Document processing pipeline completed successfully")
                return True
            else:
                print(f"❌ {self.name}: Failed to build vector store")
                return False
                
        except Exception as e:
            print(f"❌ {self.name}: Error in document processing: {str(e)}")
            return False
    
    def answer_question(self, query: str) -> Dict[str, Any]:
        """Answer user question using the agent pipeline"""
        if not self.documents_processed:
            return {
                "answer": "Please upload and process documents first before asking questions.",
                "sources": [],
                "error": "No documents processed"
            }
        
        print(f"🤔 {self.name}: Processing question: '{query}'")
        
        # Generate trace ID for this query
        trace_id = mcp.generate_trace_id()
        
        try:
            # Step 1: Retrieval Agent searches for relevant context
            self.retrieval_agent.search_documents(query, top_k=5, trace_id=trace_id)
            
            # Step 2: LLM Agent generates response
            response = self.llm_agent.generate_response(query, trace_id)
            
            print(f"✅ {self.name}: Question answered successfully")
            return response
            
        except Exception as e:
            print(f"❌ {self.name}: Error answering question: {str(e)}")
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}",
                "sources": [],
                "error": str(e)
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "documents_processed": self.documents_processed,
            "ingestion_stats": self.ingestion_agent.get_processing_stats(),
            "vector_store_stats": self.retrieval_agent.get_vector_store_stats(),
            "supported_formats": self.ingestion_agent.get_supported_formats()
        }
    
    def clear_system(self):
        """Clear all processed data"""
        self.retrieval_agent.clear_vector_store()
        self.ingestion_agent.processed_documents = []
        self.documents_processed = False
        mcp.clear_queue()
        print(f"🗑️ {self.name}: System cleared")
    
    def test_llm_connection(self) -> bool:
        """Test LLM connection"""
        return self.llm_agent.test_connection()

# Global coordinator instance
coordinator = CoordinatorAgent()

if __name__ == "__main__":
    print("🤖 Agentic RAG Chatbot Coordinator")
    print("Testing LLM connection...")
    
    if coordinator.test_llm_connection():
        print("✅ System ready!")
    else:
        print("❌ LLM connection failed. Please check your API key.")
        
    print("Use the Streamlit interface to interact with the system.")
    print("Run: streamlit run ui/streamlit_app.py")