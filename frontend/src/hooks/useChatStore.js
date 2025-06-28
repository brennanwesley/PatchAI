import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ChatService } from '../services/ChatService';
import { v4 as uuidv4 } from 'uuid';

// Create context
const ChatContext = createContext();

// Initial state for single chat architecture
const initialState = {
  messages: [],
  isLoading: false,
  isTyping: false,
  error: null,
  chatTitle: 'Chat Session'
};

// Reducer for single chat architecture
function chatReducer(state, action) {
  switch (action.type) {
    case 'LOAD_MESSAGES':
      console.log('📥 LOAD_MESSAGES: Loading', action.payload?.length || 0, 'messages');
      return {
        ...state,
        messages: Array.isArray(action.payload) ? action.payload : [],
        isLoading: false,
        error: null
      };
    
    case 'ADD_MESSAGE':
      console.log('➕ ADD_MESSAGE: Adding message:', action.payload.role);
      return {
        ...state,
        messages: [...state.messages, action.payload]
      };
    
    case 'CLEAR_MESSAGES':
      console.log('🗑️ CLEAR_MESSAGES: Clearing all messages');
      return {
        ...state,
        messages: []
      };
    
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload
      };
    
    case 'SET_TYPING':
      return {
        ...state,
        isTyping: action.payload
      };
    
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
        isTyping: false
      };
    
    case 'SET_CHAT_TITLE':
      return {
        ...state,
        chatTitle: action.payload
      };
    
    // REMOVED: All multi-chat cases (CREATE_CHAT, SWITCH_CHAT, UPDATE_CHAT_TITLE, DELETE_CHAT, UPDATE_CHAT)
    // Single chat architecture doesn't need these operations
    
    default:
      return state;
  }
}

export function ChatProvider({ children }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const { user } = useAuth();

  // SINGLE CHAT: Load messages for user's single chat session
  const loadMessages = useCallback(async () => {
    if (!user) {
      console.log('🔍 LOAD_MESSAGES: No user authenticated, skipping message loading');
      return;
    }

    try {
      console.log('🔄 LOAD_MESSAGES: Loading messages for single chat session');
      dispatch({ type: 'SET_LOADING', payload: true });
      
      // Fetch single chat session from backend
      const chatSession = await ChatService.getSingleChatSession();
      console.log('🔍 LOAD_MESSAGES: Backend response:', chatSession);
      
      // Extract messages and title from single chat session
      const messages = chatSession?.messages || [];
      const title = chatSession?.title || 'Chat Session';
      
      console.log('✅ LOAD_MESSAGES: Retrieved', messages.length, 'messages from backend');
      
      dispatch({ type: 'LOAD_MESSAGES', payload: messages });
      dispatch({ type: 'SET_CHAT_TITLE', payload: title });
      
    } catch (error) {
      console.error('❌ LOAD_MESSAGES: Failed to load messages:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  }, [user]);

  // SINGLE CHAT: Send message to single chat session
  const sendMessage = useCallback(async (content) => {
    if (!user) {
      console.error('❌ SEND_MESSAGE: No user authenticated');
      return;
    }

    try {
      console.log('📤 SEND_MESSAGE: Sending message to single chat session');
      
      // Add user message immediately (optimistic UI)
      const userMessage = {
        id: uuidv4(),
        content,
        role: 'user',
        timestamp: new Date().toISOString()
      };
      
      dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
      dispatch({ type: 'SET_TYPING', payload: true });
      
      // Send to backend and get AI response
      const response = await ChatService.sendMessage(content);
      
      // Add AI response
      const aiMessage = {
        id: uuidv4(),
        content: response.message,
        role: 'assistant',
        timestamp: new Date().toISOString()
      };
      
      dispatch({ type: 'ADD_MESSAGE', payload: aiMessage });
      dispatch({ type: 'SET_TYPING', payload: false });
      
      console.log('✅ SEND_MESSAGE: Message sent and response received');
      
    } catch (error) {
      console.error('❌ SEND_MESSAGE: Failed to send message:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
      dispatch({ type: 'SET_TYPING', payload: false });
    }
  }, [user]);

  // SINGLE CHAT: Clear all messages from single chat session
  const clearMessages = useCallback(async () => {
    try {
      console.log('🗑️ CLEAR_MESSAGES: Clearing messages from single chat session');
      await ChatService.clearMessages();
      dispatch({ type: 'CLEAR_MESSAGES' });
      console.log('✅ CLEAR_MESSAGES: Messages cleared successfully');
    } catch (error) {
      console.error('❌ CLEAR_MESSAGES: Failed to clear messages:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  }, []);

  // Load messages when user changes
  useEffect(() => {
    if (user) {
      loadMessages();
    } else {
      // Clear messages when user logs out
      dispatch({ type: 'CLEAR_MESSAGES' });
    }
  }, [user, loadMessages]);

  // Context value for single chat architecture
  const value = {
    // State
    messages: state.messages,
    isLoading: state.isLoading,
    isTyping: state.isTyping,
    error: state.error,
    chatTitle: state.chatTitle,
    
    // Actions
    sendMessage,
    loadMessages,
    clearMessages
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
}

// Custom hook to use chat context
export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
