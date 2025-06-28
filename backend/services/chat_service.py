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
    """Service for managing SINGLE chat session per user - simplified architecture"""
    
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
    
    async def get_or_create_single_chat(self, user_id: str) -> str:
        """Get user's single chat session or create it if it doesn't exist"""
        try:
            # Check if user already has a chat session
            existing_result = self.supabase.table("chat_sessions").select("id").eq("user_id", user_id).execute()
            
            if existing_result.data:
                chat_id = existing_result.data[0]["id"]
                logger.info(f"Found existing chat session {chat_id} for user {user_id}")
                return chat_id
            
            # Create new single chat session
            chat_id = str(uuid.uuid4())
            
            session_result = self.supabase.table("chat_sessions").insert({
                "id": chat_id,
                "user_id": user_id,
                "title": "Chat with Patch",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            
            logger.info(f"Created new single chat session {chat_id} for user {user_id}")
            return chat_id
            
        except Exception as e:
            logger.error(f"Failed to get or create single chat for user {user_id}: {e}")
            raise
    
    async def add_message_to_single_chat(self, user_id: str, message: Message) -> str:
        """Add a single message to user's single chat session"""
        try:
            # Get or create user's single chat session
            chat_id = await self.get_or_create_single_chat(user_id)
            
            # Insert the message
            self.supabase.table("messages").insert({
                "chat_session_id": chat_id,
                "role": message.role,
                "content": message.content,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            # Update chat session timestamp
            self.supabase.table("chat_sessions").update({
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", chat_id).eq("user_id", user_id).execute()
            
            logger.info(f"Added {message.role} message to single chat {chat_id} for user {user_id}")
            return chat_id
            
        except Exception as e:
            logger.error(f"Failed to add message to single chat for user {user_id}: {e}")
            raise
    

    
    async def get_single_chat_session(self, user_id: str) -> Optional[ChatSession]:
        """Get user's single chat session with all messages"""
        try:
            # Get or create user's single chat session
            chat_id = await self.get_or_create_single_chat(user_id)
            
            # Get session metadata
            session_result = self.supabase.table("chat_sessions").select("*").eq("id", chat_id).eq("user_id", user_id).execute()
            
            if not session_result.data:
                logger.error(f"Single chat session {chat_id} not found for user {user_id}")
                return None
            
            session_data = session_result.data[0]
            
            # Get all non-deleted messages from separate messages table
            messages_result = self.supabase.table("messages").select("*").eq("chat_session_id", chat_id).is_("deleted_at", "null").order("created_at").execute()
            messages = [Message(role=msg["role"], content=msg["content"]) for msg in messages_result.data]
            
            logger.info(f"Retrieved single chat session {chat_id} with {len(messages)} messages for user {user_id}")
            
            return ChatSession(
                id=session_data["id"],
                user_id=session_data["user_id"],
                title=session_data["title"],
                messages=messages,
                created_at=datetime.fromisoformat(session_data["created_at"]),
                updated_at=datetime.fromisoformat(session_data["updated_at"])
            )
            
        except Exception as e:
            logger.error(f"Failed to get single chat session for user {user_id}: {e}")
            return None
    
    async def get_single_chat_messages(self, user_id: str) -> List[Message]:
        """Get all non-deleted messages from user's single chat session"""
        try:
            # Get or create user's single chat session
            chat_id = await self.get_or_create_single_chat(user_id)
            
            # Get all non-deleted messages (exclude soft deleted)
            messages_result = self.supabase.table("messages").select("*").eq("chat_session_id", chat_id).is_("deleted_at", "null").order("created_at").execute()
            messages = [Message(role=msg["role"], content=msg["content"]) for msg in messages_result.data]
            
            logger.info(f"Retrieved {len(messages)} non-deleted messages from single chat for user {user_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages for user {user_id}: {e}")
            return []
    
    async def clear_single_chat_messages(self, user_id: str) -> bool:
        """HARD DELETE all messages from user's single chat session (remove from database completely)"""
        try:
            # Get user's single chat session
            chat_id = await self.get_or_create_single_chat(user_id)
            
            # HARD DELETE all messages from the chat (remove from database completely)
            self.supabase.table("messages").delete().eq("chat_session_id", chat_id).execute()
            
            # Update chat session timestamp
            self.supabase.table("chat_sessions").update({
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", chat_id).eq("user_id", user_id).execute()
            
            logger.info(f"HARD DELETED all messages from single chat {chat_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to hard delete messages for user {user_id}: {e}")
            return False
