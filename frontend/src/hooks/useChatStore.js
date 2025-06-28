import { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { ChatService } from '../services/chatService';
import { useAuth } from '../contexts/AuthContext';

// Chat State Management
const ChatContext = createContext();

const initialState = {
  chats: [],
  activeChat: null,
  messages: [],
  isLoading: false,
  isTyping: false,
  error: null
};

function chatReducer(state, action) {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    case 'SET_TYPING':
      return { ...state, isTyping: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    
    case 'LOAD_CHATS':
      return { ...state, chats: action.payload || [], isLoading: false };
    
    case 'SET_ACTIVE_CHAT':
      return { ...state, activeChat: action.payload };
    
    case 'SET_MESSAGES':
      return { ...state, messages: action.payload };
    
    case 'ADD_MESSAGE':
      return { 
        ...state, 
        messages: [...state.messages, action.payload] 
      };
    
    case 'CREATE_CHAT':
      return {
        ...state,
        chats: [action.payload, ...(Array.isArray(state.chats) ? state.chats : [])],
        activeChat: action.payload,
        messages: []
      };
    
    case 'UPDATE_CHAT_TITLE':
      return {
        ...state,
        chats: state.chats.map(chat => 
          chat.id === action.payload.chatId 
            ? { ...chat, title: action.payload.title }
            : chat
        ),
        activeChat: state.activeChat?.id === action.payload.chatId 
          ? { ...state.activeChat, title: action.payload.title }
          : state.activeChat
      };
    
    case 'DELETE_CHAT':
      const updatedChats = state.chats.filter(chat => chat.id !== action.payload);
      const wasActiveChat = state.activeChat?.id === action.payload;
      return {
        ...state,
        chats: updatedChats,
        activeChat: wasActiveChat ? null : state.activeChat,
        messages: wasActiveChat ? [] : state.messages
      };
    
    case 'UPDATE_CHAT':
      return {
        ...state,
        chats: Array.isArray(state.chats) 
          ? state.chats.map(chat => chat.id === action.payload.id ? action.payload : chat)
          : [action.payload],
        activeChat: action.payload
      };
    
    default:
      return state;
  }
}

export function ChatProvider({ children }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const { user } = useAuth();

  // FIXED: Memoized loadChats to prevent infinite loops
  const loadChats = useCallback(async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const chats = await ChatService.getUserChatSessions();
      dispatch({ type: 'LOAD_CHATS', payload: chats });
    } catch (error) {
      console.error('Failed to load chats:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
      dispatch({ type: 'LOAD_CHATS', payload: [] });
    }
  }, []); // Empty dependency array - function doesn't depend on state

  // FIXED: Proper dependency array with memoized function
  useEffect(() => {
    if (user) {
      loadChats();
    }
  }, [user, loadChats]);

  const createNewChat = useCallback(async () => {
    try {
      // FIXED: Use UUID instead of Date.now() to prevent ID collisions
      const chatId = uuidv4();
      const newChat = {
        id: `temp-${chatId}`,
        title: 'New Chat',
        messages: [],
        createdAt: new Date().toISOString(),
        isNew: true
      };
      
      console.log('🆕 CREATE_NEW_CHAT: Generated unique chat ID:', newChat.id);
      dispatch({ type: 'CREATE_CHAT', payload: newChat });
      return newChat;
    } catch (error) {
      console.error('Failed to create new chat:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  }, []); // No dependencies needed

  const selectChat = useCallback(async (chat) => {
    try {
      dispatch({ type: 'SET_ACTIVE_CHAT', payload: chat });
      dispatch({ type: 'SET_LOADING', payload: true });
      
      if (chat.isNew) {
        dispatch({ type: 'SET_MESSAGES', payload: [] });
      } else {
        const messages = await ChatService.getChatMessages(chat.id);
        dispatch({ type: 'SET_MESSAGES', payload: messages || [] });
      }
      
      dispatch({ type: 'SET_LOADING', payload: false });
    } catch (error) {
      console.error('Failed to load chat messages:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []); // No dependencies needed

  // FIXED: Removed chats dependency to prevent circular dependency
  const sendMessage = useCallback(async (content, files = []) => {
    console.log('🚀 SENDMESSAGE: Starting with content:', content);
    
    if (!user) {
      console.error('❌ SENDMESSAGE: User not authenticated');
      throw new Error('User not authenticated');
    }

    // If no active chat exists, create one first
    if (!state.activeChat) {
      console.log('📝 SENDMESSAGE: No active chat found, creating new chat...');
      const newChat = await createNewChat();
      if (!newChat) {
        console.error('❌ SENDMESSAGE: Failed to create new chat');
        throw new Error('Failed to create new chat');
      }
    }

    // FIXED: Use UUID for message IDs to prevent collisions
    const messageId = uuidv4();
    const userMessage = {
      id: `user-${messageId}`,
      role: 'user',
      content,
      files,
      timestamp: new Date().toISOString()
    };

    console.log('✅ SENDMESSAGE: Created user message:', userMessage);

    // Add user message immediately (optimistic UI)
    dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
    console.log('✅ SENDMESSAGE: User message added to state');

    let chatId = state.activeChat?.id;
    let currentChat = state.activeChat;

    console.log('🔍 SENDMESSAGE: Current chat state:', { chatId, isNew: currentChat?.isNew });

    // If no active chat or it's a new chat, create it first
    if (!currentChat || currentChat.isNew) {
      console.log('📝 SENDMESSAGE: Creating new chat session...');
      const title = content.substring(0, 30) + (content.length > 30 ? '...' : '');
      const newChat = await ChatService.createChatSession(title, userMessage);
      chatId = newChat.id;
      currentChat = { ...newChat, isNew: false };
      
      dispatch({ type: 'UPDATE_CHAT', payload: currentChat });
      dispatch({ type: 'SET_ACTIVE_CHAT', payload: currentChat });
      console.log('✅ SENDMESSAGE: New chat created with ID:', chatId);
    } else {
      // Save to existing chat
      console.log('💾 SENDMESSAGE: Adding message to existing chat:', chatId);
      await ChatService.addMessageToSession(chatId, userMessage.role, userMessage.content);
    }

    // Ensure we have a valid chatId before proceeding
    if (!chatId) {
      console.error('❌ SENDMESSAGE: No valid chatId available');
      throw new Error('Failed to create or get chat session');
    }

    console.log('🔍 SENDMESSAGE: Final chatId for AI call:', chatId);

    // Show typing indicator
    dispatch({ type: 'SET_TYPING', payload: true });
    console.log('⏳ SENDMESSAGE: Typing indicator set to true');

    try {
      console.log('🤖 AI_FLOW: Starting AI response request...');
      
      // Get current messages for AI context
      const allMessages = [...state.messages, userMessage];
      const apiMessages = allMessages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      console.log('📤 AI_FLOW: Prepared API messages:', apiMessages);
      console.log('📤 AI_FLOW: Calling ChatService.sendPrompt with chatId:', chatId);

      // STEP 2: Call sendPrompt with correct parameters (messages + chatId)
      const aiResponse = await ChatService.sendPrompt(apiMessages, chatId);
      console.log('✅ AI_FLOW: AI response received:', aiResponse);

      // STEP 3: Proper state management - Create assistant message
      // FIXED: Use UUID for assistant message IDs
      const assistantMessageId = uuidv4();
      const assistantMessage = {
        id: `assistant-${assistantMessageId}`,
        role: 'assistant',
        content: aiResponse,
        timestamp: new Date().toISOString()
      };

      console.log('📝 AI_FLOW: Created assistant message:', assistantMessage);

      // Add AI response to state
      dispatch({ type: 'ADD_MESSAGE', payload: assistantMessage });
      dispatch({ type: 'SET_TYPING', payload: false });
      console.log('✅ AI_FLOW: Assistant message added to state, typing indicator cleared');

      // Save AI message to database
      console.log('💾 AI_FLOW: Saving AI response to database...');
      await ChatService.addMessageToSession(chatId, 'assistant', aiResponse);
      console.log('✅ AI_FLOW: AI response saved to database');

      // Update chat with last message
      const updatedChat = {
        ...currentChat,
        lastMessage: assistantMessage.content,
        updatedAt: new Date().toISOString()
      };
      dispatch({ type: 'UPDATE_CHAT', payload: updatedChat });
      console.log('✅ AI_FLOW: Chat updated with last message');
      
      console.log('🎉 AI_FLOW: Complete flow finished successfully!');

    } catch (error) {
      console.error('❌ AI_FLOW: Failed to get AI response:', error);
      console.error('❌ AI_FLOW: Error details:', {
        message: error.message,
        status: error.status,
        isAuthError: error.isAuthError,
        isPaywallError: error.isPaywallError,
        stack: error.stack
      });
      
      dispatch({ type: 'SET_ERROR', payload: error.message });
      dispatch({ type: 'SET_TYPING', payload: false });
      
      // Show user-friendly error message
      let errorContent = 'Sorry, I encountered an error processing your request. Please try again.';
      
      // Special handling for paywall errors
      if (error.isPaywallError || error.status === 402) {
        errorContent = '💳 Subscription required to continue chatting. Please upgrade to the Standard Plan to keep using PatchAI.';
      }
      
      // FIXED: Use UUID for error message IDs
      const errorMessageId = uuidv4();
      const errorMessage = {
        id: `error-${errorMessageId}`,
        role: 'assistant',
        content: errorContent,
        timestamp: new Date().toISOString(),
        isError: true,
        isPaywallError: error.isPaywallError || error.status === 402
      };
      dispatch({ type: 'ADD_MESSAGE', payload: errorMessage });
      console.log('📝 AI_FLOW: Error message added to chat');
    }
  }, [state.activeChat]); // Only depend on activeChat

  // Update chat title (frontend only)
  const updateChatTitle = useCallback((chatId, newTitle) => {
    dispatch({ 
      type: 'UPDATE_CHAT_TITLE', 
      payload: { chatId, title: newTitle } 
    });
  }, []);

  // Delete chat (frontend only)
  const deleteChat = useCallback((chatId) => {
    dispatch({ type: 'DELETE_CHAT', payload: chatId });
  }, []);

  const value = {
    ...state,
    loadChats,
    createNewChat,
    selectChat,
    sendMessage,
    updateChatTitle,
    deleteChat
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChatStore() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatStore must be used within a ChatProvider');
  }
  return context;
}
