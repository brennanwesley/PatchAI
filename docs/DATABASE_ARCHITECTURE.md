# PatchAI Database Architecture

## Overview
PatchAI uses Supabase (PostgreSQL) with Row Level Security (RLS) to ensure complete user isolation and data security. Each user can only access their own chat sessions and messages.

## Database Schema

### 1. `user_profiles` Table
Stores additional user information linked to Supabase Auth users.

```sql
CREATE TABLE public.user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  display_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Purpose**: 
- Extends Supabase Auth with custom user data
- Automatically created when user signs up
- Stores display preferences and profile information

**Security**: 
- Users can only view/edit their own profile
- Automatically synced with auth.users table

### 2. `chat_sessions` Table
Represents individual chat conversations.

```sql
CREATE TABLE public.chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL DEFAULT 'New Chat',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Purpose**:
- Groups related messages into conversations
- Allows users to have multiple concurrent chats
- Provides chat titles for organization

**Security**:
- Each session belongs to exactly one user
- Users can only access their own sessions
- Cascade delete when user is deleted

### 3. `messages` Table
Stores individual messages within chat sessions.

```sql
CREATE TABLE public.messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chat_session_id UUID NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Purpose**:
- Stores all chat messages (user input, AI responses, system messages)
- Maintains conversation history
- Supports metadata for future features (attachments, etc.)

**Security**:
- Users can only access messages from their own chat sessions
- Enforced through RLS policies that check session ownership

## Row Level Security (RLS) Policies

### User Isolation
Every table has RLS policies that ensure:
1. Users can only see their own data
2. Users can only modify their own data
3. No cross-user data leakage is possible

### Policy Examples

**Chat Sessions**:
```sql
-- Users can only view their own chat sessions
CREATE POLICY "Users can view their own chat sessions"
  ON public.chat_sessions FOR SELECT
  USING (auth.uid() = user_id);
```

**Messages**:
```sql
-- Users can only view messages from their own chat sessions
CREATE POLICY "Users can view messages from their own chat sessions"
  ON public.messages FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.chat_sessions 
      WHERE id = messages.chat_session_id 
      AND user_id = auth.uid()
    )
  );
```

## Data Flow

### 1. User Registration
```
1. User signs up via Supabase Auth
2. Trigger automatically creates user_profiles record
3. User can immediately start creating chat sessions
```

### 2. Chat Creation
```
1. Frontend creates new chat_session
2. Database assigns UUID and links to user
3. First message triggers chat title generation
```

### 3. Message Flow
```
1. User sends message → stored as 'user' role
2. Backend processes with OpenAI → stored as 'assistant' role
3. All messages linked to chat_session_id
4. Frontend displays in chronological order
```

## Performance Optimizations

### Indexes
- `idx_chat_sessions_user_id`: Fast user session lookup
- `idx_messages_chat_session_id`: Fast message retrieval
- `idx_messages_created_at`: Chronological message ordering
- `idx_messages_chat_session_created`: Composite for common queries

### Views
- `chat_sessions_with_counts`: Includes message counts and last activity

## API Integration

### Frontend → Database
- Uses Supabase client with user JWT
- All queries automatically filtered by RLS
- Real-time subscriptions for live updates

### Backend → Database
- Uses service role key for admin operations
- Can bypass RLS when needed for system operations
- Validates user permissions before operations

## Security Features

### Authentication
- JWT tokens from Supabase Auth
- Automatic token refresh
- Session management

### Authorization
- Row Level Security on all tables
- User-scoped queries only
- No shared data between users

### Data Protection
- Foreign key constraints prevent orphaned data
- Cascade deletes maintain referential integrity
- Input validation via CHECK constraints

## Migration Strategy

### Current Migration
- `20240620193000_rebuild_clean_schema.sql`
- Drops existing tables and recreates with clean schema
- Preserves data integrity and security

### Future Migrations
- Always test on staging first
- Use transactions for atomic changes
- Include rollback procedures

## Monitoring and Maintenance

### Key Metrics
- Active chat sessions per user
- Message volume and frequency
- Query performance (especially RLS overhead)
- Storage usage growth

### Regular Tasks
- Monitor RLS policy performance
- Update indexes based on query patterns
- Archive old chat sessions if needed
- Backup strategy for user data

## Troubleshooting

### Common Issues
1. **RLS Policy Errors**: Check user authentication and policy conditions
2. **Foreign Key Violations**: Ensure chat_session exists before adding messages
3. **Performance Issues**: Review indexes and query patterns

### Debug Queries
```sql
-- Check user's chat sessions
SELECT * FROM chat_sessions WHERE user_id = auth.uid();

-- Check message counts per session
SELECT 
  cs.title,
  COUNT(m.id) as message_count
FROM chat_sessions cs
LEFT JOIN messages m ON cs.id = m.chat_session_id
WHERE cs.user_id = auth.uid()
GROUP BY cs.id, cs.title;
```

This architecture ensures complete user isolation, scalability, and security for the PatchAI chat application.
