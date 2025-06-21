#!/usr/bin/env python3
"""
Automated Database Migration Script for PatchAI
This script applies the clean database schema migration automatically
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('REACT_APP_SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def check_environment():
    """Check if required environment variables are set"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("ERROR: Missing required environment variables:")
        print("   REACT_APP_SUPABASE_URL")
        print("   SUPABASE_SERVICE_ROLE_KEY")
        print("\nPlease set these in your .env file")
        sys.exit(1)
    
    print("SUCCESS: Environment variables found")
    print(f"   Supabase URL: {SUPABASE_URL}")
    print(f"   Service Key: {SUPABASE_SERVICE_ROLE_KEY[:20]}...")

def read_migration_file():
    """Read the migration SQL file"""
    migration_path = Path(__file__).parent.parent / 'supabase' / 'migrations' / '20240620193000_rebuild_clean_schema.sql'
    
    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")
    
    with open(migration_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Reading migration file: {migration_path}")
    print(f"   Size: {len(content)} characters")
    
    return content

def execute_migration(supabase: Client, sql_content: str):
    """Execute the migration SQL"""
    print("\nStarting database migration...\n")
    
    # Split SQL into individual statements
    statements = []
    current_statement = ""
    
    for line in sql_content.split('\n'):
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('--'):
            continue
            
        current_statement += line + '\n'
        
        # Check if statement is complete (ends with semicolon)
        if line.endswith(';'):
            statements.append(current_statement.strip())
            current_statement = ""
    
    print(f"Found {len(statements)} SQL statements to execute\n")
    
    success_count = 0
    error_count = 0
    
    for i, statement in enumerate(statements, 1):
        try:
            print(f"Executing statement {i}/{len(statements)}...")
            
            # Execute the SQL statement
            result = supabase.rpc('exec_sql', {'sql': statement}).execute()
            
            if result.data is not None:
                print(f"SUCCESS: Statement {i} executed successfully")
                success_count += 1
            else:
                print(f"WARNING: Statement {i} completed with warnings")
                success_count += 1
                
        except Exception as error:
            error_msg = str(error)
            print(f"ERROR: Error in statement {i}: {error_msg}")
            
            # Log the problematic statement for debugging
            preview = statement[:100].replace('\n', ' ')
            print(f"   Statement: {preview}...")
            
            # Handle specific error types
            if 'already exists' in error_msg.lower():
                print(f"   WARNING: Skipping - object already exists")
                success_count += 1
            elif 'permission denied' in error_msg.lower():
                print(f"   ERROR: Permission denied - check service role key")
                error_count += 1
                break
            else:
                error_count += 1
    
    print(f"\nMigration Summary:")
    print(f"   SUCCESS: {success_count}")
    print(f"   ERRORS: {error_count}")
    print(f"   TOTAL: {len(statements)}")
    
    return error_count == 0

def verify_migration(supabase: Client):
    """Verify that the migration was successful"""
    print("\nVerifying migration...\n")
    
    tables = ['user_profiles', 'chat_sessions', 'messages']
    
    for table_name in tables:
        try:
            # Try to query the table
            result = supabase.table(table_name).select('*').limit(1).execute()
            print(f"SUCCESS: Table '{table_name}' exists and is accessible")
            
        except Exception as error:
            print(f"ERROR: Table '{table_name}' verification failed: {error}")
    
    print("\nMigration verification complete!")

def main():
    """Main migration function"""
    print("PatchAI Database Migration Tool\n")
    
    try:
        # Check environment
        check_environment()
        
        # Create Supabase client
        print("\nConnecting to Supabase...")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        print("SUCCESS: Connected to Supabase")
        
        # Read migration file
        print("\nReading migration file...")
        sql_content = read_migration_file()
        
        # Execute migration
        success = execute_migration(supabase, sql_content)
        
        if success:
            print("\nSUCCESS: Database migration completed successfully!")
            
            # Verify migration
            verify_migration(supabase)
            
            print("\nNext Steps:")
            print("1. Update your backend API endpoints")
            print("2. Update your frontend to use the new schema")
            print("3. Test the complete user flow")
            
        else:
            print("\nWARNING: Migration completed with errors.")
            print("Please check the errors above and verify your database state.")
            
    except Exception as error:
        print(f"\nERROR: Migration failed: {error}")
        print("\nPlease check:")
        print("1. Your Supabase URL and service role key are correct")
        print("2. You have sufficient permissions")
        print("3. Your Supabase project is accessible")
        sys.exit(1)

if __name__ == "__main__":
    main()
