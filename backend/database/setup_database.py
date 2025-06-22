#!/usr/bin/env python3
"""
Database setup script for PatchAI
Creates necessary tables and indexes in Supabase
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from services.supabase_service import initialize_supabase_client


def test_database():
    """Test database connection and table accessibility"""
    try:
        print("🔄 Testing database connection...")
        supabase = initialize_supabase_client()
        
        if not supabase:
            print("❌ Failed to initialize Supabase client")
            return False
        
        print("✅ Supabase client initialized successfully")
        
        # Test chat_sessions table
        print("🔄 Testing chat_sessions table...")
        try:
            result = supabase.table("chat_sessions").select("*").limit(1).execute()
            print(f"✅ chat_sessions table accessible: {len(result.data)} rows found")
        except Exception as e:
            print(f"❌ chat_sessions table error: {e}")
            return False
        
        # Test messages table
        print("🔄 Testing messages table...")
        try:
            result = supabase.table("messages").select("*").limit(1).execute()
            print(f"✅ messages table accessible: {len(result.data)} rows found")
        except Exception as e:
            print(f"❌ messages table error: {e}")
            return False
        
        print("✅ Database test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def create_test_chat():
    """Create a test chat session to verify database functionality"""
    try:
        print("🔄 Creating test chat session...")
        supabase = initialize_supabase_client()
        
        # Create test chat session
        test_chat = {
            "id": "test-chat-123",
            "user_id": "test-user",
            "title": "Test Chat",
            "created_at": "2025-06-21T22:50:00Z",
            "updated_at": "2025-06-21T22:50:00Z"
        }
        
        result = supabase.table("chat_sessions").insert(test_chat).execute()
        print(f"✅ Test chat session created: {result.data}")
        
        # Create test message
        test_message = {
            "chat_session_id": "test-chat-123",
            "role": "user",
            "content": "Hello, this is a test message",
            "created_at": "2025-06-21T22:50:00Z"
        }
        
        result = supabase.table("messages").insert(test_message).execute()
        print(f"✅ Test message created: {result.data}")
        
        # Clean up test data
        print("🔄 Cleaning up test data...")
        supabase.table("messages").delete().eq("chat_session_id", "test-chat-123").execute()
        supabase.table("chat_sessions").delete().eq("id", "test-chat-123").execute()
        print("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Test chat creation failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 PatchAI Database Test")
    print("=" * 50)
    
    # Test database connectivity
    if test_database():
        print("\n" + "=" * 50)
        print("🧪 Testing Chat Creation")
        if create_test_chat():
            print("\n✅ All database tests passed!")
        else:
            print("\n❌ Chat creation test failed")
    else:
        print("❌ Database connectivity test failed")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Database testing complete!")
