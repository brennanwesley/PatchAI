#!/usr/bin/env python3
"""
Cleanup Test Users Script - Auto Confirm Version
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
        for user in users:
            print(f"  - ID: {user['id']}")
            print(f"    Email: {user.get('email', 'N/A')}")
            print(f"    Created: {user.get('created_at', 'N/A')}")
            print(f"    Subscription: {user.get('subscription_status', 'N/A')}")
        
        print(f"\nProceeding to delete ALL {len(users)} user profiles and related data...")
        
        # 2. Delete related data first (foreign key constraints)
        print("\nDeleting related data...")
        
        # Delete payment transactions
        print("   Deleting payment transactions...")
        transactions_result = supabase.table("payment_transactions").delete().neq("id", "").execute()
        print(f"   Deleted {len(transactions_result.data)} payment transactions")
        
        # Delete user subscriptions
        print("   Deleting user subscriptions...")
        subscriptions_result = supabase.table("user_subscriptions").delete().neq("id", "").execute()
        print(f"   Deleted {len(subscriptions_result.data)} user subscriptions")
        
        # Delete chat histories (if table exists)
        try:
            print("   Deleting chat histories...")
            chats_result = supabase.table("chat_histories").delete().neq("id", "").execute()
            print(f"   Deleted {len(chats_result.data)} chat histories")
        except Exception as e:
            print(f"   Chat histories table not found or error: {e}")
        
        # 3. Delete user profiles
        print("   Deleting user profiles...")
        profiles_result = supabase.table("user_profiles").delete().neq("id", "").execute()
        print(f"   Deleted {len(profiles_result.data)} user profiles")
        
        print("\nCleanup completed successfully!")
        print("Summary:")
        print(f"   - User profiles: {len(profiles_result.data)} deleted")
        print(f"   - User subscriptions: {len(subscriptions_result.data)} deleted") 
        print(f"   - Payment transactions: {len(transactions_result.data)} deleted")
        
        print("\nDatabase is now clean and ready for fresh testing!")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        print("Make sure your Supabase credentials are correct and you have service role permissions.")
        return False
    
    return True

def main():
    """Main function"""
    print("PatchAI Test User Cleanup Script (Auto-Confirm)")
    print("=" * 50)
    
    try:
        cleanup_test_users()
    except KeyboardInterrupt:
        print("\nCleanup cancelled by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
