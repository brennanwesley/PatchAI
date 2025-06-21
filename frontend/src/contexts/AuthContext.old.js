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

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  return useContext(AuthContext);
};
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
