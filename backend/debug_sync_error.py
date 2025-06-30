#!/usr/bin/env python3
"""
Debug script to identify the sync endpoint error locally
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from services.supabase_service import supabase
    print("[SUCCESS] Successfully imported supabase")
except Exception as e:
    print(f"[ERROR] Failed to import supabase: {e}")
    sys.exit(1)

def test_user_profile_query():
    """Test the exact query that's failing in the sync endpoint"""
    print("\n[DEBUG] Testing user profile query...")
    
    # Test with a known user ID (you can replace this with a real one)
    test_user_id = "test-user-id"  # Replace with actual user ID
    
    try:
        print(f"[INFO] Querying user profile for ID: {test_user_id}")
        
        # This is the exact query from the sync endpoint
        user_profile_response = supabase.table("user_profiles").select(
            "email"
        ).eq("id", test_user_id).single().execute()
        
        print(f"[SUCCESS] Query successful!")
        print(f"[INFO] Response type: {type(user_profile_response)}")
        print(f"[INFO] Response attributes: {dir(user_profile_response)}")
        
        if hasattr(user_profile_response, 'data'):
            print(f"[INFO] Response.data: {user_profile_response.data}")
            print(f"[INFO] Response.data type: {type(user_profile_response.data)}")
        else:
            print("[ERROR] Response has no 'data' attribute!")
            
    except Exception as e:
        print(f"[ERROR] Query failed: {e}")
        print(f"[ERROR] Error type: {type(e)}")
        import traceback
        traceback.print_exc()

def test_general_query():
    """Test a simple query to see the response structure"""
    print("\n[DEBUG] Testing general query structure...")
    
    try:
        # Simple query to understand response structure
        response = supabase.table("user_profiles").select("email").limit(1).execute()
        
        print(f"[SUCCESS] General query successful!")
        print(f"[INFO] Response type: {type(response)}")
        print(f"[INFO] Response attributes: {dir(response)}")
        
        if hasattr(response, 'data'):
            print(f"[INFO] Response.data: {response.data}")
            print(f"[INFO] Response.data type: {type(response.data)}")
        else:
            print("[ERROR] Response has no 'data' attribute!")
            
    except Exception as e:
        print(f"[ERROR] General query failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("[START] Starting sync endpoint debug session...")
    
    # Test basic connection
    print(f"[INFO] Supabase client: {supabase}")
    print(f"[INFO] Supabase type: {type(supabase)}")
    
    # Run tests
    test_general_query()
    test_user_profile_query()
    
    print("\n[COMPLETE] Debug session complete!")
