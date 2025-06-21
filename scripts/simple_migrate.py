#!/usr/bin/env python3
"""
Simple Database Migration Script for PatchAI
Uses direct HTTP requests to avoid Python version compatibility issues
"""

import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('REACT_APP_SUPABASE_URL') or os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def check_environment():
    """Check if required environment variables are set"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("ERROR: Missing required environment variables:")
        print("   REACT_APP_SUPABASE_URL (or SUPABASE_URL)")
        print("   SUPABASE_SERVICE_ROLE_KEY")
        print("\nPlease set these in your .env file")
        return False
    
    print("SUCCESS: Environment variables found")
    print(f"   Supabase URL: {SUPABASE_URL}")
    print(f"   Service Key: {SUPABASE_SERVICE_ROLE_KEY[:20]}...")
    return True

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

def execute_sql_via_api(sql_statement):
    """Execute SQL statement via Supabase REST API"""
    # Clean the URL to get the base URL
    base_url = SUPABASE_URL.rstrip('/')
    
    # Use the PostgREST API to execute SQL
    url = f"{base_url}/rest/v1/rpc/exec_sql"
    
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    payload = {
        'sql': sql_statement
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            return True, None
        elif response.status_code == 404:
            # Try alternative method - direct SQL execution
            return execute_sql_direct(sql_statement)
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {str(e)}"

def execute_sql_direct(sql_statement):
    """Execute SQL statement via direct database connection simulation"""
    # For statements that might not work via API, we'll try a different approach
    base_url = SUPABASE_URL.rstrip('/')
    
    # Try using the database URL directly
    url = f"{base_url}/database/sql"
    
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/sql'
    }
    
    try:
        response = requests.post(url, headers=headers, data=sql_statement, timeout=30)
        
        if response.status_code in [200, 201, 204]:
            return True, None
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {str(e)}"

def execute_migration(sql_content):
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
        print(f"Executing statement {i}/{len(statements)}...")
        
        success, error = execute_sql_via_api(statement)
        
        if success:
            print(f"SUCCESS: Statement {i} executed successfully")
            success_count += 1
        else:
            print(f"ERROR: Statement {i} failed: {error}")
            
            # Check if it's a "already exists" error
            if error and 'already exists' in error.lower():
                print(f"   WARNING: Skipping - object already exists")
                success_count += 1
            elif error and 'permission denied' in error.lower():
                print(f"   ERROR: Permission denied - check service role key")
                error_count += 1
                break
            else:
                error_count += 1
                
                # Show the problematic statement for debugging
                preview = statement[:100].replace('\n', ' ')
                print(f"   Statement: {preview}...")
    
    print(f"\nMigration Summary:")
    print(f"   SUCCESS: {success_count}")
    print(f"   ERRORS: {error_count}")
    print(f"   TOTAL: {len(statements)}")
    
    return error_count == 0

def verify_migration():
    """Verify that the migration was successful"""
    print("\nVerifying migration...\n")
    
    base_url = SUPABASE_URL.rstrip('/')
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json'
    }
    
    tables = ['user_profiles', 'chat_sessions', 'messages']
    
    for table_name in tables:
        try:
            url = f"{base_url}/rest/v1/{table_name}?select=*&limit=1"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"SUCCESS: Table '{table_name}' exists and is accessible")
            else:
                print(f"WARNING: Table '{table_name}' verification failed: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Table '{table_name}' verification failed: {e}")
    
    print("\nMigration verification complete!")

def main():
    """Main migration function"""
    print("PatchAI Simple Database Migration Tool\n")
    
    try:
        # Check environment
        if not check_environment():
            sys.exit(1)
        
        print("\nConnecting to Supabase...")
        
        # Test connection
        base_url = SUPABASE_URL.rstrip('/')
        test_url = f"{base_url}/rest/v1/"
        headers = {
            'apikey': SUPABASE_SERVICE_ROLE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}'
        }
        
        response = requests.get(test_url, headers=headers, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Cannot connect to Supabase: HTTP {response.status_code}")
        
        print("SUCCESS: Connected to Supabase")
        
        # Read migration file
        print("\nReading migration file...")
        sql_content = read_migration_file()
        
        # Execute migration
        success = execute_migration(sql_content)
        
        if success:
            print("\nSUCCESS: Database migration completed successfully!")
            
            # Verify migration
            verify_migration()
            
            print("\nNext Steps:")
            print("1. Your database schema is now ready")
            print("2. Update your backend API endpoints")
            print("3. Update your frontend to use the new schema")
            print("4. Test the complete user flow")
            
        else:
            print("\nWARNING: Migration completed with errors.")
            print("Please check the errors above and verify your database state.")
            print("\nYou may need to:")
            print("1. Check your Supabase service role key permissions")
            print("2. Manually run some statements in Supabase SQL Editor")
            print("3. Contact Supabase support if issues persist")
            
    except Exception as error:
        print(f"\nERROR: Migration failed: {error}")
        print("\nPlease check:")
        print("1. Your Supabase URL and service role key are correct")
        print("2. You have sufficient permissions")
        print("3. Your Supabase project is accessible")
        print("4. Your internet connection is stable")
        sys.exit(1)

if __name__ == "__main__":
    main()
