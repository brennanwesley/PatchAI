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

// Track state resets and request deduplication
let stateResetCount = 0;
const isProduction = process.env.NODE_ENV === 'production';

// Optimized logger with log levels
const logger = {
  debug: (...args) => !isProduction && console.debug(...args),
  info: (...args) => !isProduction && console.info(...args),
  warn: (...args) => console.warn(...args),
  error: (...args) => console.error(...args),
  group: (...args) => !isProduction && console.group(...args),
  groupEnd: (...args) => !isProduction && console.groupEnd(...args)
};

if (!isProduction) {
  logger.info('Chat store initialized in development mode');
}

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

  if (!isProduction) {
    logger.group(`Action: ${action.type} [${actionId}]`);
    logger.debug('Action Payload:', action.payload);
    logger.debug('Previous State:', {
      messagesCount: state.messages.length,
      messages: state.messages.map(m => ({
        id: m.id,
        role: m.role,
        preview: m.content?.substring(0, 30) + (m.content?.length > 30 ? '...' : '')
      })),
      isLoading: state.isLoading,
      isTyping: state.isTyping
    });
  }

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
    
    case 'BATCH_UPDATE':
      // Process multiple actions in a single state update
      if (!isProduction) {
        logger.debug(`Processing batch update with ${action.payload.length} actions`);
      }
      return action.payload.reduce((currentState, action) => {
        return chatReducer(currentState, action);
      }, state);
    
    default:
      logger.warn(`Unknown action type: ${action.type}`);
      newState = state;
    }

    if (!isProduction) {
      logger.debug('New State:', {
        messagesCount: newState.messages.length,
        messages: newState.messages.map(m => ({
          id: m.id,
          role: m.role,
          preview: m.content?.substring(0, 30) + (m.content?.length > 30 ? '...' : '')
        })),
        isLoading: newState.isLoading,
        isTyping: newState.isTyping
      });
    }

    return newState;
  } catch (error) {
    logger.error('Reducer Error:', {
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
    logger.groupEnd();
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
    
    if (!isProduction) {
      logger.group(`${name} Mount #${mountCount.current} [${mountId.current}]`);
      logger.debug('Mount Time:', new Date().toISOString());
      logger.debug('Mount ID:', mountId.current);
      logger.groupEnd();
    }
    
    return () => {
      isMounted.current = false;
      if (!isProduction) {
        const uptime = Date.now() - mountTime;
        logger.group(`${name} Unmount [${mountId.current}]`);
        logger.debug('Uptime:', `${(uptime / 1000).toFixed(2)}s`);
        logger.debug('Unmount Time:', new Date().toISOString());
        logger.groupEnd();
      }
    };
  }, [name]);
  
  return { mountCount, isMounted, mountId };
}

export function ChatProvider({ children }) {
  const { mountCount, isMounted, mountId } = useMountTracking('ChatProvider');
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const { user } = useAuth();
  
  if (!isProduction) {
    logger.debug(`ChatProvider Render #${mountCount.current} [${mountId.current}]`, {
      isMounted: isMounted.current,
      state: {
        messagesCount: state.messages.length,
        isLoading: state.isLoading,
        isTyping: state.isTyping,
        error: state.error ? 'Error present' : 'No error'
      },
      user: user ? 'Authenticated' : 'Not authenticated'
    });
  }

  // Track loading state to prevent duplicate requests
  const isLoadingRef = useRef(false);
  const lastLoadTimeRef = useRef(0);
  
  // SINGLE CHAT: Load messages for single chat session (OPTIMIZED)
  const loadMessages = useCallback(async () => {
    console.log('🚀 LOAD_DEBUG: loadMessages function called');
    const now = Date.now();
    const timeSinceLastLoad = now - lastLoadTimeRef.current;
    const COOLDOWN_PERIOD = 5000; // 5 seconds
    
    if (isLoadingRef.current) {
      console.log('⏸️ LOAD_DEBUG: Skipping - already loading');
      logger.debug('Skipping duplicate loadMessages call - already loading');
      return;
    }
    
    if (timeSinceLastLoad < COOLDOWN_PERIOD) {
      console.log(`⏸️ LOAD_DEBUG: Skipping - cooldown period (${timeSinceLastLoad}ms < ${COOLDOWN_PERIOD}ms)`);
      logger.debug(`Skipping loadMessages - cooldown period (${timeSinceLastLoad}ms < ${COOLDOWN_PERIOD}ms)`);
      return;
    }
    
    try {
      console.log('🔄 LOAD_DEBUG: Starting message load process');
      isLoadingRef.current = true;
      lastLoadTimeRef.current = now;
      
      logger.info('Loading messages for single chat session');
      dispatch({ type: 'SET_LOADING', payload: true });
      
      console.log('📡 LOAD_DEBUG: About to call ChatService.getSingleChatSession()');
      // Fetch single chat session from backend
      const chatSession = await ChatService.getSingleChatSession();
      console.log('📨 LOAD_DEBUG: ChatService.getSingleChatSession() returned:', chatSession);
      
      // Extract messages and title from single chat session
      const messages = chatSession?.messages || [];
      const title = chatSession?.title || 'Chat Session';
      
      logger.info(`Retrieved ${messages.length} messages from backend`);
      
      // Batch updates to prevent multiple renders
      dispatch({
        type: 'BATCH_UPDATE',
        payload: [
          { type: 'LOAD_MESSAGES', payload: messages },
          { type: 'SET_CHAT_TITLE', payload: title },
          { type: 'SET_LOADING', payload: false }
        ]
      });
      
    } catch (error) {
      logger.error('Failed to load messages:', error);
      // Batch error handling
      dispatch({
        type: 'BATCH_UPDATE',
        payload: [
          { type: 'SET_ERROR', payload: error.message },
          { type: 'SET_LOADING', payload: false }
        ]
      });
    } finally {
      isLoadingRef.current = false;
    }
  }, []); // Stable dependency array

  // SINGLE CHAT: Send message to single chat session
  const sendMessage = useCallback(async (content) => {
    if (!user) {
      logger.error('No user authenticated');
      return;
    }

    try {
      logger.info('Sending message to single chat session');
      
      // CRITICAL FIX: Use functional state update to get the most current state
      let currentConversationHistory = [];
      
      // Get current state using functional update pattern
      dispatch((currentState) => {
        currentConversationHistory = [...currentState.messages];
        if (!isProduction) {
          logger.debug(`Captured ${currentConversationHistory.length} messages from current state`);
        }
        return currentState; // No state change, just capturing
      });
      
      // Debug logging in development only
      if (!isProduction) {
        logger.debug(`Captured conversation history length: ${currentConversationHistory.length}`);
        logger.debug(`Original state.messages length: ${state.messages.length}`);
        
        // Detailed message analysis
        const userMsgs = currentConversationHistory.filter(m => m.role === 'user');
        const assistantMsgs = currentConversationHistory.filter(m => m.role === 'assistant');
        
        logger.debug(`Message breakdown - User: ${userMsgs.length}, Assistant: ${assistantMsgs.length}`);
        
        // Log each message for debugging
        currentConversationHistory.forEach((msg, i) => {
          const preview = msg.content?.substring(0, 50) + '...' || 'No content';
          logger.debug(`Message ${i+1} (${msg.role}): ${preview}`);
        });
        
        // Critical validation
        if (currentConversationHistory.length === 0) {
          logger.warn('No conversation history found - this may cause context loss');
        } else {
          logger.debug(`Context preservation active - sending ${currentConversationHistory.length} historical + 1 new = ${currentConversationHistory.length + 1} total messages`);
        }
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
      logger.info('Clearing messages from single chat session');
      await ChatService.clearMessages();
      dispatch({ type: 'CLEAR_MESSAGES' });
      logger.info('Messages cleared successfully');
    } catch (error) {
      logger.error('Failed to clear messages:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  }, []);

  // Track initial load to prevent duplicate loads
  const initialLoadRef = useRef(false);
  
  // Load messages when user is authenticated (OPTIMIZED)
  useEffect(() => {
    if (!isProduction) {
      logger.debug('useEffect triggered', {
        hasUser: !!user,
        messageCount: state.messages.length,
        isLoading: state.loading,
        initialLoad: initialLoadRef.current
      });
    }
    
    // 🔍 DEBUG: Log all conditions for message loading
    console.log('🔍 LOAD_DEBUG: Checking message load conditions:', {
      hasUser: !!user,
      messagesLength: state.messages.length,
      isLoading: state.loading,
      initialLoadDone: initialLoadRef.current,
      shouldLoad: user && state.messages.length === 0 && !state.loading && !initialLoadRef.current
    });
    
    // Only load messages if we have a user, no messages, not loading, and haven't loaded yet
    if (user && state.messages.length === 0 && !state.loading && !initialLoadRef.current) {
      initialLoadRef.current = true;
      console.log('✅ LOAD_DEBUG: Conditions met - calling loadMessages()');
      logger.info('Performing initial message load for authenticated user');
      loadMessages();
    } else if (!user) {
      // Clear messages when user logs out
      console.log('🔒 USER_LOGOUT: Clearing messages due to logout');
      dispatch({ type: 'CLEAR_MESSAGES' });
    } else if (state.loading) {
      console.log('⏳ LOADING_GUARD: Skipping loadMessages - already loading');
    } else if (initialLoadRef.current) {
      console.log('🔄 LOAD_DEBUG: Skipping loadMessages - initial load already done');
    } else if (state.messages.length > 0) {
      console.log('📝 LOAD_DEBUG: Skipping loadMessages - messages already exist:', state.messages.length);
    } else {
      console.log('❓ LOAD_DEBUG: Skipping loadMessages - unknown condition');
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
