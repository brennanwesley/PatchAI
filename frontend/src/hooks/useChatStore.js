import React, { createContext, useContext, useReducer, useCallback, useEffect, useMemo, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ChatService } from '../services/chatService';
import { v4 as uuidv4 } from 'uuid';

// Create context
const ChatContext = createContext();

// Helper function to generate debug info
const createDebugInfo = (type, data = {}) => ({
  _debug: {
    type,
    timestamp: new Date().toISOString(),
    timestampMs: Date.now(),
    ...data
  }
});

// Initial state for single chat architecture
const initialState = {
  messages: [],
  isLoading: false,
  isTyping: false,
  error: null,
  chatTitle: 'Chat Session',
  _debug: createDebugInfo('INITIAL_STATE')
};

// DEBUG: Track state resets
let stateResetCount = 0;
console.log('🏗️ CHAT_STORE_DEBUG: useChatStore.js loaded, initialState created');

// Enhanced reducer with detailed logging
function chatReducer(state, action) {
  const actionId = Math.random().toString(36).substring(2, 9);
  const actionDebug = {
    actionId,
    type: action.type,
    payload: action.payload,
    timestamp: Date.now(),
    prevState: {
      messagesCount: state.messages.length,
      isLoading: state.isLoading,
      isTyping: state.isTyping
    }
  };

  console.group(`🎬 Action: ${action.type} [${actionId}]`);
  console.log('📦 Action Payload:', action.payload);
  console.log('📊 Previous State:', {
    messagesCount: state.messages.length,
    messages: state.messages.map(m => ({
      id: m.id,
      role: m.role,
      preview: m.content?.substring(0, 30) + (m.content?.length > 30 ? '...' : '')
    })),
    isLoading: state.isLoading,
    isTyping: state.isTyping
  });

  let newState;
  try {
    switch (action.type) {
    case 'LOAD_MESSAGES': {
      const payload = Array.isArray(action.payload) ? action.payload : [];
      console.log(`📥 Loading ${payload.length} messages`);
      
      newState = {
        ...state,
        messages: payload,
        isLoading: false,
        error: null,
        _debug: createDebugInfo('STATE_UPDATE', {
          action: 'LOAD_MESSAGES',
          messageCount: payload.length,
          actionId
        })
      };
      
      console.log('📥 Loaded Messages:', {
        count: newState.messages.length,
        messages: newState.messages.map(m => ({
          id: m.id,
          role: m.role,
          preview: m.content?.substring(0, 50) + (m.content?.length > 50 ? '...' : '')
        }))
      });
      break;
    }
    
    case 'ADD_MESSAGE': {
      const message = {
        ...action.payload,
        _debug: createDebugInfo('MESSAGE_ADDED', { actionId })
      };
      
      console.log(`➕ Adding ${message.role} message:`, {
        id: message.id,
        content: message.content?.substring(0, 50) + (message.content?.length > 50 ? '...' : ''),
        timestamp: message.timestamp || new Date().toISOString()
      });
      
      newState = {
        ...state,
        messages: [...state.messages, message],
        _debug: createDebugInfo('STATE_UPDATE', {
          action: 'ADD_MESSAGE',
          messageId: message.id,
          role: message.role,
          actionId
        })
      };
      break;
    }
    
    case 'CLEAR_MESSAGES':
      console.log('🗑️ Clearing all messages');
      newState = {
        ...state,
        messages: [],
        _debug: createDebugInfo('STATE_UPDATE', {
          action: 'CLEAR_MESSAGES',
          actionId
        })
      };
      break;
    
    case 'SET_LOADING':
      console.log(`⏳ Setting loading: ${action.payload}`);
      newState = {
        ...state,
        isLoading: action.payload,
        _debug: createDebugInfo('STATE_UPDATE', {
          action: 'SET_LOADING',
          loading: action.payload,
          actionId
        })
      };
      break;
    
    case 'SET_TYPING':
      console.log(`⌨️ Setting typing: ${action.payload}`);
      newState = {
        ...state,
        isTyping: action.payload,
        _debug: createDebugInfo('STATE_UPDATE', {
          action: 'SET_TYPING',
          isTyping: action.payload,
          actionId
        })
      };
      break;
    
    case 'SET_ERROR':
      console.error('❌ Error:', action.payload);
      newState = {
        ...state,
        error: action.payload,
        isLoading: false,
        isTyping: false,
        _debug: createDebugInfo('STATE_UPDATE', {
          action: 'SET_ERROR',
          error: action.payload?.message || String(action.payload),
          actionId
        })
      };
      break;
    
    case 'SET_CHAT_TITLE':
      console.log(`🏷️ Setting chat title: ${action.payload}`);
      newState = {
        ...state,
        chatTitle: action.payload,
        _debug: createDebugInfo('STATE_UPDATE', {
          action: 'SET_CHAT_TITLE',
          title: action.payload,
          actionId
        })
      };
      break;
    
    // REMOVED: All multi-chat cases (CREATE_CHAT, SWITCH_CHAT, UPDATE_CHAT_TITLE, DELETE_CHAT, UPDATE_CHAT)
    // Single chat architecture doesn't need these operations
    
    default:
      console.warn(`⚠️ Unknown action type: ${action.type}`);
      newState = state;
    }

    console.log('🆕 New State:', {
      messagesCount: newState.messages.length,
      messages: newState.messages.map(m => ({
        id: m.id,
        role: m.role,
        preview: m.content?.substring(0, 30) + (m.content?.length > 30 ? '...' : '')
      })),
      isLoading: newState.isLoading,
      isTyping: newState.isTyping,
      _debug: newState._debug
    });

    return newState;
  } catch (error) {
    console.error('❌ Reducer Error:', {
      action,
      error: error.message,
      stack: error.stack,
      state: {
        messagesCount: state.messages.length,
        isLoading: state.isLoading,
        isTyping: state.isTyping
      }
    });
    return state;
  } finally {
    console.groupEnd();
  }
}

function useMountTracking(name) {
  const mountCount = useRef(0);
  const isMounted = useRef(false);
  const mountId = useRef(Math.random().toString(36).substring(2, 8));
  
  useEffect(() => {
    mountCount.current++;
    isMounted.current = true;
    const mountTime = Date.now();
    
    console.group(`🏗️ ${name} Mount #${mountCount.current} [${mountId.current}]`);
    console.log('Mount Time:', new Date().toISOString());
    console.log('Mount ID:', mountId.current);
    console.trace('Mount Trace');
    console.groupEnd();
    
    return () => {
      isMounted.current = false;
      const uptime = Date.now() - mountTime;
      console.group(`♻️ ${name} Unmount [${mountId.current}]`);
      console.log('Uptime:', `${(uptime / 1000).toFixed(2)}s`);
      console.log('Unmount Time:', new Date().toISOString());
      console.trace('Unmount Trace');
      console.groupEnd();
    };
  }, [name]);
  
  return { mountCount, isMounted, mountId };
}

export function ChatProvider({ children }) {
  const { mountCount, isMounted, mountId } = useMountTracking('ChatProvider');
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const { user } = useAuth();
  
  console.log(`🏗️ ChatProvider Render #${mountCount.current} [${mountId.current}]`, {
    isMounted: isMounted.current,
    state: {
      messagesCount: state.messages.length,
      isLoading: state.isLoading,
      isTyping: state.isTyping,
      error: state.error ? 'Error present' : 'No error'
    },
    user: user ? 'Authenticated' : 'Not authenticated'
  });

  // SINGLE CHAT: Load messages for single chat session (STABLE)
  const loadMessages = useCallback(async () => {
    // LOADING GUARD: Prevent multiple simultaneous calls
    if (state.loading) {
      console.log('⏳ LOAD_MESSAGES_GUARD: Already loading, skipping duplicate call');
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
      dispatch({ type: 'SET_LOADING', payload: false }); // ✅ Reset loading state
      
    } catch (error) {
      console.error('❌ LOAD_MESSAGES: Failed to load messages:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
      dispatch({ type: 'SET_LOADING', payload: false }); // ✅ Reset loading state on error
    }
  }, []); // ✅ NO DEPENDENCIES - completely stable

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

  // Load messages ONLY ONCE when user is authenticated (STABLE - no infinite loop)
  useEffect(() => {
    console.log('🔄 USEEFFECT_DEBUG: useEffect triggered');
    console.log('🔄 USEEFFECT_DEBUG: user exists:', !!user);
    console.log('🔄 USEEFFECT_DEBUG: current state.messages.length:', state.messages.length);
    console.log('🔄 USEEFFECT_DEBUG: current state.loading:', state.loading);
    
    if (user && state.messages.length === 0 && !state.loading) {
      console.log('🔄 INITIAL_LOAD: Loading messages for newly authenticated user (ONCE)');
      loadMessages();
    } else if (!user) {
      // Clear messages when user logs out
      console.log('🔒 USER_LOGOUT: Clearing messages due to logout');
      dispatch({ type: 'CLEAR_MESSAGES' });
    } else if (state.loading) {
      console.log('⏳ LOADING_GUARD: Skipping loadMessages - already loading');
    }
  }, [user]); // ✅ FIXED - Remove loadMessages dependency to break infinite loop

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

// BACKWARD COMPATIBILITY: Export useChatStore for existing components (MEMOIZED)
export function useChatStore() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatStore must be used within a ChatProvider');
  }
  
  // MEMOIZED: Get last message timestamp for sidebar display
  const getLastMessageTime = useMemo(() => {
    if (context.messages.length === 0) return null;
    const lastMessage = context.messages[context.messages.length - 1];
    return lastMessage.timestamp || new Date().toISOString();
  }, [context.messages]);

  // MEMOIZED: Create single chat object with proper timestamp
  const singleChatObject = useMemo(() => ({
    id: 'single-chat',
    title: context.chatTitle,
    messages: context.messages,
    createdAt: getLastMessageTime,
    lastMessage: context.messages.length > 0 ? context.messages[context.messages.length - 1].content?.substring(0, 50) + '...' : null
  }), [context.chatTitle, context.messages, getLastMessageTime]);

  // MEMOIZED: Map single chat API to multi-chat API for backward compatibility
  return useMemo(() => ({
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
      console.log('🗑️ DELETE_CHAT: Clearing messages for single chat');
      return context.clearMessages();
    },
    loadChats: () => {
      console.log('📂 LOAD_CHATS: Loading single chat session');
      return context.loadMessages();
    }
  }), [context.messages, context.chatTitle, context.isLoading, context.isTyping, context.error, singleChatObject, context.sendMessage, context.loadMessages, context.clearMessages, context.updateChatTitle]);
}
