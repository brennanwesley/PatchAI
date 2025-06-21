import { supabase } from '../supabaseClient';
import { ApiService } from './apiService';

/**
 * Chat Service - Handles all chat-related operations
 * Uses Supabase for database operations and API service for AI completions
 */

export class ChatService {
  /**
   * Get all chat sessions for the current user
   * @returns {Promise<Array>} Array of chat sessions
   */
  static async getUserChatSessions() {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        console.error('User not authenticated');
        return [];
      }

      let sessions = [];
      let apiError = null;

      // First try to get from API
      try {
        const response = await ApiService.getChatHistory();
        if (response && response.data) {
          sessions = response.data;
          console.log('Fetched sessions from API:', sessions);
          return sessions;
        }
      } catch (error) {
        apiError = error;
        
        // If it's an authentication error, don't fall back to Supabase
        if (error.isAuthError) {
          console.error('Authentication error when fetching chat history:', error);
          throw error;
        }
        
        console.warn('Failed to fetch chat history from API, falling back to Supabase:', error);
      }

      // Fallback to Supabase if API fails (but not for auth errors)
      try {
        const { data, error: supabaseError } = await supabase
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
          .eq('user_id', user.id)
          .order('updated_at', { ascending: false });

        if (supabaseError) {
          console.error('Supabase error fetching chat sessions:', supabaseError);
          throw supabaseError;
        }

        // Transform data to match frontend format
        sessions = (data || []).map(session => ({
          id: session.id,
          title: session.title || 'New Chat',
          messages: (session.messages || []).sort((a, b) => new Date(a.created_at) - new Date(b.created_at)),
          messageCount: session.messages?.length || 0,
          lastMessage: session.messages?.length > 0 
            ? session.messages[session.messages.length - 1].content 
            : 'No messages yet',
          createdAt: session.created_at,
          updatedAt: session.updated_at
        }));
        
        console.log('Fetched sessions from Supabase (fallback):', sessions);
        return sessions;
      } catch (supabaseError) {
        console.error('Failed to fetch chat sessions from both API and Supabase:', {
          apiError,
          supabaseError
        });
        
        // If both API and Supabase fail, throw the original API error if it was auth-related
        if (apiError?.isAuthError) {
          throw apiError;
        }
        
        // Otherwise throw the Supabase error
        throw supabaseError;
      }
    } catch (error) {
      console.error('Error in getUserChatSessions:', error);
      throw error;
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
   * @param {string} chatId - Chat session ID
   * @param {string} role - Message role ('user' or 'assistant')
   * @param {string} content - Message content
   * @returns {Promise<Object>} Added message
   */
  static async addMessageToSession(chatId, role, content) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        throw new Error('User not authenticated');
      }

      // First try to save via API
      try {
        const response = await ApiService.sendPrompt([{ role, content }]);
        return response;
      } catch (apiError) {
        console.warn('Failed to save message via API, falling back to Supabase:', apiError);
      }

      // Verify chat session exists and belongs to user
      const { data: chatSession, error: chatError } = await supabase
        .from('chat_sessions')
        .select('id')
        .eq('id', chatId)
        .eq('user_id', user.id)
        .single();

      if (chatError || !chatSession) {
        throw new Error('Chat session not found or access denied');
      }

      // Insert message
      const { data: message, error } = await supabase
        .from('messages')
        .insert({
          chat_id: chatId,
          role: role,
          content: content,
          user_id: user.id
        })
        .select()
        .single();

      if (error) throw error;

      // Update the chat's updated_at timestamp
      const { error: updateError } = await supabase
        .from('chat_sessions')
        .update({ updated_at: new Date().toISOString() })
        .eq('id', chatId);

      if (updateError) console.error('Error updating chat timestamp:', updateError);

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
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        console.error('User not authenticated');
        return [];
      }

      const { data: messages, error } = await supabase
        .from('messages')
        .select('*')
        .eq('chat_id', sessionId)
        .eq('user_id', user.id)
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
