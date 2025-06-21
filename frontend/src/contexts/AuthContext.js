import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
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
  
  const value = {
    user,
    loading,
    initialized,
    signIn,
    signOut,
  };

  return <AuthContext.Provider value={value}>{!loading && children}</AuthContext.Provider>;
};

export const useAuth = () => {
  return useContext(AuthContext);
};
