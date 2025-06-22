#!/usr/bin/env python3
"""
Cleanup Supabase Auth Users Script
Deletes ALL auth users and user profiles for complete cleanup
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

def cleanup_all_users():
    """Delete ALL auth users and user profiles"""
    try:
        supabase = initialize_supabase()
        
        print("Starting complete user cleanup (Auth + Profiles)...")
        
        # 1. Get all auth users
        print("\nFetching all auth users...")
        auth_response = supabase.auth.admin.list_users()
        auth_users = auth_response.users if hasattr(auth_response, 'users') else []
        
        print(f"Found {len(auth_users)} auth users:")
        for user in auth_users:
            print(f"  - ID: {user.id}")
            print(f"    Email: {user.email}")
            print(f"    Created: {user.created_at}")
        
        # 2. Get all user profiles
        print("\nFetching all user profiles...")
        profiles_response = supabase.table("user_profiles").select("*").execute()
        profiles = profiles_response.data
        
        print(f"Found {len(profiles)} user profiles:")
        for profile in profiles:
            print(f"  - ID: {profile['id']}")
            print(f"    Email: {profile.get('email', 'N/A')}")
        
        if len(auth_users) == 0 and len(profiles) == 0:
            print("\nNo users found. Database is already clean.")
            return
        
        print(f"\nProceeding to delete ALL {len(auth_users)} auth users and {len(profiles)} profiles...")
        
        # 3. Delete user profiles first
        if profiles:
            print("   Deleting user profiles...")
            for profile in profiles:
                try:
                    supabase.table("user_profiles").delete().eq("id", profile['id']).execute()
                    print(f"   Deleted profile: {profile.get('email', profile['id'])}")
                except Exception as e:
                    print(f"   Warning: Could not delete profile {profile['id']}: {e}")
        
        # 4. Delete auth users
        if auth_users:
            print("   Deleting auth users...")
            for user in auth_users:
                try:
                    supabase.auth.admin.delete_user(user.id)
                    print(f"   Deleted auth user: {user.email}")
                except Exception as e:
                    print(f"   Warning: Could not delete auth user {user.id}: {e}")
        
        print("\nComplete cleanup finished!")
        print("Summary:")
        print(f"   - Auth users: {len(auth_users)} deleted")
        print(f"   - User profiles: {len(profiles)} deleted")
        
        print("\nDatabase is now completely clean!")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        print("Make sure your Supabase credentials are correct and you have service role permissions.")
        return False
    
    return True

def main():
    """Main function"""
    print("PatchAI Complete User Cleanup Script")
    print("=" * 50)
    
    try:
        cleanup_all_users()
    except KeyboardInterrupt:
        print("\nCleanup cancelled by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
