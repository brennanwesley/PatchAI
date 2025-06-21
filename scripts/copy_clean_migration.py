#!/usr/bin/env python3
"""
Copy Clean Migration to Clipboard
"""

import pyperclip
from pathlib import Path

def main():
    """Copy clean migration SQL to clipboard"""
    migration_path = Path(__file__).parent / 'clean_migration.sql'
    
    with open(migration_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    pyperclip.copy(sql_content)
    
    print("SUCCESS: Clean migration SQL copied to clipboard!")
    print(f"Size: {len(sql_content)} characters")
    print("\nNEXT STEPS:")
    print("1. Go to Supabase dashboard > SQL Editor")
    print("2. Create a new query")
    print("3. Press Ctrl+V to paste the migration")
    print("4. Click 'Run' to execute")
    print("\nThis clean migration should work without any snippet errors!")

if __name__ == "__main__":
    main()
