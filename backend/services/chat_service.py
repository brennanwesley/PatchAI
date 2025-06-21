"""
Chat session management service
"""

import uuid
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from models.schemas import Message, ChatSession

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat sessions and conversation context"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def generate_chat_title(self, messages: List[Message]) -> str:
        """Generate a title for the chat based on the first user message"""
        for message in messages:
            if message.role == 'user':
                # Take first 50 characters of user's first message
                title = message.content[:50].strip()
                if len(message.content) > 50:
                    title += "..."
                return title
        return "New Chat"
    
    async def create_chat_session(self, user_id: str, messages: List[Message], title: Optional[str] = None) -> str:
        """Create a new chat session and return the chat_id"""
        try:
            chat_id = str(uuid.uuid4())
            
            if not title:
                title = self.generate_chat_title(messages)
            
            # Insert chat session metadata
            session_result = self.supabase.table("chat_sessions").insert({
                "id": chat_id,
                "user_id": user_id,
                "title": title,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            
            # Insert messages into separate messages table
            for message in messages:
                self.supabase.table("messages").insert({
                    "chat_session_id": chat_id,
                    "user_id": user_id,
                    "role": message.role,
                    "content": message.content,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
            
            logger.info(f"Created new chat session {chat_id} for user {user_id} with {len(messages)} messages")
            return chat_id
            
        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            raise
    
    async def update_chat_session(self, chat_id: str, user_id: str, messages: List[Message]) -> bool:
        """Update an existing chat session with new messages"""
        try:
            # Delete existing messages
            self.supabase.table("messages").delete().eq("chat_session_id", chat_id).execute()
            
            # Insert new messages into separate messages table
            for message in messages:
                self.supabase.table("messages").insert({
                    "chat_session_id": chat_id,
                    "user_id": user_id,
                    "role": message.role,
                    "content": message.content,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
            
            # Update chat session metadata
            session_result = self.supabase.table("chat_sessions").update({
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", chat_id).eq("user_id", user_id).execute()
            
            if not session_result.data:
                logger.warning(f"No chat session found with id {chat_id} for user {user_id}")
                return False
            
            logger.info(f"Updated chat session {chat_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update chat session {chat_id}: {e}")
            raise
    
    async def get_chat_session(self, chat_id: str, user_id: str) -> Optional[ChatSession]:
        """Get a specific chat session"""
        try:
            session_result = self.supabase.table("chat_sessions").select("*").eq("id", chat_id).eq("user_id", user_id).execute()
            
            if not session_result.data:
                return None
            
            session_data = session_result.data[0]
            
            # Get messages from separate messages table
            messages_result = self.supabase.table("messages").select("*").eq("chat_session_id", chat_id).execute()
            messages = [Message(role=msg["role"], content=msg["content"]) for msg in messages_result.data]
            
            return ChatSession(
                id=session_data["id"],
                user_id=session_data["user_id"],
                title=session_data["title"],
                messages=messages,
                created_at=datetime.fromisoformat(session_data["created_at"]),
                updated_at=datetime.fromisoformat(session_data["updated_at"])
            )
            
        except Exception as e:
            logger.error(f"Failed to get chat session {chat_id}: {e}")
            return None
    
    async def get_user_chat_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all chat sessions for a user (without full message content for performance)"""
        try:
            result = self.supabase.table("chat_sessions").select(
                "id, title, created_at, updated_at"
            ).eq("user_id", user_id).order("updated_at", desc=True).limit(limit).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get chat sessions for user {user_id}: {e}")
            return []
    
    async def delete_chat_session(self, chat_id: str, user_id: str) -> bool:
        """Delete a chat session"""
        try:
            # Delete messages from separate messages table
            self.supabase.table("messages").delete().eq("chat_session_id", chat_id).execute()
            
            # Delete chat session metadata
            session_result = self.supabase.table("chat_sessions").delete().eq("id", chat_id).eq("user_id", user_id).execute()
            
            if not session_result.data:
                logger.warning(f"No chat session found with id {chat_id} for user {user_id}")
                return False
            
            logger.info(f"Deleted chat session {chat_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete chat session {chat_id}: {e}")
            return False
