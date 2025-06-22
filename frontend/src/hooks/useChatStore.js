import { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
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
        chats: [action.payload, ...state.chats],
        activeChat: action.payload,
        messages: []
      };
    
    case 'UPDATE_CHAT':
      return {
        ...state,
        chats: state.chats.map(chat => 
          chat.id === action.payload.id ? action.payload : chat
        ),
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

      // FIXED: Use functional state update to access current messages without dependency
      dispatch(currentState => {
        const allMessages = [...currentState.messages];
        const apiMessages = allMessages.map(msg => ({
          role: msg.role,
          content: msg.content
        }));

        // Get AI response (async without await to prevent blocking)
        ChatService.sendPrompt(apiMessages)
          .then(response => {
            const assistantMessage = {
              id: `assistant-${Date.now()}`,
              role: 'assistant',
              content: response,
              timestamp: new Date().toISOString()
            };

            // Add AI response
            dispatch({ type: 'ADD_MESSAGE', payload: assistantMessage });
            dispatch({ type: 'SET_TYPING', payload: false });

            // Save AI message to database
            if (!state.activeChat?.isNew) {
              ChatService.addMessageToSession(chatId, 'assistant', response);
            }

            // Update chat with last message
            const updatedChat = {
              ...state.activeChat,
              lastMessage: assistantMessage.content,
              updatedAt: new Date().toISOString()
            };
            dispatch({ type: 'UPDATE_CHAT', payload: updatedChat });
          })
          .catch(error => {
            console.error('Failed to get AI response:', error);
            dispatch({ type: 'SET_ERROR', payload: error.message });
            dispatch({ type: 'SET_TYPING', payload: false });
          });

        return currentState; // Return unchanged state
      });

    } catch (error) {
      console.error('Failed to send message:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
      dispatch({ type: 'SET_TYPING', payload: false });
    }
  }, [state.activeChat]); // Only depend on activeChat

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
