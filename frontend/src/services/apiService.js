import { API_ENDPOINTS, createApiRequest } from '../config/api';

export const ApiService = {
  /**
   * Send a prompt to the AI and get a response
   * @param {Array} messages - Array of message objects with role and content
   * @returns {Promise<Object>} AI response
   */
  async sendPrompt(messages) {
    return createApiRequest(API_ENDPOINTS.PROMPT, 'POST', { messages });
  },

  /**
   * Get chat history for the current user
   * @returns {Promise<Array>} Array of chat sessions
   */
  async getChatHistory() {
    return createApiRequest(API_ENDPOINTS.HISTORY, 'GET');
  },

  /**
   * Save chat history
   * @param {Array} messages - Array of message objects
   * @returns {Promise<Object>} Saved chat data
   */
  async saveChatHistory(messages) {
    return createApiRequest(API_ENDPOINTS.HISTORY, 'POST', { messages });
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
