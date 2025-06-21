#!/usr/bin/env python3
"""
Migration Copy Helper for PatchAI
This script prepares the migration SQL for easy copy-paste into Supabase dashboard
"""

import os
from pathlib import Path

def read_migration_file():
    """Read the migration SQL file"""
    migration_path = Path(__file__).parent.parent / 'supabase' / 'migrations' / '20240620193000_rebuild_clean_schema.sql'
    
    if not migration_path.exists():
        print(f"ERROR: Migration file not found: {migration_path}")
        return None
    
    with open(migration_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content, migration_path

def create_dashboard_instructions():
    """Create step-by-step instructions for running migration in Supabase dashboard"""
    instructions = """
=================================================================
PatchAI Database Migration - Supabase Dashboard Instructions
=================================================================

STEP 1: Open Supabase Dashboard
1. Go to https://supabase.com/dashboard
2. Select your PatchAI project
3. Click on "SQL Editor" in the left sidebar

STEP 2: Create New Query
1. Click "New Query" button
2. Clear any existing content in the editor

STEP 3: Copy and Paste Migration SQL
1. Copy the SQL below (between the === lines)
2. Paste it into the Supabase SQL Editor
3. Click "Run" button to execute

STEP 4: Verify Success
1. Check that no errors appear in the results
2. Go to "Table Editor" to see your new tables:
   - user_profiles
   - chat_sessions  
   - messages
3. Verify Row Level Security is enabled on all tables

=================================================================
MIGRATION SQL TO COPY:
=================================================================
"""
    return instructions

def main():
    """Main function"""
    print("PatchAI Migration Copy Helper")
    print("=" * 50)
    
    # Read migration file
    result = read_migration_file()
    if not result:
        return
    
    sql_content, migration_path = result
    
    print(f"SUCCESS: Read migration file from {migration_path}")
    print(f"Size: {len(sql_content)} characters")
    
    # Create output file with instructions
    output_path = Path(__file__).parent / 'migration_for_dashboard.sql'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(create_dashboard_instructions())
        f.write(sql_content)
        f.write("\n\n=================================================================")
        f.write("\nEND OF MIGRATION SQL")
        f.write("\n=================================================================")
    
    print(f"\nSUCCESS: Created migration file for dashboard at:")
    print(f"   {output_path}")
    
    print(f"\nNEXT STEPS:")
    print(f"1. Open the file: {output_path}")
    print(f"2. Follow the instructions in the file")
    print(f"3. Copy the SQL and paste it into Supabase dashboard")
    print(f"4. Run the migration in Supabase SQL Editor")
    
    # Also copy to clipboard if possible
    try:
        import pyperclip
        pyperclip.copy(sql_content)
        print(f"\nBONUS: Migration SQL copied to clipboard!")
        print(f"You can paste it directly into Supabase dashboard")
    except ImportError:
        print(f"\nTIP: Install pyperclip for automatic clipboard copy:")
        print(f"   pip install pyperclip")
    
    print(f"\n" + "=" * 50)
    print(f"Ready to run migration in Supabase dashboard!")

if __name__ == "__main__":
    main()
