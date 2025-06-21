import { API_ENDPOINTS, createApiRequest } from '../config/api';

export const ApiService = {
  /**
   * Send a prompt to the AI and get a response
   * @param {Array} messages - Array of message objects with role and content
   * @param {string} chatId - Optional chat session ID
   * @returns {Promise<Object>} AI response with chat_id
   */
  async sendPrompt(messages, chatId = null) {
    const payload = { messages };
    if (chatId) {
      payload.chat_id = chatId;
    }
    return createApiRequest(API_ENDPOINTS.PROMPT, 'POST', payload);
  },

  /**
   * Get chat sessions for the current user
   * @returns {Promise<Array>} Array of chat sessions
   */
  async getChatHistory() {
    return createApiRequest(API_ENDPOINTS.HISTORY, 'GET');
  },

  /**
   * Get specific chat session with full message history
   * @param {string} chatId - Chat session ID
   * @returns {Promise<Object>} Chat session with messages
   */
  async getChatSession(chatId) {
    return createApiRequest(`${API_ENDPOINTS.HISTORY}/${chatId}`, 'GET');
  },

  /**
   * Save or update chat session
   * @param {string} chatId - Chat session ID
   * @param {Array} messages - Array of message objects
   * @param {string} title - Optional chat title
   * @returns {Promise<Object>} Saved chat data
   */
  async saveChatSession(chatId, messages, title = null) {
    const payload = { chat_id: chatId, messages };
    if (title) {
      payload.title = title;
    }
    return createApiRequest(API_ENDPOINTS.HISTORY, 'POST', payload);
  },

  /**
   * Delete a chat session
   * @param {string} chatId - Chat session ID
   * @returns {Promise<Object>} Deletion confirmation
   */
  async deleteChatSession(chatId) {
    return createApiRequest(`${API_ENDPOINTS.HISTORY}/${chatId}`, 'DELETE');
  },

  /**
   * Check if the backend is healthy
   * @returns {Promise<boolean>} True if backend is healthy
   */
  async checkHealth() {
    try {
      const response = await fetch(API_ENDPOINTS.HEALTH);
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }
};

export default ApiService;
