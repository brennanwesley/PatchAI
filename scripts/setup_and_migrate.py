#!/usr/bin/env python3
"""
Setup and Migration Script for PatchAI
This script will help you set up environment variables and run the database migration
"""

import os
import sys
from pathlib import Path

def get_user_input():
    """Get Supabase credentials from user"""
    print("PatchAI Database Migration Setup")
    print("=" * 50)
    print()
    print("I need your Supabase credentials to run the migration.")
    print("You can find these in your Supabase Dashboard:")
    print("1. Go to https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Go to Settings > API")
    print()
    
    # Get Supabase URL
    supabase_url = input("Enter your Supabase URL (https://xxx.supabase.co): ").strip()
    if not supabase_url:
        print("ERROR: Supabase URL is required!")
        sys.exit(1)
    
    # Get Service Role Key
    print("\nIMPORTANT: Enter your SERVICE ROLE key (not the anon key)")
    print("   This is the secret key that starts with 'eyJ...'")
    service_key = input("Enter your Supabase Service Role Key: ").strip()
    if not service_key:
        print("ERROR: Service Role Key is required!")
        sys.exit(1)
    
    return supabase_url, service_key

def create_env_file(supabase_url, service_key):
    """Create .env file with credentials"""
    env_path = Path(__file__).parent.parent / '.env'
    
    env_content = f"""# PatchAI Environment Variables
# Frontend Supabase Configuration
REACT_APP_SUPABASE_URL={supabase_url}
REACT_APP_SUPABASE_ANON_KEY=your-anon-key-here

# Backend Supabase Configuration (for migration)
SUPABASE_URL={supabase_url}
SUPABASE_SERVICE_ROLE_KEY={service_key}

# OpenAI Configuration
OPENAI_API_KEY=your-openai-key-here
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"SUCCESS: Created .env file at: {env_path}")
    return env_path

def run_migration():
    """Run the database migration"""
    print("\nRunning database migration...")
    
    # Import and run the migration
    try:
        # Add the scripts directory to Python path
        scripts_dir = Path(__file__).parent
        sys.path.insert(0, str(scripts_dir))
        
        # Import the migration module
        from migrate_database import main as migrate_main
        
        # Run the migration
        migrate_main()
        
    except Exception as error:
        print(f"ERROR: Migration failed: {error}")
        print("\nYou can try running the migration manually:")
        print("python scripts/migrate_database.py")
        sys.exit(1)

def main():
    """Main setup function"""
    try:
        # Get credentials from user
        supabase_url, service_key = get_user_input()
        
        # Create .env file
        env_path = create_env_file(supabase_url, service_key)
        
        # Confirm before running migration
        print("\n" + "=" * 50)
        print("Ready to run database migration!")
        print("This will:")
        print("1. Drop existing tables (if any)")
        print("2. Create new clean schema")
        print("3. Set up Row Level Security")
        print("4. Create indexes and triggers")
        print()
        
        confirm = input("Continue with migration? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Migration cancelled.")
            print(f"Your .env file has been created at: {env_path}")
            print("You can run the migration later with: python scripts/migrate_database.py")
            return
        
        # Run the migration
        run_migration()
        
        print("\nSetup and migration complete!")
        print("\nNext steps:")
        print("1. Your database schema is now ready")
        print("2. Update your frontend/backend if needed")
        print("3. Test the complete user flow")
        
    except KeyboardInterrupt:
        print("\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as error:
        print(f"\nSetup failed: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
