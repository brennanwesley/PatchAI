#!/usr/bin/env python3
"""
Script to delete all chat history for a specific user
Usage: python delete_user_history.py
"""

import os
import sys
from supabase import create_client, Client

def delete_user_chat_history(user_email: str):
    """Delete all chat history for a specific user"""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables must be set")
        return False
    
    try:
        supabase: Client = create_client(supabase_url, supabase_service_key)
        print(f"✅ Connected to Supabase")
        
        # Get all chat sessions for the user
        print(f"🔍 Finding chat sessions for user: {user_email}")
        chat_sessions_result = supabase.table("chat_sessions").select("id, title").eq("user_id", user_email).execute()
        
        if not chat_sessions_result.data:
            print(f"ℹ️  No chat sessions found for user: {user_email}")
            return True
        
        chat_sessions = chat_sessions_result.data
        print(f"📋 Found {len(chat_sessions)} chat sessions to delete:")
        
        for session in chat_sessions:
            print(f"   - {session['id']}: {session['title']}")
        
        # Confirm deletion
        print(f"\n⚠️  This will permanently delete ALL chat history for {user_email}")
        confirm = input("Are you sure you want to proceed? (yes/no): ").lower().strip()
        
        if confirm != 'yes':
            print("❌ Deletion cancelled")
            return False
        
        # Delete messages for each chat session
        deleted_messages_count = 0
        for session in chat_sessions:
            chat_id = session['id']
            print(f"🗑️  Deleting messages for chat: {session['title']}")
            
            # Delete messages
            messages_result = supabase.table("messages").delete().eq("chat_session_id", chat_id).execute()
            if messages_result.data:
                deleted_messages_count += len(messages_result.data)
                print(f"   ✅ Deleted {len(messages_result.data)} messages")
            else:
                print(f"   ℹ️  No messages found for this chat")
        
        # Delete chat sessions
        print(f"🗑️  Deleting chat sessions...")
        sessions_result = supabase.table("chat_sessions").delete().eq("user_id", user_email).execute()
        
        if sessions_result.data:
            deleted_sessions_count = len(sessions_result.data)
            print(f"✅ Deleted {deleted_sessions_count} chat sessions")
        else:
            print(f"⚠️  No chat sessions were deleted")
        
        print(f"\n🎉 DELETION COMPLETE!")
        print(f"   - Chat sessions deleted: {len(chat_sessions)}")
        print(f"   - Messages deleted: {deleted_messages_count}")
        print(f"   - User {user_email} now has a clean slate")
        
        return True
        
    except Exception as e:
        print(f"❌ Error deleting chat history: {e}")
        return False

if __name__ == "__main__":
    # Target user email
    target_user = "tharaldson.brennan@gmail.com"
    
    print("🗑️  PatchAI Chat History Deletion Tool")
    print("=" * 50)
    
    success = delete_user_chat_history(target_user)
    
    if success:
        print(f"\n✅ Successfully cleaned chat history for {target_user}")
        print("🚀 Ready for fresh testing!")
    else:
        print(f"\n❌ Failed to clean chat history for {target_user}")
        sys.exit(1)
