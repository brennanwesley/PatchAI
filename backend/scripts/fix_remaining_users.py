#!/usr/bin/env python3
"""
Fix remaining users with subscription sync issues
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.stripe_webhooks import webhook_handler

# Load environment variables
load_dotenv()

async def fix_user_subscription(email):
    """Fix subscription status for a specific user"""
    print(f"[SYNC] Attempting to fix subscription for: {email}")
    
    try:
        success = await webhook_handler.sync_subscription_from_stripe(email)
        
        if success:
            print(f"[SUCCESS] Successfully synced subscription for {email}")
            return True
        else:
            print(f"[FAILED] No active subscription found in Stripe for {email}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error syncing {email}: {str(e)}")
        return False

async def main():
    """Fix subscription sync for remaining problematic users"""
    print("FIXING REMAINING SUBSCRIPTION ISSUES")
    print("=" * 50)
    
    # Remaining users with issues
    remaining_users = [
        "dchr393@gmail.com",
        "slowe@highpeakenergy.com", 
        "testuser3@email.com"
    ]
    
    results = {}
    
    for email in remaining_users:
        print(f"\n[PROCESSING] {email}")
        success = await fix_user_subscription(email)
        results[email] = success
    
    print("\n" + "=" * 50)
    print("SYNC RESULTS SUMMARY:")
    print("=" * 50)
    
    for email, success in results.items():
        status = "[FIXED]" if success else "[FAILED]"
        print(f"{email}: {status}")
    
    # Count successful fixes
    successful_fixes = sum(1 for success in results.values() if success)
    total_users = len(remaining_users)
    
    print(f"\n[SUMMARY] {successful_fixes}/{total_users} users successfully synced")
    
    if successful_fixes == total_users:
        print("[SUCCESS] ALL REMAINING USERS FIXED!")
    else:
        print("[WARNING] Some users still need manual intervention.")

if __name__ == "__main__":
    asyncio.run(main())
