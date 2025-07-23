from typing import List, Dict, Any
import os
from core.mcp_protocol import mcp
from core.document_parser import DocumentParser

class IngestionAgent:
    """Agent responsible for parsing and preprocessing documents"""
    
    def __init__(self):
        self.name = "IngestionAgent"
        self.parser = DocumentParser()
        self.processed_documents = []
    
    def process_documents(self, file_paths: List[str], trace_id: str) -> List[Dict[str, Any]]:
        """Process multiple documents and return parsed content"""
        print(f"🔄 {self.name}: Starting document processing...")
        
        processed_docs = []
        
        for file_path in file_paths:
            try:
                print(f"📄 Processing: {os.path.basename(file_path)}")
                
                # Parse document
                parsed_doc = self.parser.parse_document(file_path)
                processed_docs.append(parsed_doc)
                
                print(f"✅ Processed {parsed_doc['filename']}: {len(parsed_doc['chunks'])} chunks")
                
            except Exception as e:
                print(f"❌ Error processing {file_path}: {str(e)}")
                # Add error document
                processed_docs.append({
                    'filename': os.path.basename(file_path),
                    'content': f"Error: {str(e)}",
                    'chunks': [],
                    'metadata': {'error': str(e)}
                })
        
        # Store processed documents
        self.processed_documents.extend(processed_docs)
        
        # Send MCP message to RetrievalAgent
        mcp.send_message(
            sender=self.name,
            receiver="RetrievalAgent",
            message_type="INGESTION_COMPLETE",
            trace_id=trace_id,
            payload={
                "processed_documents": processed_docs,
                "total_documents": len(processed_docs),
                "total_chunks": sum(len(doc['chunks']) for doc in processed_docs)
            }
        )
        
        print(f"✅ {self.name}: Processing complete. Sent to RetrievalAgent")
        return processed_docs
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return list(self.parser.supported_formats)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about processed documents"""
        total_chunks = sum(len(doc['chunks']) for doc in self.processed_documents)
        formats = {}
        
        for doc in self.processed_documents:
            fmt = doc['metadata'].get('format', 'unknown')
            formats[fmt] = formats.get(fmt, 0) + 1
        
        return {
            'total_documents': len(self.processed_documents),
            'total_chunks': total_chunks,
            'formats_processed': formats
        } 
