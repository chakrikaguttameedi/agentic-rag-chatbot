import streamlit as st
import os
import sys
from pathlib import Path
import time

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from main import coordinator

# Page config
st.set_page_config(
    page_title="Agentic RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'documents_uploaded' not in st.session_state:
    st.session_state.documents_uploaded = False
if 'processing' not in st.session_state:
    st.session_state.processing = False

def save_uploaded_file(uploaded_file):
    """Save uploaded file to uploads directory"""
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return str(file_path)

def display_sources(sources):
    """Display source information without nested expanders"""
    if sources:
        for i, source in enumerate(sources):
            st.markdown(f"**Source {i+1}:** `{source['filename']}`")
            st.markdown(f"> {source['preview']}")
            st.markdown("---")

def main():
    st.title("🤖 Agentic RAG Chatbot")
    st.markdown("### Multi-Format Document QA with Model Context Protocol")
    
    # Sidebar for document upload and system status
    with st.sidebar:
        st.header("📁 Document Upload")
        
        uploaded_files = st.file_uploader(
            "Upload your documents",
            type=['pdf', 'pptx', 'docx', 'csv', 'txt', 'md'],
            accept_multiple_files=True,
            help="Supported formats: PDF, PPTX, DOCX, CSV, TXT, MD"
        )
        
        if uploaded_files and not st.session_state.processing:
            if st.button("🚀 Process Documents", type="primary"):
                st.session_state.processing = True
                
                with st.spinner("Processing documents..."):
                    file_paths = []
                    for uploaded_file in uploaded_files:
                        file_path = save_uploaded_file(uploaded_file)
                        file_paths.append(file_path)
                        st.success(f"Saved: {uploaded_file.name}")
                    
                    success = coordinator.process_documents(file_paths)
                    
                    if success:
                        st.session_state.documents_uploaded = True
                        st.session_state.processing = False
                        st.success("✅ Documents processed successfully!")
                        st.rerun()
                    else:
                        st.session_state.processing = False
                        st.error("❌ Failed to process documents")
        
        st.header("🔧 System Status")
        status = coordinator.get_system_status()
        
        if status['documents_processed']:
            st.success("✅ System Ready")
            
            ingestion_stats = status['ingestion_stats']
            vector_stats = status['vector_store_stats']
            
            st.metric("Documents", ingestion_stats['total_documents'])
            st.metric("Text Chunks", ingestion_stats['total_chunks'])
            st.metric("Vector Dimension", vector_stats.get('dimension', 'N/A'))
            
            if ingestion_stats['formats_processed']:
                st.subheader("📊 Document Formats")
                for fmt, count in ingestion_stats['formats_processed'].items():
                    st.text(f"{fmt.upper()}: {count}")
        else:
            st.warning("⏳ Upload documents to get started")
        
        if st.button("🗑️ Clear System"):
            coordinator.clear_system()
            st.session_state.documents_uploaded = False
            st.session_state.chat_history = []
            st.success("System cleared!")
            st.rerun()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("💬 Chat Interface")
        
        for i, (question, answer, sources) in enumerate(st.session_state.chat_history):
            st.markdown(f"**You:** {question}")
            st.markdown(f"**Assistant:** {answer}")
            
            if sources:
                display_sources(sources)
            
            st.divider()
        
        if st.session_state.documents_uploaded:
            with st.form("query_form"):
                query = st.text_input(
                    "Ask a question about your documents:",
                    placeholder="What are the key findings in the uploaded documents?"
                )
                submit_button = st.form_submit_button("Ask Question", type="primary")
                
                if submit_button and query.strip():
                    with st.spinner("Generating answer..."):
                        response = coordinator.answer_question(query.strip())
                        
                        st.session_state.chat_history.append((
                            query.strip(), 
                            response['answer'], 
                            response.get('sources', [])
                        ))
                        
                        st.rerun()
        else:
            st.info("📤 Please upload and process documents first to start asking questions.")
    
    with col2:
        st.header("🔍 Agent Architecture")
        
        st.markdown("""
        **Agent Flow:**
        1. 🔄 **IngestionAgent**
           - Parses documents
           - Creates text chunks
        
        2. 🔍 **RetrievalAgent** 
           - Builds vector store
           - Performs semantic search
        
        3. 🤖 **LLMResponseAgent**
           - Uses Gemini 2.0 Flash or Hugging Face LLM
           - Generates contextual answers
        
        **MCP Protocol:**
        - Structured message passing
        - Trace ID tracking
        - Agent coordination
        """)
        
        st.header("ℹ️ System Info")
        st.json({
            "Model": "HuggingFace: flan-t5-base",
            "Vector Store": "FAISS",
            "Embeddings": "SentenceTransformers",
            "Supported Formats": ["PDF", "PPTX", "DOCX", "CSV", "TXT", "MD"]
        })

if __name__ == "__main__":
    main()
