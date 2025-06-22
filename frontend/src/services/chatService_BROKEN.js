import { supabase } from '../supabaseClient';
import { ApiService } from './apiService';

/**
 * REBUILT Chat Service - Clean and Simple
 * Handles all chat operations with proper error handling
 */

export class ChatService {
  /**
   * Get all chat sessions for the current user
   */
  static async getUserChatSessions() {
    try {
      console.log('📂 ChatService: Getting user chat sessions');
      
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        console.error('❌ User not authenticated');
        return [];
      }

      const response = await ApiService.getChatHistory();
      const chats = response.data || response || [];
      
      console.log(`✅ ChatService: Retrieved ${chats.length} chat sessions`);
      return chats;
      
    } catch (error) {
      console.error('❌ ChatService: Failed to get chat sessions:', error);
      
      // Don't throw auth errors, just return empty array
      if (error.isAuthError) {
        console.log('🔐 Authentication error, returning empty chats');
        return [];
      }
      
      return [];
    }
  }

  /**
   * Create a new chat session
   */
  static async createChatSession(title, firstMessage) {
    try {
      console.log('🆕 ChatService: Creating new chat session');
      
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        throw new Error('User not authenticated');
      }

      // Create the chat by sending the first message
      const messages = [{
        role: firstMessage.role,
        content: firstMessage.content
      }];
      
      const response = await ApiService.sendPrompt(messages);
      
      if (!response.chat_id) {
        throw new Error('No chat_id returned from API');
      }
      
      const newChat = {
        id: response.chat_id,
        title: title,
        messages: [firstMessage], // Include the first message
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        lastMessage: firstMessage.content
      };
      
      console.log('✅ ChatService: Chat session created:', newChat.id);
      return newChat;
      
    } catch (error) {
      console.error('❌ ChatService: Failed to create chat session:', error);
      throw error;
    }
  }

  /**
   * Get a specific chat session
   */
  static async getChatSession(sessionId) {
    try {
      console.log('📋 ChatService: Getting chat session:', sessionId);
      
      const response = await ApiService.getChatSession(sessionId);
      const chatData = response.data || response;
      
      console.log('✅ ChatService: Chat session retrieved');
      return chatData;
      
    } catch (error) {
      console.error('❌ ChatService: Failed to get chat session:', error);
      throw error;
    }
  }

  /**
   * Add a message to an existing chat session
   * SIMPLIFIED - Just save to backend, don't complicate it
   */
  static async addMessageToSession(sessionId, role, content) {
    try {
      console.log('💾 ChatService: Adding message to session:', sessionId);
      
      // Create message object
      const message = {
        role: role,
        content: content,
        timestamp: new Date().toISOString()
      };
      
      // Get current session
      const session = await this.getChatSession(sessionId);
      const currentMessages = session.messages || [];
      
      // Add new message
      const updatedMessages = [...currentMessages, message];
      
      // Save updated session
      await ApiService.saveChatSession(sessionId, updatedMessages);
      
      console.log('✅ ChatService: Message added to session');
      
    } catch (error) {
      console.error('❌ ChatService: Failed to add message:', error);
      throw error;
    }
  }

  /**
   * Delete a chat session
   */
  static async deleteSession(sessionId) {
    try {
      console.log('🗑️ ChatService: Deleting session:', sessionId);
      
      await ApiService.deleteChatSession(sessionId);
      
      console.log('✅ ChatService: Session deleted');
      
    } catch (error) {
      console.error('❌ ChatService: Failed to delete session:', error);
      throw error;
    }
  }

  /**
   * Clear any cached data
   */
  static clearLocalStorageData() {
    console.log('🧹 ChatService: Clearing local data');
    // Nothing to clear since we use backend API
  }
}
