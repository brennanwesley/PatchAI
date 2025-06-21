import { supabase } from '../supabaseClient';
import { ApiService } from './apiService';

/**
 * Chat Service - Handles all chat-related operations
 * Uses backend API for all chat operations
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

      const response = await ApiService.getChatHistory();
      return response.data || response || [];
    } catch (error) {
      console.error('Failed to fetch chat sessions:', error);
      if (error.isAuthError) {
        throw error;
      }
      return [];
    }
  }

  /**
   * Create a new chat session
   * @param {string} title - Chat title
   * @param {Object} firstMessage - First message object
   * @returns {Promise<Object>} Created chat session
   */
  static async createChatSession(title, firstMessage) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        throw new Error('User not authenticated');
      }

      // Send the first message to create the chat session
      const messages = [firstMessage];
      const response = await ApiService.sendPrompt(messages);
      
      return {
        id: response.chat_id,
        title: title,
        messages: messages,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
    } catch (error) {
      console.error('Failed to create chat session:', error);
      throw error;
    }
  }

  /**
   * Get a specific chat session with messages
   * @param {string} sessionId - Chat session ID
   * @returns {Promise<Object>} Chat session with messages
   */
  static async getChatSession(sessionId) {
    try {
      const response = await ApiService.getChatSession(sessionId);
      return response.data || response;
    } catch (error) {
      console.error('Failed to get chat session:', error);
      throw error;
    }
  }

  /**
   * Add a message to an existing chat session
   * @param {string} sessionId - Chat session ID
   * @param {string} role - Message role (user/assistant)
   * @param {string} content - Message content
   * @returns {Promise<void>}
   */
  static async addMessageToSession(sessionId, role, content) {
    try {
      // Get current session to append the new message
      const session = await this.getChatSession(sessionId);
      const messages = session.messages || [];
      
      const newMessage = {
        role: role,
        content: content,
        timestamp: new Date().toISOString()
      };
      
      const updatedMessages = [...messages, newMessage];
      await ApiService.saveChatSession(sessionId, updatedMessages);
    } catch (error) {
      console.error('Failed to add message to session:', error);
      throw error;
    }
  }

  /**
   * Delete a chat session
   * @param {string} sessionId - Chat session ID
   * @returns {Promise<void>}
   */
  static async deleteSession(sessionId) {
    try {
      await ApiService.deleteChatSession(sessionId);
    } catch (error) {
      console.error('Failed to delete chat session:', error);
      throw error;
    }
  }

  /**
   * Clear local storage data (for logout)
   */
  static clearLocalStorageData() {
    // No local storage to clear since we use backend API
    console.log('Local storage cleared');
  }
}
