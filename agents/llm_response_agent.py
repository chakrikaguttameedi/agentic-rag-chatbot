from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from core.mcp_protocol import mcp

# Load environment variables
load_dotenv()

class LLMResponseAgent:
    """Agent responsible for generating responses using Gemini 2.0 Flash"""
    
    def __init__(self):
        self.name = "LLMResponseAgent"
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.0-flash"
    
    def generate_response(self, query: str, trace_id: str) -> Dict[str, Any]:
        """Generate response using retrieved context"""
        print(f"🤖 {self.name}: Generating response for query: '{query}'")
        
        # Wait for context from RetrievalAgent
        message = mcp.receive_message(self.name)
        
        if not message or message.type != "CONTEXT_RESPONSE":
            print(f"❌ {self.name}: No context received from RetrievalAgent")
            return {
                "answer": "I apologize, but I couldn't retrieve relevant information to answer your question.",
                "sources": [],
                "error": "No context available"
            }
        
        retrieved_context = message.payload["retrieved_context"]
        
        # Build context from retrieved chunks
        context_text = ""
        sources = []
        
        for i, chunk in enumerate(retrieved_context):
            context_text += f"Document: {chunk['filename']}\n"
            context_text += f"Content: {chunk['text']}\n"
            context_text += f"Relevance Score: {chunk['score']:.3f}\n\n"
            
            sources.append({
                "filename": chunk["filename"],
                "chunk_id": chunk["chunk_id"],
                "score": chunk["score"],
                "preview": chunk["text"][:150] + "..." if len(chunk["text"]) > 150 else chunk["text"]
            })
        
        # Create prompt for Gemini
        prompt = f"""You are a helpful AI assistant that answers questions based on provided document context.

Context from documents:
{context_text}

User Question: {query}

Instructions:
1. Answer the question based ONLY on the provided context
2. Be specific and cite which documents you're referencing
3. If the context doesn't contain enough information to answer the question, say so
4. Provide a clear, concise, and helpful response
5. Do not make up information not present in the context

Answer:"""

        try:
            # Generate response using Gemini
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                ),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                response_mime_type="text/plain",
            )
            
            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                response_text += chunk.text
            
            print(f"✅ {self.name}: Response generated successfully")
            
            # Send response back to coordinator
            response_data = {
                "answer": response_text.strip(),
                "sources": sources,
                "query": query,
                "context_used": len(retrieved_context)
            }
            
            mcp.send_message(
                sender=self.name,
                receiver="CoordinatorAgent",
                message_type="RESPONSE_COMPLETE",
                trace_id=trace_id,
                payload=response_data
            )
            
            return response_data
            
        except Exception as e:
            print(f"❌ {self.name}: Error generating response: {str(e)}")
            error_response = {
                "answer": f"I apologize, but I encountered an error while generating the response: {str(e)}",
                "sources": sources,
                "error": str(e)
            }
            
            mcp.send_message(
                sender=self.name,
                receiver="CoordinatorAgent",
                message_type="RESPONSE_ERROR",
                trace_id=trace_id,
                payload=error_response
            )
            
            return error_response
    
    def test_connection(self) -> bool:
        """Test connection to Gemini API"""
        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="Hello, this is a test message.")],
                ),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                response_mime_type="text/plain",
            )
            
            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                response_text += chunk.text
                break  # Just test the first chunk
            
            print(f"✅ {self.name}: Gemini API connection successful")
            return True
            
        except Exception as e:
            print(f"❌ {self.name}: Gemini API connection failed: {str(e)}")
            return False 
