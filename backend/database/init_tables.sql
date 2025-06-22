-- PatchAI Database Schema
-- Create tables for chat sessions and messages

-- Create chat_sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_chat_session_id ON messages(chat_session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- Enable Row Level Security (RLS)
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for chat_sessions
CREATE POLICY IF NOT EXISTS "Users can view their own chat sessions" ON chat_sessions
    FOR SELECT USING (user_id = auth.uid()::text);

CREATE POLICY IF NOT EXISTS "Users can insert their own chat sessions" ON chat_sessions
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY IF NOT EXISTS "Users can update their own chat sessions" ON chat_sessions
    FOR UPDATE USING (user_id = auth.uid()::text);

CREATE POLICY IF NOT EXISTS "Users can delete their own chat sessions" ON chat_sessions
    FOR DELETE USING (user_id = auth.uid()::text);

-- Create RLS policies for messages
CREATE POLICY IF NOT EXISTS "Users can view messages from their chat sessions" ON messages
    FOR SELECT USING (
        chat_session_id IN (
            SELECT id FROM chat_sessions WHERE user_id = auth.uid()::text
        )
    );

CREATE POLICY IF NOT EXISTS "Users can insert messages to their chat sessions" ON messages
    FOR INSERT WITH CHECK (
        chat_session_id IN (
            SELECT id FROM chat_sessions WHERE user_id = auth.uid()::text
        )
    );

CREATE POLICY IF NOT EXISTS "Users can update messages in their chat sessions" ON messages
    FOR UPDATE USING (
        chat_session_id IN (
            SELECT id FROM chat_sessions WHERE user_id = auth.uid()::text
        )
    );

CREATE POLICY IF NOT EXISTS "Users can delete messages from their chat sessions" ON messages
    FOR DELETE USING (
        chat_session_id IN (
            SELECT id FROM chat_sessions WHERE user_id = auth.uid()::text
        )
    );
