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
    if (currentUser && !location.pathname.startsWith('/chat')) {
      navigate('/chat');
    } else if (!currentUser && location.pathname !== '/') {
      navigate('/');
    }
    
    if (!initialized) {
      setInitialized(true);
      setLoading(false);
    }
  }, [navigate, location.pathname, initialized]);

  useEffect(() => {
    // Check for existing session first
    const checkSession = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        handleAuthChange('INITIAL_SESSION', session);
      } catch (error) {
        console.error('Error checking session:', error);
        setLoading(false);
      }
    };

    checkSession();

    // Set up auth state change listener
    const { data: { subscription } } = supabase.auth.onAuthStateChange(handleAuthChange);

    return () => {
      if (subscription) subscription.unsubscribe();
    };
  }, [handleAuthChange]);

  const login = async (email, password) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) throw error;
  };

  const signUp = async (email, password) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
    });
    if (error) throw error;
  };

  const logout = async () => {
    await supabase.auth.signOut();
  };

  const value = {
    user,
    loading,
    login,
    signUp,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
};
