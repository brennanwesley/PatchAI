#!/usr/bin/env python3
"""
Verify Cleanup Script
Checks if all test user profiles have been deleted
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

def verify_cleanup():
    """Verify all test data has been deleted"""
    try:
        supabase = initialize_supabase()
        
        print("Verifying database cleanup...")
        
        # Check user profiles
        users_response = supabase.table("user_profiles").select("*").execute()
        users = users_response.data
        print(f"User profiles remaining: {len(users)}")
        
        # Check user subscriptions
        try:
            subs_response = supabase.table("user_subscriptions").select("*").execute()
            subs = subs_response.data
            print(f"User subscriptions remaining: {len(subs)}")
        except Exception as e:
            print(f"User subscriptions table: {e}")
        
        # Check payment transactions
        try:
            trans_response = supabase.table("payment_transactions").select("*").execute()
            trans = trans_response.data
            print(f"Payment transactions remaining: {len(trans)}")
        except Exception as e:
            print(f"Payment transactions table: {e}")
        
        if len(users) == 0:
            print("\nDatabase cleanup verified successfully!")
            print("All test user profiles have been deleted.")
        else:
            print(f"\nWarning: {len(users)} user profiles still exist:")
            for user in users:
                print(f"  - {user.get('email', 'N/A')} ({user['id']})")
        
    except Exception as e:
        print(f"Error during verification: {e}")

def main():
    """Main function"""
    print("PatchAI Database Cleanup Verification")
    print("=" * 40)
    
    try:
        verify_cleanup()
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
