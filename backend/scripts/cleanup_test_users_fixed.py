#!/usr/bin/env python3
"""
Cleanup Test Users Script - Fixed Version
Deletes all test user profiles and related data from the database
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Add the parent directory to the path to import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def initialize_supabase() -> Client:
    """Initialize Supabase client with service role key"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_service_role_key:
        raise ValueError("Missing Supabase configuration. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
    
    return create_client(supabase_url, supabase_service_role_key)

def cleanup_test_users():
    """Delete all test user profiles and related data"""
    try:
        supabase = initialize_supabase()
        
        print("Starting cleanup of test user profiles...")
        
        # 1. Get all user profiles
        print("\nFetching all user profiles...")
        users_response = supabase.table("user_profiles").select("*").execute()
        users = users_response.data
        
        if not users:
            print("No user profiles found. Database is already clean.")
            return
        
        print(f"Found {len(users)} user profiles:")
        user_ids = []
        for user in users:
            user_ids.append(user['id'])
            print(f"  - ID: {user['id']}")
            print(f"    Email: {user.get('email', 'N/A')}")
            print(f"    Created: {user.get('created_at', 'N/A')}")
            print(f"    Subscription: {user.get('subscription_status', 'N/A')}")
        
        print(f"\nProceeding to delete ALL {len(users)} user profiles and related data...")
        
        # 2. Delete related data first (foreign key constraints)
        print("\nDeleting related data...")
        
        # Delete payment transactions for each user
        print("   Deleting payment transactions...")
        transactions_deleted = 0
        for user_id in user_ids:
            try:
                result = supabase.table("payment_transactions").delete().eq("user_id", user_id).execute()
                transactions_deleted += len(result.data)
            except Exception as e:
                print(f"   Warning: Could not delete transactions for user {user_id}: {e}")
        print(f"   Deleted {transactions_deleted} payment transactions")
        
        # Delete user subscriptions for each user
        print("   Deleting user subscriptions...")
        subscriptions_deleted = 0
        for user_id in user_ids:
            try:
                result = supabase.table("user_subscriptions").delete().eq("user_id", user_id).execute()
                subscriptions_deleted += len(result.data)
            except Exception as e:
                print(f"   Warning: Could not delete subscriptions for user {user_id}: {e}")
        print(f"   Deleted {subscriptions_deleted} user subscriptions")
        
        # Delete chat histories for each user (if table exists)
        print("   Deleting chat histories...")
        chats_deleted = 0
        for user_id in user_ids:
            try:
                result = supabase.table("chat_histories").delete().eq("user_id", user_id).execute()
                chats_deleted += len(result.data)
            except Exception as e:
                print(f"   Chat histories: {e}")
                break
        if chats_deleted > 0:
            print(f"   Deleted {chats_deleted} chat histories")
        else:
            print("   No chat histories found or table doesn't exist")
        
        # 3. Delete user profiles
        print("   Deleting user profiles...")
        profiles_deleted = 0
        for user_id in user_ids:
            try:
                result = supabase.table("user_profiles").delete().eq("id", user_id).execute()
                profiles_deleted += len(result.data)
            except Exception as e:
                print(f"   Warning: Could not delete profile for user {user_id}: {e}")
        print(f"   Deleted {profiles_deleted} user profiles")
        
        print("\nCleanup completed successfully!")
        print("Summary:")
        print(f"   - User profiles: {profiles_deleted} deleted")
        print(f"   - User subscriptions: {subscriptions_deleted} deleted") 
        print(f"   - Payment transactions: {transactions_deleted} deleted")
        print(f"   - Chat histories: {chats_deleted} deleted")
        
        print("\nDatabase is now clean and ready for fresh testing!")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        print("Make sure your Supabase credentials are correct and you have service role permissions.")
        return False
    
    return True

def main():
    """Main function"""
    print("PatchAI Test User Cleanup Script (Fixed)")
    print("=" * 50)
    
    try:
        cleanup_test_users()
    except KeyboardInterrupt:
        print("\nCleanup cancelled by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
