#!/usr/bin/env node

/**
 * Automated Database Migration Script for PatchAI
 * This script applies the clean database schema migration automatically
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// Load environment variables
require('dotenv').config({ path: path.join(__dirname, '../.env') });

const SUPABASE_URL = process.env.REACT_APP_SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.error('❌ Missing required environment variables:');
  console.error('   REACT_APP_SUPABASE_URL');
  console.error('   SUPABASE_SERVICE_ROLE_KEY');
  console.error('\nPlease set these in your .env file');
  process.exit(1);
}

// Create Supabase client with service role key
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

async function runMigration() {
  console.log('🚀 Starting PatchAI Database Migration...\n');

  try {
    // Read the migration file
    const migrationPath = path.join(__dirname, '../supabase/migrations/20240620193000_rebuild_clean_schema.sql');
    
    if (!fs.existsSync(migrationPath)) {
      throw new Error(`Migration file not found: ${migrationPath}`);
    }

    const migrationSQL = fs.readFileSync(migrationPath, 'utf8');
    
    console.log('📖 Reading migration file...');
    console.log(`   File: ${migrationPath}`);
    console.log(`   Size: ${migrationSQL.length} characters\n`);

    // Split the migration into individual statements
    const statements = migrationSQL
      .split(';')
      .map(stmt => stmt.trim())
      .filter(stmt => stmt.length > 0 && !stmt.startsWith('--'));

    console.log(`📝 Found ${statements.length} SQL statements to execute\n`);

    // Execute each statement
    let successCount = 0;
    let errorCount = 0;

    for (let i = 0; i < statements.length; i++) {
      const statement = statements[i] + ';';
      
      try {
        console.log(`⏳ Executing statement ${i + 1}/${statements.length}...`);
        
        const { data, error } = await supabase.rpc('exec_sql', {
          sql: statement
        });

        if (error) {
          // Try direct query if RPC fails
          const { data: directData, error: directError } = await supabase
            .from('information_schema.tables')
            .select('*')
            .limit(1);

          if (directError) {
            throw error;
          }

          // Execute using raw SQL
          const { error: sqlError } = await supabase.rpc('exec_sql', {
            sql: statement
          });

          if (sqlError) {
            throw sqlError;
          }
        }

        console.log(`✅ Statement ${i + 1} executed successfully`);
        successCount++;

      } catch (error) {
        console.error(`❌ Error in statement ${i + 1}:`, error.message);
        
        // Log the problematic statement for debugging
        console.error(`   Statement: ${statement.substring(0, 100)}...`);
        errorCount++;

        // Continue with other statements unless it's a critical error
        if (error.message.includes('already exists')) {
          console.log(`   ⚠️  Skipping - object already exists`);
          successCount++;
        } else if (error.message.includes('permission denied')) {
          console.error(`   🔒 Permission denied - check service role key`);
          break;
        }
      }
    }

    console.log('\n📊 Migration Summary:');
    console.log(`   ✅ Successful: ${successCount}`);
    console.log(`   ❌ Errors: ${errorCount}`);
    console.log(`   📝 Total: ${statements.length}`);

    if (errorCount === 0) {
      console.log('\n🎉 Database migration completed successfully!');
      
      // Verify the migration
      await verifyMigration();
      
    } else {
      console.log('\n⚠️  Migration completed with some errors.');
      console.log('   Please check the errors above and verify your database state.');
    }

  } catch (error) {
    console.error('\n💥 Migration failed:', error.message);
    console.error('\nPlease check:');
    console.error('1. Your Supabase URL and service role key are correct');
    console.error('2. You have sufficient permissions');
    console.error('3. Your Supabase project is accessible');
    process.exit(1);
  }
}

async function verifyMigration() {
  console.log('\n🔍 Verifying migration...');

  try {
    // Check if tables exist
    const tables = ['user_profiles', 'chat_sessions', 'messages'];
    
    for (const tableName of tables) {
      const { data, error } = await supabase
        .from(tableName)
        .select('*')
        .limit(1);

      if (error) {
        console.error(`❌ Table ${tableName} verification failed:`, error.message);
      } else {
        console.log(`✅ Table ${tableName} exists and is accessible`);
      }
    }

    // Test RLS policies by trying to access without auth
    console.log('\n🔒 Testing Row Level Security...');
    
    const { data: rlsData, error: rlsError } = await supabase
      .from('chat_sessions')
      .select('*')
      .limit(1);

    if (rlsError && rlsError.message.includes('row-level security')) {
      console.log('✅ RLS is properly configured');
    } else {
      console.log('⚠️  RLS might not be properly configured');
    }

    console.log('\n✨ Migration verification complete!');

  } catch (error) {
    console.error('❌ Verification failed:', error.message);
  }
}

// Run the migration
runMigration().catch(console.error);
