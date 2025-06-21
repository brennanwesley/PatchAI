
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
-- PatchAI Database Schema Rebuild
-- Clean, optimized schema for multi-user chat functionality
-- Created: 2024-06-20 19:30:00 UTC

-- ============================================================================
-- STEP 1: Clean up existing tables (if they exist)
-- ============================================================================

-- Drop existing tables and their dependencies
DROP TABLE IF EXISTS public.messages CASCADE;
DROP TABLE IF EXISTS public.chat_sessions CASCADE;
DROP TABLE IF EXISTS public.user_profiles CASCADE;

-- Drop existing functions
DROP FUNCTION IF EXISTS public.handle_new_user() CASCADE;
DROP FUNCTION IF EXISTS public.handle_email_update() CASCADE;
DROP FUNCTION IF EXISTS public.generate_referral_code() CASCADE;
DROP FUNCTION IF EXISTS public.update_updated_at_column() CASCADE;

-- ============================================================================
-- STEP 2: Create utility functions
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 3: Create user_profiles table
-- ============================================================================

CREATE TABLE public.user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  display_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_profiles
CREATE POLICY "Users can view their own profile"
  ON public.user_profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
  ON public.user_profiles FOR INSERT
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
  ON public.user_profiles FOR UPDATE
  USING (auth.uid() = id);

-- Trigger to update updated_at
CREATE TRIGGER update_user_profiles_updated_at
  BEFORE UPDATE ON public.user_profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- Function to handle new user signups
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.user_profiles (id, email, display_name)
  VALUES (
    NEW.id, 
    NEW.email, 
    COALESCE(NEW.raw_user_meta_data->>'name', NEW.email)
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user creation
CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW 
  EXECUTE FUNCTION public.handle_new_user();

-- ============================================================================
-- STEP 4: Create chat_sessions table
-- ============================================================================

CREATE TABLE public.chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL DEFAULT 'New Chat',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policies for chat_sessions
CREATE POLICY "Users can view their own chat sessions"
  ON public.chat_sessions FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own chat sessions"
  ON public.chat_sessions FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own chat sessions"
  ON public.chat_sessions FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own chat sessions"
  ON public.chat_sessions FOR DELETE
  USING (auth.uid() = user_id);

-- Trigger to update updated_at
CREATE TRIGGER update_chat_sessions_updated_at
  BEFORE UPDATE ON public.chat_sessions
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================================
-- STEP 5: Create messages table
-- ============================================================================

CREATE TABLE public.messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chat_session_id UUID NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies for messages
CREATE POLICY "Users can view messages from their own chat sessions"
  ON public.messages FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.chat_sessions 
      WHERE id = messages.chat_session_id 
      AND user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert messages to their own chat sessions"
  ON public.messages FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.chat_sessions 
      WHERE id = messages.chat_session_id 
      AND user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update messages in their own chat sessions"
  ON public.messages FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.chat_sessions 
      WHERE id = messages.chat_session_id 
      AND user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete messages from their own chat sessions"
  ON public.messages FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.chat_sessions 
      WHERE id = messages.chat_session_id 
      AND user_id = auth.uid()
    )
  );

-- ============================================================================
-- STEP 6: Create indexes for performance
-- ============================================================================

-- User profiles indexes
CREATE INDEX idx_user_profiles_email ON public.user_profiles(email);

-- Chat sessions indexes
CREATE INDEX idx_chat_sessions_user_id ON public.chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_created_at ON public.chat_sessions(created_at DESC);
CREATE INDEX idx_chat_sessions_updated_at ON public.chat_sessions(updated_at DESC);

-- Messages indexes
CREATE INDEX idx_messages_chat_session_id ON public.messages(chat_session_id);
CREATE INDEX idx_messages_created_at ON public.messages(created_at ASC);
CREATE INDEX idx_messages_role ON public.messages(role);

-- Composite indexes for common queries
CREATE INDEX idx_messages_chat_session_created ON public.messages(chat_session_id, created_at ASC);

-- ============================================================================
-- STEP 7: Grant permissions
-- ============================================================================

-- Grant permissions to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_profiles TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.chat_sessions TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.messages TO authenticated;

-- ============================================================================
-- STEP 8: Create helpful views (optional)
-- ============================================================================

-- View for chat sessions with message counts
CREATE VIEW public.chat_sessions_with_counts AS
SELECT 
  cs.*,
  COALESCE(msg_counts.message_count, 0) as message_count,
  COALESCE(msg_counts.last_message_at, cs.created_at) as last_message_at
FROM public.chat_sessions cs
LEFT JOIN (
  SELECT 
    chat_session_id,
    COUNT(*) as message_count,
    MAX(created_at) as last_message_at
  FROM public.messages
  GROUP BY chat_session_id
) msg_counts ON cs.id = msg_counts.chat_session_id;

-- Grant access to the view
GRANT SELECT ON public.chat_sessions_with_counts TO authenticated;

-- ============================================================================
-- STEP 9: Insert system configuration (if needed)
-- ============================================================================

-- You can add any system-wide configuration here
-- For example, default system prompts, etc.

COMMENT ON TABLE public.user_profiles IS 'User profile information linked to Supabase Auth';
COMMENT ON TABLE public.chat_sessions IS 'Individual chat conversations for each user';
COMMENT ON TABLE public.messages IS 'Messages within chat sessions (user, assistant, system)';
COMMENT ON VIEW public.chat_sessions_with_counts IS 'Chat sessions with message counts and last message timestamps';


=================================================================
END OF MIGRATION SQL
=================================================================