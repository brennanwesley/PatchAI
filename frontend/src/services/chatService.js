import { ApiService } from '../config/api';

export class ChatService {
  // Get all chat sessions for the current user
  static async getUserChatSessions() {
    try {
      console.log('🔄 ChatService: Fetching user chat sessions');
      const response = await ApiService.get('/history');
      console.log('✅ ChatService: Retrieved chat sessions:', response?.length || 0);
      return response || [];
    } catch (error) {
      console.error('❌ ChatService: Failed to get user chat sessions:', error);
      throw error;
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
      
      const chatData = {
        title,
        messages: [firstMessage]
      };

      const response = await ApiService.post('/history', chatData);
      console.log('✅ ChatService: Created new chat session:', response.id);
      return response;
    } catch (error) {
      console.error('❌ ChatService: Failed to create chat session:', error);
      throw error;
    }
  }

  // Add a message to an existing chat session
  static async addMessageToSession(chatId, role, content) {
    try {
      console.log('🔄 ChatService: Adding message to session:', chatId);
      
      const messageData = {
        chat_id: chatId,
        role,
        content,
        timestamp: new Date().toISOString()
      };

      // Try direct message addition first (more efficient)
      try {
        const response = await ApiService.post(`/history/${chatId}/messages`, messageData);
        console.log('✅ ChatService: Message added directly to session');
        return response;
      } catch (directError) {
        console.warn('⚠️ Direct message addition failed, falling back to full chat update');
        
        // Fallback: Get current chat and update with new message
        const chat = await this.getChatSession(chatId);
        const messages = chat.messages || [];
        
        const newMessage = {
          id: `${role}-${Date.now()}`,
          role,
          content,
          timestamp: new Date().toISOString()
        };
        
        const updatedMessages = [...messages, newMessage];
        
        const updateData = {
          ...chat,
          messages: updatedMessages,
          lastMessage: content,
          updatedAt: new Date().toISOString()
        };

        const response = await ApiService.post('/history', updateData);
        console.log('✅ ChatService: Message added via chat update');
        return response;
      }
    } catch (error) {
      console.error('❌ ChatService: Failed to add message to session:', error);
      throw error;
    }
  }

  // Send prompt to AI and get response
  static async sendPrompt(messages, chatId = null) {
    try {
      console.log('🔄 ChatService: Sending prompt to AI');
      
      const requestData = {
        messages,
        ...(chatId && { chat_id: chatId })
      };

      const response = await ApiService.post('/prompt', requestData);
      console.log('✅ ChatService: Received AI response');
      
      // Handle multiple possible response formats
      if (typeof response === 'string') {
        return response; // Direct string response
      } else if (response?.response) {
        return response.response; // { response: "..." } format
      } else if (response?.content) {
        return response.content; // { content: "..." } format
      } else if (response?.message) {
        return response.message; // { message: "..." } format
      } else {
        console.warn('⚠️ Unexpected AI response format:', response);
        return response?.toString() || 'No response received';
      }
    } catch (error) {
      console.error('❌ ChatService: Failed to send prompt:', error);
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
