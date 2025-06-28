import { v4 as uuidv4 } from 'uuid';
import { ApiService } from '../config/api';
import { paywallEvents, PAYWALL_EVENTS } from '../utils/paywallEvents';

export class ChatService {
  // Get all chat sessions for the current user
  static async getUserChatSessions() {
    try {
      console.log('🔄 ChatService: Fetching user chat sessions');
      const response = await ApiService.get('/history');
      
      // CRITICAL: Debug the exact response from backend
      console.log('🔍 ChatService: Raw backend response:', {
        type: typeof response,
        value: response,
        isArray: Array.isArray(response),
        length: response?.length
      });
      
      // CRITICAL: Ensure we always return an array
      if (!Array.isArray(response)) {
        console.warn('⚠️ ChatService: Backend returned non-array, converting to empty array:', response);
        return [];
      }
      
      console.log('✅ ChatService: Retrieved', response.length, 'chat sessions');
      return response;
    } catch (error) {
      console.error('❌ ChatService: Failed to get user chat sessions:', error);
      // Return empty array instead of throwing to prevent app crash
      console.warn('⚠️ ChatService: Returning empty array due to error');
      return [];
    }
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

  // Add a message to an existing chat session
  static async addMessageToSession(chatId, role, content) {
    try {
      console.log('🔄 CHATSERVICE: Adding message to session:', chatId);
      
      // Get current chat and update with new message
      const chat = await this.getChatSession(chatId);
      const messages = chat.messages || [];
      
      // FIXED: Use UUID for message IDs to prevent collisions
      const messageId = uuidv4();
      const newMessage = {
        id: `${role}-${messageId}`,
        role,
        content,
        timestamp: new Date().toISOString()
      };
      
      const updatedMessages = [...messages, newMessage];
      
      // FIXED: Send only the fields that backend expects (SaveChatRequest schema)
      const updateData = {
        chat_id: chatId,
        messages: updatedMessages,
        title: chat.title || 'Chat Session'
      };

      console.log('📤 CHATSERVICE: Sending update payload to /history:', updateData);

      const response = await ApiService.post('/history', updateData);
      console.log('✅ CHATSERVICE: Message added to session successfully');
      return response;
    } catch (error) {
      console.error('❌ CHATSERVICE: Failed to add message to session:', error);
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
