#!/usr/bin/env python3
"""
Emergency script to fix sync issue for brennan.testuser2@email.com
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

async def fix_testuser2_sync():
    """Fix the sync issue for brennan.testuser2@email.com"""
    email = "brennan.testuser2@email.com"
    
    print(f"[FIX] Emergency sync for {email}")
    print("=" * 50)
    
    try:
        success = await webhook_handler.sync_subscription_from_stripe(email)
        print(f"[RESULT] Sync result: {success}")
        
        if success:
            print("[SUCCESS] Sync completed successfully!")
        else:
            print("[FAILED] Sync failed - check logs")
            
    except Exception as e:
        print(f"[ERROR] Sync error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False
    
    return success

if __name__ == "__main__":
    result = asyncio.run(fix_testuser2_sync())
    print(f"\nFinal result: {result}")
