// API Configuration
import { supabase } from '../supabaseClient';

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

/**
 * Get the current user's JWT token from Supabase session
 * @returns {Promise<string|null>} JWT token or null if not authenticated
 */
const getAuthToken = async () => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    console.log('🔐 Supabase session:', session ? 'Present' : 'Null');
    console.log('🔐 Access token:', session?.access_token ? 'Present' : 'Missing');
    if (session?.access_token) {
      console.log('🔐 Token preview:', session.access_token.substring(0, 50) + '...');
    }
    return session?.access_token || null;
  } catch (error) {
    console.error('Error getting auth token:', error);
    return null;
  }
};

/**
 * Create headers with authentication if user is logged in
 * @returns {Promise<Object>} Headers object with optional Authorization
 */
const createAuthHeaders = async () => {
  const headers = { ...DEFAULT_HEADERS };
  
  const token = await getAuthToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  return headers;
};

export const createApiRequest = async (endpoint, method = 'GET', data = null) => {
  const headers = await createAuthHeaders();
  
  const options = {
    method,
    headers,
    credentials: 'include' // Important for cookies, authorization headers with HTTPS
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(endpoint, options);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      console.error(`API Error ${response.status}:`, {
        status: response.status,
        statusText: response.statusText,
        url: endpoint,
        errorData
      });
      
      // Handle authentication errors specifically
      if (response.status === 401 || response.status === 403) {
        const authError = new Error(errorData.detail || 'Authentication required');
        authError.status = response.status;
        authError.isAuthError = true;
        throw authError;
      }
      
      // Handle validation errors (422)
      if (response.status === 422) {
        const validationError = new Error(errorData.detail || 'Validation error');
        validationError.status = response.status;
        validationError.validationDetails = errorData;
        throw validationError;
      }
      
      throw new Error(errorData.detail || 'API request failed');
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', {
      message: error.message,
      status: error.status,
      isAuthError: error.isAuthError,
      stack: error.stack
    });
    throw error;
  }
};

// ApiService class for easy method access
export class ApiService {
  static async get(endpoint) {
    const fullUrl = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
    return await createApiRequest(fullUrl, 'GET');
  }

  static async post(endpoint, data) {
    const fullUrl = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
    return await createApiRequest(fullUrl, 'POST', data);
  }

  static async put(endpoint, data) {
    const fullUrl = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
    return await createApiRequest(fullUrl, 'PUT', data);
  }

  static async delete(endpoint) {
    const fullUrl = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
    return await createApiRequest(fullUrl, 'DELETE');
  }
}
