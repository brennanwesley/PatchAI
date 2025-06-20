import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { supabase } from '../supabaseClient';

const AuthContext = createContext({});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);
  const [sessionCleared, setSessionCleared] = useState(false);
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
    // Only clear sessions on the very first app load, not after successful login
    const initializeAuth = async () => {
      try {
        if (!sessionCleared) {
          // FORCE LOGOUT ON INITIAL APP LOAD ONLY - FOR TESTING PURPOSES
          console.log('Initial app load - clearing any existing sessions');
          
          // Clear any existing session
          await supabase.auth.signOut();
          
          // Clear localStorage items that might contain session data
          const keysToRemove = [];
          for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && (key.startsWith('supabase') || key.startsWith('sb-'))) {
              keysToRemove.push(key);
            }
          }
          keysToRemove.forEach(key => localStorage.removeItem(key));
          
          // Clear sessionStorage as well
          const sessionKeysToRemove = [];
          for (let i = 0; i < sessionStorage.length; i++) {
            const key = sessionStorage.key(i);
            if (key && (key.startsWith('supabase') || key.startsWith('sb-'))) {
              sessionKeysToRemove.push(key);
            }
          }
          sessionKeysToRemove.forEach(key => sessionStorage.removeItem(key));
          
          console.log('Initial session clearing completed');
          setSessionCleared(true);
          
          // Set user to null and finish loading
          setUser(null);
          setInitialized(true);
          setLoading(false);
          
          // Ensure we're on the login page
          if (location.pathname !== '/') {
            navigate('/');
          }
        } else {
          // Session already cleared, just check for existing session normally
          const { data: { session } } = await supabase.auth.getSession();
          handleAuthChange('INITIAL_SESSION', session);
        }
        
      } catch (error) {
        console.error('Error during auth initialization:', error);
        setUser(null);
        setLoading(false);
      }
    };

    // Execute auth initialization
    initializeAuth();

    // Set up auth state change listener for future login events
    const { data: { subscription } } = supabase.auth.onAuthStateChange(handleAuthChange);

    return () => {
      if (subscription) subscription.unsubscribe();
    };
  }, [handleAuthChange, navigate, location.pathname, sessionCleared]);

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
    try {
      // Sign out from Supabase
      await supabase.auth.signOut();
      
      // Clear all Supabase-related localStorage items
      const keysToRemove = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && (key.startsWith('supabase') || key.startsWith('sb-'))) {
          keysToRemove.push(key);
        }
      }
      keysToRemove.forEach(key => localStorage.removeItem(key));
      
      // Clear all Supabase-related sessionStorage items
      const sessionKeysToRemove = [];
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (key && (key.startsWith('supabase') || key.startsWith('sb-'))) {
          sessionKeysToRemove.push(key);
        }
      }
      sessionKeysToRemove.forEach(key => sessionStorage.removeItem(key));
      
      // Clear chat data as well for fresh testing
      localStorage.removeItem('patchai-chats');
      localStorage.removeItem('patchai-active-chat');
      
      console.log('Complete logout - all session and app data cleared');
      
      // Set user to null
      setUser(null);
      
    } catch (error) {
      console.error('Error during logout:', error);
      // Even if there's an error, clear the user state
      setUser(null);
    }
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
