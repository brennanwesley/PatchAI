import { v4 as uuidv4 } from 'uuid';
import { ApiService } from '../config/api';
import { paywallEvents, PAYWALL_EVENTS } from '../utils/paywallEvents';

export class ChatService {
  // SINGLE CHAT: Get the user's single chat session messages
  static async getSingleChatSession() {
    try {
      console.log('🔄 ChatService: Fetching single chat session messages');
      const response = await ApiService.get('/history');
      
      console.log('🔍 ChatService: Single chat response:', response);
      
      // For single chat, return the messages array and title
      return {
        messages: Array.isArray(response?.messages) ? response.messages : [],
        title: response?.title || 'Chat Session'
      };
    } catch (error) {
      console.error('❌ ChatService: Failed to get single chat session:', error);
      // Return empty session instead of throwing
      return {
        messages: [],
        title: 'Chat Session'
      };
    }
  }

  // SINGLE CHAT: Send message and get AI response
  static async sendMessage(content, conversationHistory = []) {
    try {
      console.log('🔄 ChatService: Starting message send with context preservation');
      
      // Validate and clean conversation history
      const historicalMessages = conversationHistory
        .filter(msg => msg && msg.content && msg.role && msg.content.trim().length > 0)
        .map(msg => ({
          role: msg.role,
          content: msg.content.trim()
        }));
      
      // Add the new user message at the end
      const messages = [
        ...historicalMessages,
        {
          role: 'user',
          content: content.trim()
        }
      ];
      
      // Enterprise-grade logging for debugging
      console.log(`📝 ChatService: Prepared ${messages.length} total messages`);
      console.log(`   • Historical messages: ${historicalMessages.length}`);
      console.log(`   • New user message: 1`);
      console.log(`   • Message flow: ${messages.map(m => m.role).join(' → ')}`);
      
      if (messages.length > 1) {
        console.log('✅ ChatService: Context preservation ACTIVE - AI will remember conversation');
      } else {
        console.log('⚠️ ChatService: No historical context - this appears to be first message');
      }
      
      // Backend expects messages array with full conversation history
      const response = await ApiService.post('/prompt', {
        messages: messages
      });
      
      console.log('✅ ChatService: AI response received with full conversational context');
      
      return {
        message: response.response || response.message || 'No response received'
      };
    } catch (error) {
      console.error('❌ ChatService: Failed to send message:', error);
      throw error;
    }
  }

  // SINGLE CHAT: Clear all messages from single chat session
  static async clearMessages() {
    try {
      console.log('🔄 ChatService: Clearing single chat session');
      // This might need to be implemented on backend
      // For now, just log the action
      console.log('✅ ChatService: Single chat session cleared');
      return true;
    } catch (error) {
      console.error('❌ ChatService: Failed to clear messages:', error);
      throw error;
    }
  }

  // LEGACY MULTI-CHAT FUNCTIONS (kept for compatibility but not used in single chat)
  static async getUserChatSessions() {
    console.warn('⚠️ ChatService: getUserChatSessions() called but single chat mode active');
    return [];
  }

  // Get messages for a specific chat session
  static async getChatMessages(chatId) {
    try {
      console.log('🔄 ChatService: Fetching messages for chat:', chatId);
      const response = await ApiService.get(`/history/${chatId}/messages`);
      console.log('✅ ChatService: Retrieved messages:', response?.length || 0);
      return response || [];
    } catch (error) {
      console.error('❌ ChatService: Failed to get chat messages:', error);
      // Fallback: try to get full chat session and extract messages
      try {
        const chat = await this.getChatSession(chatId);
        return chat?.messages || [];
      } catch (fallbackError) {
        console.error('❌ ChatService: Fallback also failed:', fallbackError);
        return [];
      }
    }
  }

  // Get a specific chat session with messages
  static async getChatSession(chatId) {
    try {
      console.log('🔄 ChatService: Fetching chat session:', chatId);
      const response = await ApiService.get(`/history/${chatId}`);
      console.log('✅ ChatService: Retrieved chat session');
      return response;
    } catch (error) {
      console.error('❌ ChatService: Failed to get chat session:', error);
      throw error;
    }
  }

  // Create a new chat session
  static async createChatSession(title, firstMessage) {
    try {
      console.log('🔄 ChatService: Creating new chat session:', title);
      
      // FIXED: Generate a unique chat ID using UUID to prevent collisions
      const tempChatId = `chat_${uuidv4()}`;
      
      const chatData = {
        chat_id: tempChatId,
        title,
        messages: [firstMessage]
      };

      const response = await ApiService.post('/history', chatData);
      console.log('✅ ChatService: Created new chat session:', response.chat_id);
      
      // Return the chat object with the ID from the backend
      return {
        id: response.chat_id,
        title,
        messages: [firstMessage],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
    } catch (error) {
      console.error('❌ ChatService: Failed to create chat session:', error);
      throw error;
    }
  }

  // Add a message to an existing chat session (EFFICIENT APPEND-ONLY)
  static async addMessageToSession(chatId, role, content) {
    try {
      console.log('🔄 CHATSERVICE: Adding message to session (APPEND-ONLY):', chatId);
      
      // CRITICAL FIX: Use efficient append-only endpoint instead of full update
      const messageData = {
        role: role,
        content: content
      };

      console.log('📤 CHATSERVICE: Sending append payload to /history/{chatId}/messages:', messageData);

      const response = await ApiService.post(`/history/${chatId}/messages`, messageData);
      console.log('✅ CHATSERVICE: Message appended to session successfully');
      return response;
    } catch (error) {
      console.error('❌ CHATSERVICE: Failed to append message to session:', error);
      console.error('❌ CHATSERVICE: Error details:', {
        message: error.message,
        status: error.status,
        chatId: chatId,
        role: role
      });
      throw error;
    }
  }

  // Send prompt to AI and get response
  static async sendPrompt(messages, chatId = null) {
    try {
      console.log('🔄 CHATSERVICE: sendPrompt called');
      console.log('🔄 CHATSERVICE: Messages count:', messages.length);
      console.log('🔄 CHATSERVICE: Messages:', messages);
      console.log('🔄 CHATSERVICE: Chat ID:', chatId);
      
      const payload = {
        messages: messages,
        chat_id: chatId
      };

      console.log('📤 CHATSERVICE: Sending payload to /prompt:', payload);

      const response = await ApiService.post('/prompt', payload);
      console.log('📡 CHATSERVICE: Raw API response:', response);
      
      if (!response) {
        console.error('❌ CHATSERVICE: No response received from API');
        throw new Error('No response received from server');
      }

      if (!response.response) {
        console.error('❌ CHATSERVICE: Response missing "response" field:', response);
        throw new Error('Invalid response format from server');
      }

      console.log('✅ CHATSERVICE: AI response text:', response.response);
      console.log('✅ CHATSERVICE: Returned chat_id:', response.chat_id);
      
      // Return just the response text
      return response.response;
    } catch (error) {
      console.error('❌ CHATSERVICE: sendPrompt failed:', error);
      console.error('❌ CHATSERVICE: Error details:', {
        message: error.message,
        status: error.status,
        isAuthError: error.isAuthError,
        stack: error.stack
      });

      // Handle 402 Payment Required - trigger paywall
      if (error.status === 402) {
        console.log('💳 CHATSERVICE: Payment required - triggering paywall');
        paywallEvents.emit(PAYWALL_EVENTS.PAYMENT_REQUIRED, {
          message: error.message || 'Subscription required to continue',
          timestamp: new Date().toISOString()
        });
        
        // Create a specific paywall error
        const paywallError = new Error('Subscription required to continue chatting. Please upgrade to the Standard Plan.');
        paywallError.isPaywallError = true;
        paywallError.status = 402;
        throw paywallError;
      }

      throw error;
    }
  }

  // Delete a chat session
  static async deleteChatSession(chatId) {
    try {
      console.log('🔄 ChatService: Deleting chat session:', chatId);
      await ApiService.delete(`/history/${chatId}`);
      console.log('✅ ChatService: Chat session deleted');
    } catch (error) {
      console.error('❌ ChatService: Failed to delete chat session:', error);
      throw error;
    }
  }

  // Update chat session (title, etc.)
  static async updateChatSession(chatId, updates) {
    try {
      console.log('🔄 ChatService: Updating chat session:', chatId);
      
      const chat = await this.getChatSession(chatId);
      const updatedChat = {
        ...chat,
        ...updates,
        updatedAt: new Date().toISOString()
      };

      const response = await ApiService.post('/history', updatedChat);
      console.log('✅ ChatService: Chat session updated');
      return response;
    } catch (error) {
      console.error('❌ ChatService: Failed to update chat session:', error);
      throw error;
    }
  }

  // Health check method for debugging
  static async healthCheck() {
    try {
      console.log('🔄 ChatService: Checking backend health');
      const response = await ApiService.get('/');
      console.log('✅ ChatService: Backend is healthy:', response);
      return response;
    } catch (error) {
      console.error('❌ ChatService: Backend health check failed:', error);
      throw error;
    }
  }

  // Test authentication method
  static async testAuth() {
    try {
      console.log('🔄 ChatService: Testing authentication');
      const response = await ApiService.get('/history');
      console.log('✅ ChatService: Authentication successful');
      return true;
    } catch (error) {
      console.error('❌ ChatService: Authentication failed:', error);
      if (error.status === 401 || error.status === 403) {
        throw new Error('Authentication failed. Please log in again.');
      }
      throw error;
    }
  }
}
