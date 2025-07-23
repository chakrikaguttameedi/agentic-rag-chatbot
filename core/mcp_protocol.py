from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from uuid import uuid4
import asyncio
from datetime import datetime
import json

class MCPMessage(BaseModel):
    """Model Context Protocol Message Structure"""
    sender: str
    receiver: str
    type: str
    trace_id: str
    timestamp: str
    payload: Dict[str, Any]

class MCPProtocol:
    """In-memory message passing system for agents"""
    
    def __init__(self):
        self.message_queue = []
        self.message_history = []
        self.current_trace_id = None
    
    def generate_trace_id(self) -> str:
        """Generate unique trace ID for message tracking"""
        return str(uuid4())[:8]
    
    def send_message(self, sender: str, receiver: str, message_type: str, payload: Dict[str, Any], trace_id: Optional[str] = None) -> str:
        """Send MCP message between agents"""
        if not trace_id:
            trace_id = self.generate_trace_id()
        
        message = MCPMessage(
            sender=sender,
            receiver=receiver,
            type=message_type,
            trace_id=trace_id,
            timestamp=datetime.now().isoformat(),
            payload=payload
        )
        
        # Store in history
        self.message_history.append(message)
        
        # Add to queue
        self.message_queue.append(message)
        
        print(f"📨 MCP Message: {sender} → {receiver} | Type: {message_type} | Trace: {trace_id}")
        
        return trace_id
    
    def receive_message(self, agent_name: str) -> Optional[MCPMessage]:
        """Receive messages for specific agent"""
        for i, message in enumerate(self.message_queue):
            if message.receiver == agent_name:
                # Remove and return the message
                return self.message_queue.pop(i)
        return None
    
    def get_message_history(self, trace_id: Optional[str] = None) -> List[MCPMessage]:
        """Get message history for debugging"""
        if trace_id:
            return [msg for msg in self.message_history if msg.trace_id == trace_id]
        return self.message_history
    
    def clear_queue(self):
        """Clear message queue"""
        self.message_queue.clear()

# Global MCP instance
mcp = MCPProtocol() 
