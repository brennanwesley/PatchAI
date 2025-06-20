import { supabase } from '../supabaseClient';

/**
 * Chat Service - Handles all chat-related database operations with user isolation
 * Replaces localStorage with secure Supabase database storage
 */

export class ChatService {
  /**
   * Get all chat sessions for the current user
   * @returns {Promise<Array>} Array of chat sessions
   */
  static async getUserChatSessions() {
    try {
      const { data: sessions, error } = await supabase
        .from('chat_sessions')
        .select(`
          id,
          title,
          created_at,
          updated_at,
          messages (
            id,
            role,
            content,
            created_at
          )
        `)
        .order('updated_at', { ascending: false });

      if (error) {
        console.error('Error fetching chat sessions:', error);
        throw error;
      }

      // Transform data to match frontend format
      return sessions.map(session => ({
        id: session.id,
        title: session.title,
        messages: session.messages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at)),
        messageCount: session.messages.length,
        lastMessage: session.messages.length > 0 
          ? session.messages[session.messages.length - 1].content 
          : 'No messages yet',
        createdAt: session.created_at,
        updatedAt: session.updated_at
      }));
    } catch (error) {
      console.error('Error in getUserChatSessions:', error);
      return [];
    }
  }

  /**
   * Create a new chat session
   * @param {string} title - Chat session title
   * @param {Object} firstMessage - First message object {role, content}
   * @returns {Promise<Object>} Created chat session
   */
  static async createChatSession(title = 'New Chat', firstMessage = null) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        throw new Error('User not authenticated');
      }

      // Create chat session
      const { data: session, error: sessionError } = await supabase
        .from('chat_sessions')
        .insert({
          user_id: user.id,
          title: title
        })
        .select()
        .single();

      if (sessionError) {
        console.error('Error creating chat session:', sessionError);
        throw sessionError;
      }

      // Add first message if provided
      if (firstMessage) {
        await this.addMessageToSession(session.id, firstMessage.role, firstMessage.content);
      }

      return {
        id: session.id,
        title: session.title,
        messages: firstMessage ? [firstMessage] : [],
        messageCount: firstMessage ? 1 : 0,
        lastMessage: firstMessage ? firstMessage.content : 'No messages yet',
        createdAt: session.created_at,
        updatedAt: session.updated_at
      };
    } catch (error) {
      console.error('Error in createChatSession:', error);
      throw error;
    }
  }

  /**
   * Add a message to a chat session
   * @param {string} sessionId - Chat session ID
   * @param {string} role - Message role (user, assistant, system)
   * @param {string} content - Message content
   * @returns {Promise<Object>} Created message
   */
  static async addMessageToSession(sessionId, role, content) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        throw new Error('User not authenticated');
      }

      // Insert message
      const { data: message, error: messageError } = await supabase
        .from('messages')
        .insert({
          chat_session_id: sessionId,
          user_id: user.id,
          role: role,
          content: content
        })
        .select()
        .single();

      if (messageError) {
        console.error('Error adding message:', messageError);
        throw messageError;
      }

      // Update chat session timestamp
      await supabase
        .from('chat_sessions')
        .update({ updated_at: new Date().toISOString() })
        .eq('id', sessionId)
        .eq('user_id', user.id);

      return {
        id: message.id,
        role: message.role,
        content: message.content,
        timestamp: message.created_at
      };
    } catch (error) {
      console.error('Error in addMessageToSession:', error);
      throw error;
    }
  }

  /**
   * Get messages for a specific chat session
   * @param {string} sessionId - Chat session ID
   * @returns {Promise<Array>} Array of messages
   */
  static async getSessionMessages(sessionId) {
    try {
      const { data: messages, error } = await supabase
        .from('messages')
        .select('*')
        .eq('chat_session_id', sessionId)
        .order('created_at', { ascending: true });

      if (error) {
        console.error('Error fetching session messages:', error);
        throw error;
      }

      return messages.map(msg => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        timestamp: msg.created_at
      }));
    } catch (error) {
      console.error('Error in getSessionMessages:', error);
      return [];
    }
  }

  /**
   * Update chat session title
   * @param {string} sessionId - Chat session ID
   * @param {string} newTitle - New title
   * @returns {Promise<boolean>} Success status
   */
  static async updateSessionTitle(sessionId, newTitle) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        throw new Error('User not authenticated');
      }

      const { error } = await supabase
        .from('chat_sessions')
        .update({ 
          title: newTitle,
          updated_at: new Date().toISOString()
        })
        .eq('id', sessionId)
        .eq('user_id', user.id);

      if (error) {
        console.error('Error updating session title:', error);
        throw error;
      }

      return true;
    } catch (error) {
      console.error('Error in updateSessionTitle:', error);
      return false;
    }
  }

  /**
   * Delete a chat session and all its messages
   * @param {string} sessionId - Chat session ID
   * @returns {Promise<boolean>} Success status
   */
  static async deleteSession(sessionId) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        throw new Error('User not authenticated');
      }

      // Delete session (messages will be deleted via CASCADE)
      const { error } = await supabase
        .from('chat_sessions')
        .delete()
        .eq('id', sessionId)
        .eq('user_id', user.id);

      if (error) {
        console.error('Error deleting session:', error);
        throw error;
      }

      return true;
    } catch (error) {
      console.error('Error in deleteSession:', error);
      return false;
    }
  }

  /**
   * Clear all localStorage chat data (migration helper)
   * This should be called once to clean up old localStorage data
   */
  static clearLocalStorageData() {
    try {
      localStorage.removeItem('patchai-chats');
      localStorage.removeItem('patchai-active-chat');
      console.log('Cleared legacy localStorage chat data');
    } catch (error) {
      console.error('Error clearing localStorage:', error);
    }
  }
}
