import { createContext, useContext, useReducer, useEffect } from 'react';
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
      return { ...state, chats: action.payload, isLoading: false };
    
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
        chats: [action.payload, ...state.chats],
        activeChat: action.payload,
        messages: []
      };
    
    case 'UPDATE_CHAT':
      return {
        ...state,
        chats: state.chats.map(chat => 
          chat.id === action.payload.id ? action.payload : chat
        )
      };
    
    default:
      return state;
  }
}

export function ChatProvider({ children }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const { user } = useAuth();

  // Load chats on mount
  useEffect(() => {
    if (user) {
      loadChats();
    }
  }, [user]);

  const loadChats = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const chats = await ChatService.getUserChatSessions();
      dispatch({ type: 'LOAD_CHATS', payload: chats || [] });
    } catch (error) {
      console.error('Failed to load chats:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
      dispatch({ type: 'LOAD_CHATS', payload: [] });
    }
  };

  const createNewChat = async () => {
    try {
      const newChat = {
        id: `temp-${Date.now()}`,
        title: 'New Chat',
        messages: [],
        createdAt: new Date().toISOString(),
        isNew: true
      };
      
      dispatch({ type: 'CREATE_CHAT', payload: newChat });
      return newChat;
    } catch (error) {
      console.error('Failed to create new chat:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  };

  const selectChat = async (chat) => {
    try {
      dispatch({ type: 'SET_ACTIVE_CHAT', payload: chat });
      
      if (chat.messages && chat.messages.length > 0) {
        dispatch({ type: 'SET_MESSAGES', payload: chat.messages });
      } else {
        // Load messages from database
        const chatData = await ChatService.getChatSession(chat.id);
        const messages = chatData?.messages || [];
        dispatch({ type: 'SET_MESSAGES', payload: messages });
      }
    } catch (error) {
      console.error('Failed to select chat:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  };

  const sendMessage = async (content, files = []) => {
    try {
      const userMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content,
        files,
        timestamp: new Date().toISOString()
      };

      // Add user message immediately (optimistic UI)
      dispatch({ type: 'ADD_MESSAGE', payload: userMessage });

      let chatId = state.activeChat?.id;

      // Create chat if it's new
      if (state.activeChat?.isNew) {
        const title = content.substring(0, 30) + (content.length > 30 ? '...' : '');
        const newChat = await ChatService.createChatSession(title, userMessage);
        chatId = newChat.id;
        
        dispatch({ type: 'UPDATE_CHAT', payload: { ...newChat, isNew: false } });
        dispatch({ type: 'SET_ACTIVE_CHAT', payload: { ...newChat, isNew: false } });
      } else {
        // Save to existing chat
        await ChatService.addMessageToSession(chatId, userMessage.role, userMessage.content);
      }

      // Show typing indicator
      dispatch({ type: 'SET_TYPING', payload: true });

      // Get AI response
      const allMessages = [...state.messages, userMessage];
      const apiMessages = allMessages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      const response = await ChatService.sendPrompt(apiMessages, chatId);
      
      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response || response.content || 'No response received',
        timestamp: new Date().toISOString()
      };

      // Add AI response
      dispatch({ type: 'ADD_MESSAGE', payload: assistantMessage });
      dispatch({ type: 'SET_TYPING', payload: false });

      // Save AI response to database
      await ChatService.addMessageToSession(chatId, assistantMessage.role, assistantMessage.content);

      // Update chat in sidebar
      const updatedChat = {
        ...state.activeChat,
        lastMessage: assistantMessage.content,
        updatedAt: new Date().toISOString(),
        messages: [...state.messages, userMessage, assistantMessage]
      };
      dispatch({ type: 'UPDATE_CHAT', payload: updatedChat });

    } catch (error) {
      console.error('Failed to send message:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
      dispatch({ type: 'SET_TYPING', payload: false });
    }
  };

  const value = {
    ...state,
    loadChats,
    createNewChat,
    selectChat,
    sendMessage
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
