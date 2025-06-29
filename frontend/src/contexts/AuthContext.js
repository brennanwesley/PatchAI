import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { supabase } from '../supabaseClient';

const AuthContext = createContext({});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Function to handle session changes
  const handleAuthChange = useCallback(async (event, session) => {
    const currentUser = session?.user ?? null;
    setUser(currentUser);
    
    // Only redirect if we're not already on the target page
    if (currentUser) {
      if (!location.pathname.startsWith('/chat')) {
        navigate('/chat');
      }
    } else if (location.pathname !== '/') {
      navigate('/');
    }
    
    if (!initialized) {
      setInitialized(true);
      setLoading(false);
    }
  }, [navigate, location.pathname, initialized]);

  useEffect(() => {
    // Initialize auth state
    const initializeAuth = async () => {
      try {
        // Check for existing session
        const { data: { session }, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error('Error getting session:', error);
          setLoading(false);
          setInitialized(true);
          return;
        }
        
        if (session) {
          // We have a valid session
          setUser(session.user);
          
          // Only redirect if we're not already on a chat page
          if (!location.pathname.startsWith('/chat')) {
            navigate('/chat');
          }
        } else {
          // No session, redirect to login if not already there
          if (location.pathname !== '/') {
            navigate('/');
          }
        }
        
        setLoading(false);
        setInitialized(true);
        
        // Set up auth state change listener
        const { data: { subscription } } = supabase.auth.onAuthStateChange(handleAuthChange);
        
        return () => {
          subscription?.unsubscribe();
        };
      } catch (error) {
        console.error('Error initializing auth:', error);
        setLoading(false);
        setInitialized(true);
      }
    };
    
    initializeAuth();
  }, [handleAuthChange, location.pathname, navigate]);
  
  // Sign in with email and password
  const signIn = async (email, password) => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      
      if (error) throw error;
      
      setUser(data.user);
      return { user: data.user, error: null };
    } catch (error) {
      console.error('Error signing in:', error);
      return { user: null, error };
    }
  };
  
  // Login function (alias for signIn with better error messages)
  const login = async (email, password) => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      
      if (error) {
        // Provide user-friendly error messages
        let userMessage = 'Login failed. Please try again.';
        
        if (error.message.includes('Invalid login credentials')) {
          userMessage = 'Invalid email or password. Please check your credentials and try again.';
        } else if (error.message.includes('Email not confirmed')) {
          userMessage = 'Please check your email and click the confirmation link before signing in.';
        } else if (error.message.includes('Too many requests')) {
          userMessage = 'Too many login attempts. Please wait a few minutes and try again.';
        } else if (error.message.includes('Invalid email')) {
          userMessage = 'Please enter a valid email address.';
        }
        
        throw new Error(userMessage);
      }
      
      setUser(data.user);
      return { user: data.user, error: null };
    } catch (error) {
      console.error('Error logging in:', error);
      throw error; // Re-throw to be caught by LandingPage
    }
  };
  
  // Sign up function with better error messages
  const signUp = async (email, password, referralCode = null, displayName = null) => {
    try {
      // If referral code is provided, use our backend referral signup endpoint
      if (referralCode) {
        const API_URL = process.env.REACT_APP_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'https://patchai-backend.onrender.com';
        const response = await fetch(`${API_URL}/referrals/signup`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email,
            password,
            referral_code: referralCode
          }),
        });

        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.detail || 'Signup with referral code failed');
        }

        // The backend handles the Supabase signup, so we need to sign in the user
        const { data: authData, error: signInError } = await supabase.auth.signInWithPassword({
          email,
          password,
        });

        if (signInError) {
          throw new Error('Account created but sign-in failed. Please try logging in.');
        }

        setUser(authData.user);
        return { user: authData.user, error: null };
      }

      // Standard signup without referral code
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      });
      
      if (error) {
        // Provide user-friendly error messages
        let userMessage = 'Sign up failed. Please try again.';
        
        if (error.message.includes('Password should be at least')) {
          userMessage = 'Password must be at least 6 characters long.';
        } else if (error.message.includes('Invalid email')) {
          userMessage = 'Please enter a valid email address.';
        } else if (error.message.includes('User already registered')) {
          userMessage = 'An account with this email already exists. Please try logging in instead.';
        } else if (error.message.includes('Signup is disabled')) {
          userMessage = 'Account creation is currently disabled. Please contact support.';
        }
        
        throw new Error(userMessage);
      }
      
      // If signup successful and display name provided, update the user profile
      if (data.user && displayName && displayName.trim()) {
        try {
          // Update the user profile with display name
          const { error: profileError } = await supabase
            .from('user_profiles')
            .update({ 
              display_name: displayName.trim(),
              updated_at: new Date().toISOString()
            })
            .eq('id', data.user.id);
          
          if (profileError) {
            console.error('Error updating display name:', profileError);
            // Don't throw error here - signup was successful, display name update is secondary
          } else {
            console.log('Display name updated successfully:', displayName.trim());
          }
        } catch (profileError) {
          console.error('Error updating user profile with display name:', profileError);
          // Don't throw error here - signup was successful
        }
      }
      
      setUser(data.user);
      return { user: data.user, error: null };
    } catch (error) {
      console.error('Error signing up:', error);
      throw error; // Re-throw to be caught by LandingPage
    }
  };
  
  // Sign out
  const signOut = async () => {
    try {
      await supabase.auth.signOut();
      setUser(null);
      return { error: null };
    } catch (error) {
      console.error('Error signing out:', error);
      return { error };
    }
  };
  
  // CRITICAL FIX: Memoize context value to prevent infinite ChatProvider re-mounting
  const value = useMemo(() => ({
    user,
    loading,
    initialized,
    signIn,
    signOut,
    login,
    signUp,
  }), [user, loading, initialized, signIn, signOut, login, signUp]);

  return <AuthContext.Provider value={value}>{!loading && children}</AuthContext.Provider>;
};

export const useAuth = () => {
  return useContext(AuthContext);
};
