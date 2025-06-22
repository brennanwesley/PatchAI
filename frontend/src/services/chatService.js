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
      
      // Get current chat
      const chat = await this.getChatSession(chatId);
      const messages = chat.messages || [];
      
      // Add new message
      const newMessage = {
        id: `${role}-${Date.now()}`,
        role,
        content,
        timestamp: new Date().toISOString()
      };
      
      const updatedMessages = [...messages, newMessage];
      
      // Update chat with new messages
      const updateData = {
        ...chat,
        messages: updatedMessages,
        lastMessage: content,
        updatedAt: new Date().toISOString()
      };

      const response = await ApiService.post('/history', updateData);
      console.log('✅ ChatService: Message added to session');
      return response;
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
      return response;
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
}
