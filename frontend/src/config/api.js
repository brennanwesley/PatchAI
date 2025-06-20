// API Configuration
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'https://patchai-backend.onrender.com';

export const API_ENDPOINTS = {
  PROMPT: `${API_BASE_URL}/prompt`,
  HISTORY: `${API_BASE_URL}/history`,
  HEALTH: `${API_BASE_URL}/`
};

export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
};

export const createApiRequest = async (endpoint, method = 'GET', data = null) => {
  const options = {
    method,
    headers: DEFAULT_HEADERS,
    credentials: 'include' // Important for cookies, authorization headers with HTTPS
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(endpoint, options);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'API request failed');
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};
