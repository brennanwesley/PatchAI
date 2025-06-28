import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ChatService } from '../services/chatService';
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

// DEBUG: Track state resets
let stateResetCount = 0;
console.log('🏗️ CHAT_STORE_DEBUG: useChatStore.js loaded, initialState created');

// Reducer for single chat architecture
function chatReducer(state, action) {
  console.log(`🔄 REDUCER_DEBUG: Action '${action.type}' called with current state.messages.length: ${state.messages.length}`);
  
  switch (action.type) {
    case 'LOAD_MESSAGES':
      console.log('📥 LOAD_MESSAGES: Loading', action.payload?.length || 0, 'messages');
      console.log('📥 LOAD_MESSAGES_DEBUG: Previous state.messages.length:', state.messages.length);
      console.log('📥 LOAD_MESSAGES_DEBUG: New payload length:', action.payload?.length || 0);
      const newState = {
        ...state,
        messages: Array.isArray(action.payload) ? action.payload : [],
        isLoading: false,
        error: null
      };
      console.log('📥 LOAD_MESSAGES_DEBUG: Returning state with messages.length:', newState.messages.length);
      return newState;
    
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
  console.log('🏗️ PROVIDER_DEBUG: ChatProvider component mounting/re-mounting');
  stateResetCount++;
  console.log(`🏗️ PROVIDER_DEBUG: This is mount #${stateResetCount}`);
  
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const { user } = useAuth();
  
  console.log('🏗️ PROVIDER_DEBUG: useReducer initialized with state.messages.length:', state.messages.length);

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
      console.log('📝 LOAD_MESSAGES: Message details:', messages.map(m => ({ role: m.role, content: m.content?.substring(0, 50) + '...' })));
      
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
      
      // CRITICAL FIX: Use functional state update to get the most current state
      // This ensures we capture the actual current state, not a stale closure
      let currentConversationHistory = [];
      
      // Get current state using functional update pattern
      dispatch((currentState) => {
        currentConversationHistory = [...currentState.messages];
        console.log(`🔍 FUNCTIONAL_STATE_DEBUG: Captured ${currentConversationHistory.length} messages from current state`);
        return currentState; // No state change, just capturing
      });
      
      // COMPREHENSIVE STATE DEBUGGING
      console.log(`🔍 STATE_DEBUG: Captured conversation history length: ${currentConversationHistory.length}`);
      console.log(`🔍 STATE_DEBUG: Original state.messages length: ${state.messages.length}`);
      
      // Detailed message analysis
      const userMsgs = currentConversationHistory.filter(m => m.role === 'user');
      const assistantMsgs = currentConversationHistory.filter(m => m.role === 'assistant');
      console.log(`📊 STATE_DEBUG: Message breakdown - User: ${userMsgs.length}, Assistant: ${assistantMsgs.length}`);
      
      // Log each message for debugging
      currentConversationHistory.forEach((msg, i) => {
        const preview = msg.content?.substring(0, 50) + '...' || 'No content';
        console.log(`📄 STATE_DEBUG: Message ${i+1} (${msg.role}): ${preview}`);
      });
      
      // Critical validation
      if (currentConversationHistory.length === 0) {
        console.error(`❌ STATE_DEBUG: CRITICAL - No conversation history found! This will cause context loss.`);
        console.error(`❌ STATE_DEBUG: This indicates a state management issue that needs immediate attention.`);
      } else {
        console.log(`✅ STATE_DEBUG: Context preservation ACTIVE - sending ${currentConversationHistory.length} historical + 1 new = ${currentConversationHistory.length + 1} total messages`);
      }
      
      // Add user message immediately (optimistic UI)
      const userMessage = {
        id: uuidv4(),
        content,
        role: 'user',
        timestamp: new Date().toISOString()
      };
      
      dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
      dispatch({ type: 'SET_TYPING', payload: true });
      
      // Send to backend with conversation history (service will add new user message)
      const response = await ChatService.sendMessage(content, currentConversationHistory);
      
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
  }, [user, state.messages]);

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

  // Load messages ONLY on initial user authentication (not on every state change)
  useEffect(() => {
    console.log('🔄 USEEFFECT_DEBUG: useEffect triggered');
    console.log('🔄 USEEFFECT_DEBUG: user exists:', !!user);
    console.log('🔄 USEEFFECT_DEBUG: current state.messages.length:', state.messages.length);
    
    if (user) {
      console.log('🔄 INITIAL_LOAD: Loading messages for newly authenticated user');
      loadMessages();
    } else {
      // Clear messages when user logs out
      console.log('🔒 USER_LOGOUT: Clearing messages due to logout');
      dispatch({ type: 'CLEAR_MESSAGES' });
    }
  }, [user]); // ❌ REMOVED loadMessages dependency to prevent state overwrites

  // SINGLE CHAT: Update chat title
  const updateChatTitle = useCallback(async (chatId, newTitle) => {
    try {
      console.log('📝 UPDATE_CHAT_TITLE: Updating single chat title to:', newTitle);
      dispatch({ type: 'SET_CHAT_TITLE', payload: newTitle });
      console.log('✅ UPDATE_CHAT_TITLE: Title updated successfully');
    } catch (error) {
      console.error('❌ UPDATE_CHAT_TITLE: Failed to update title:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  }, []);

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
    clearMessages,
    updateChatTitle
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

// BACKWARD COMPATIBILITY: Export useChatStore for existing components
export function useChatStore() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatStore must be used within a ChatProvider');
  }
  
  // Get last message timestamp for sidebar display
  const getLastMessageTime = () => {
    if (context.messages.length === 0) return null;
    const lastMessage = context.messages[context.messages.length - 1];
    return lastMessage.timestamp || new Date().toISOString();
  };

  // Create single chat object with proper timestamp
  const singleChatObject = {
    id: 'single-chat',
    title: context.chatTitle,
    messages: context.messages,
    createdAt: getLastMessageTime(),
    lastMessage: context.messages.length > 0 ? context.messages[context.messages.length - 1].content?.substring(0, 50) + '...' : null
  };

  // Map single chat API to multi-chat API for backward compatibility
  return {
    // Single chat state mapped to multi-chat expectations
    chats: context.messages.length > 0 || context.chatTitle !== 'Chat Session' ? [singleChatObject] : [],
    activeChat: context.messages.length > 0 || context.chatTitle !== 'Chat Session' ? singleChatObject : null,
    messages: context.messages,
    isLoading: context.isLoading,
    isTyping: context.isTyping,
    error: context.error,
    
    // Single chat actions mapped to multi-chat API
    sendMessage: context.sendMessage,
    loadMessages: context.loadMessages,
    clearMessages: context.clearMessages,
    
    // FIXED: Properly implement sidebar functions for single chat
    createNewChat: () => {
      console.log('🆕 CREATE_NEW_CHAT: Clearing messages to start fresh (single chat mode)');
      return context.clearMessages();
    },
    selectChat: () => {
      console.log('🔄 SELECT_CHAT: Single chat already selected');
      return Promise.resolve();
    },
    updateChatTitle: (chatId, newTitle) => {
      console.log('📝 UPDATE_CHAT_TITLE: Updating single chat title via compatibility layer');
      return context.updateChatTitle(chatId, newTitle);
    },
    deleteChat: () => {
      console.log('🗑️ DELETE_CHAT: Clearing messages to start over (single chat mode)');
      return context.clearMessages();
    },
    loadChats: () => {
      console.log('📂 LOAD_CHATS: Loading single chat session');
      return context.loadMessages();
    }
  };
}
