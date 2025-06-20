import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

// Debug logging
console.log('Supabase URL:', supabaseUrl ? 'Present' : 'Missing');
console.log('Supabase Key:', supabaseAnonKey ? 'Present' : 'Missing');

if (!supabaseUrl || !supabaseAnonKey) {
  const errorMsg = 'Missing Supabase configuration. Please set REACT_APP_SUPABASE_URL and REACT_APP_SUPABASE_ANON_KEY in your environment variables';
  console.error(errorMsg);
  throw new Error(errorMsg);
}

// Validate URL format
try {
  new URL(supabaseUrl);
} catch (err) {
  const errorMsg = `Invalid Supabase URL format: ${supabaseUrl}. It should look like: https://xxxxxxxxxxxxxx.supabase.co`;
  console.error(errorMsg);
  throw new Error(errorMsg);
}

// Create a single supabase client for interacting with your database
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});

/**
 * Signs up a new user with email and password
 * @param {string} email - User's email
 * @param {string} password - User's password
 * @returns {Promise<{user: object|null, error: Error|null}>} - User data or error
 */
export const signUp = async (email, password) => {
  try {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    });
    return { user: data?.user, error };
  } catch (error) {
    console.error('Error signing up:', error);
    return { user: null, error };
  }
};

/**
 * Signs in a user with email and password
 * @param {string} email - User's email
 * @param {string} password - User's password
 * @returns {Promise<{user: object|null, error: Error|null}>} - User data or error
 */
export const signIn = async (email, password) => {
  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    return { user: data?.user, error };
  } catch (error) {
    console.error('Error signing in:', error);
    return { user: null, error };
  }
};

/**
 * Signs out the current user
 * @returns {Promise<{error: Error|null}>} - Error if any
 */
export const signOut = async () => {
  try {
    const { error } = await supabase.auth.signOut();
    return { error };
  } catch (error) {
    console.error('Error signing out:', error);
    return { error };
  }
};

/**
 * Gets the currently logged in user
 * @returns {Promise<object|null>} - Current user or null if not authenticated
 */
export const getCurrentUser = async () => {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    return user;
  } catch (error) {
    console.error('Error getting current user:', error);
    return null;
  }
};

/**
 * Gets the current session
 * @returns {Promise<object|null>} - Current session or null if not authenticated
 */
export const getSession = async () => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    return session;
  } catch (error) {
    console.error('Error getting session:', error);
    return null;
  }
};

/**
 * Subscribe to auth state changes
 * @param {Function} callback - Callback function that receives the auth state
 * @returns {object} - Object with an unsubscribe method
 */
export const onAuthStateChange = (callback) => {
  return supabase.auth.onAuthStateChange((event, session) => {
    callback(event, session);
  });
};
