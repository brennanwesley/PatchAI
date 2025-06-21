# Apply Database Migration

## Steps to Apply the Clean Database Schema

### 1. Backup Current Data (if needed)
If you have any important data in your current database, export it first:

1. Go to your Supabase Dashboard
2. Navigate to SQL Editor
3. Run these queries to export data:

```sql
-- Export existing chat sessions
SELECT * FROM chat_sessions;

-- Export existing messages  
SELECT * FROM messages;
```

### 2. Apply the Migration

1. **Go to Supabase Dashboard**
   - Open your Supabase project dashboard
   - Navigate to "SQL Editor"

2. **Copy and Run the Migration**
   - Open the file: `supabase/migrations/20240620193000_rebuild_clean_schema.sql`
   - Copy the entire contents
   - Paste into the SQL Editor
   - Click "Run"

3. **Verify the Migration**
   Run this query to verify tables were created:
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name IN ('user_profiles', 'chat_sessions', 'messages');
   ```

### 3. Test the Schema

Run these test queries to ensure everything works:

```sql
-- Test 1: Check RLS is enabled
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename IN ('user_profiles', 'chat_sessions', 'messages');

-- Test 2: Check policies exist
SELECT schemaname, tablename, policyname 
FROM pg_policies 
WHERE tablename IN ('user_profiles', 'chat_sessions', 'messages');

-- Test 3: Check indexes
SELECT indexname, tablename 
FROM pg_indexes 
WHERE tablename IN ('user_profiles', 'chat_sessions', 'messages');
```

### 4. Environment Variables

Ensure these are set in your Supabase project:

**Frontend (Vercel)**:
- `REACT_APP_SUPABASE_URL`: Your Supabase project URL
- `REACT_APP_SUPABASE_ANON_KEY`: Your Supabase anon key

**Backend (Render)**:
- `SUPABASE_URL`: Your Supabase project URL  
- `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key
- `OPENAI_API_KEY`: Your OpenAI API key

### 5. Test User Flow

After migration, test this flow:

1. **Sign up a new user** - Should auto-create user_profile
2. **Create a chat session** - Should work with RLS
3. **Send a message** - Should store properly
4. **View chat history** - Should only show user's own data

### Expected Results

After successful migration:
- ✅ Clean database schema with proper relationships
- ✅ Row Level Security protecting user data
- ✅ Optimized indexes for performance
- ✅ Automatic user profile creation
- ✅ Proper foreign key constraints

### Troubleshooting

If you encounter errors:

1. **Permission Errors**: Ensure you're using the service role key
2. **RLS Errors**: Check that auth.uid() is working in your session
3. **Foreign Key Errors**: Ensure parent records exist before creating children

### Next Steps

Once database migration is complete:
1. Update backend API endpoints
2. Update frontend data access patterns
3. Test complete user flow
4. Deploy updated code

This migration provides a solid foundation for rebuilding the chat functionality.
