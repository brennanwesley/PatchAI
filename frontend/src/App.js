import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import Sidebar from './components/Sidebar';
import ChatFeed from './components/ChatFeed';
import ChatInput from './components/ChatInput';
import { v4 as uuidv4 } from 'uuid';
import { FiMenu, FiLogOut } from 'react-icons/fi';
import { supabase } from './supabaseClient';
import { ChatService } from './services/chatService';
import './App.css';

// Constants
const MOBILE_BREAKPOINT = 768;

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, loading } = useAuth();
  
  // Handle sign out
  const handleSignOut = async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  // Layout state
  const [isMobile, setIsMobile] = useState(window.innerWidth < MOBILE_BREAKPOINT);
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const sidebarRef = useRef(null);
  
  // Chat state - now using Supabase instead of localStorage
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [chatsLoading, setChatsLoading] = useState(true);

  // Load user's chat sessions from database
  useEffect(() => {
    const loadUserChats = async () => {
      if (!user) {
        setChats([]);
        setActiveChatId(null);
        setMessages([]);
        setChatsLoading(false);
        return;
      }

      try {
        setChatsLoading(true);
        
        // Clear any legacy localStorage data
        ChatService.clearLocalStorageData();
        
        // Load chats from database
        const userChats = await ChatService.getUserChatSessions();
        setChats(userChats);
        
        // If no active chat but chats exist, select the most recent one
        if (!activeChatId && userChats.length > 0) {
          const mostRecentChat = userChats[0]; // Already sorted by updated_at DESC
          setActiveChatId(mostRecentChat.id);
          setMessages(mostRecentChat.messages || []);
        } else if (activeChatId) {
          // Load messages for the active chat
          const activeChat = userChats.find(chat => chat.id === activeChatId);
          if (activeChat) {
            setMessages(activeChat.messages || []);
          } else {
            // Active chat not found, reset
            setActiveChatId(null);
            setMessages([]);
          }
        }
      } catch (error) {
        console.error('Error loading user chats:', error);
        setChats([]);
      } finally {
        setChatsLoading(false);
      }
    };

    loadUserChats();
  }, [user, activeChatId]);
  
  // Handle window resize and mobile/desktop detection
  useEffect(() => {
    const handleResize = () => {
      const wasMobile = isMobile;
      const nowMobile = window.innerWidth < MOBILE_BREAKPOINT;
      
      if (wasMobile !== nowMobile) {
        setIsMobile(nowMobile);
        // Reset mobile sidebar state when switching to desktop
        if (!nowMobile) {
          setShowMobileSidebar(false);
        }
      }
    };

    // Initial check
    handleResize();
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isMobile]);
  
  // Define handleSelectChat first since it's used in other callbacks
  const handleSelectChat = useCallback((chatId) => {
    setActiveChatId(chatId);
  }, []);

  // Define handleNewChat next since it's used in other callbacks
  const handleNewChat = useCallback(() => {
    setActiveChatId(null);
    setMessages([]);
  }, []);

  // Toggle mobile sidebar
  const toggleMobileSidebar = useCallback(() => {
    setShowMobileSidebar(prev => !prev);
  }, []);

  // Close mobile sidebar when chat is selected
  const handleSelectChatWrapper = useCallback((chatId) => {
    handleSelectChat(chatId);
    if (isMobile) {
      setShowMobileSidebar(false);
    }
  }, [isMobile, handleSelectChat]);
  
  // Close mobile sidebar when new chat is created
  const handleNewChatWrapper = useCallback(() => {
    handleNewChat();
    if (isMobile) {
      setShowMobileSidebar(false);
    }
  }, [isMobile, handleNewChat]);
  
  // Toggle sidebar collapse (desktop)
  const handleToggleCollapse = useCallback(() => {
    setIsSidebarCollapsed(prev => !prev);
  }, []);

  // Load messages for active chat
  useEffect(() => {
    const activeChat = chats.find(chat => chat.id === activeChatId);
    if (activeChat) {
      setMessages(activeChat ? activeChat.messages : []);
    } else {
      setMessages([]);
    }
  }, [activeChatId, chats]);

  // Create new chat with database storage
  const createNewChat = async (firstMessage) => {
    try {
      if (!user) {
        console.error('User not authenticated');
        return null;
      }

      // Generate title from first message
      const title = firstMessage.content.length > 50 
        ? firstMessage.content.substring(0, 50) + '...'
        : firstMessage.content;

      // Create chat session in database
      const newChat = await ChatService.createChatSession(title, firstMessage);
      
      // Update local state
      setChats(prevChats => [newChat, ...prevChats]);
      setActiveChatId(newChat.id);
      setMessages([firstMessage]);
      
      return newChat.id;
    } catch (error) {
      console.error('Error creating new chat:', error);
      return null;
    }
  };

  // Update chat with new messages
  const updateChat = async (chatId, newMessages) => {
    try {
      // Update local state immediately for responsiveness
      setChats(prevChats => 
        prevChats.map(chat => 
          chat.id === chatId 
            ? {
                ...chat,
                messages: newMessages,
                messageCount: newMessages.length,
                lastMessage: newMessages[newMessages.length - 1]?.content || '',
                updatedAt: new Date().toISOString()
              }
            : chat
        )
      );

      // Note: Individual messages are saved via ChatService.addMessageToSession
      // This function just updates the local state for UI responsiveness
    } catch (error) {
      console.error('Error updating chat:', error);
    }
  };

  // Delete chat from database
  const handleDeleteChat = async (chatId, e) => {
    e.stopPropagation();
    
    try {
      // Delete from database
      await ChatService.deleteSession(chatId);
      
      // Update local state
      setChats(prevChats => {
        const updatedChats = prevChats.filter(chat => chat.id !== chatId);
        
        // If the deleted chat was active, clear the active chat
        if (chatId === activeChatId) {
          setActiveChatId(null);
          setMessages([]);
        }
        
        return updatedChats;
      });
    } catch (error) {
      console.error('Error deleting chat:', error);
    }
  };

  const handleMessageError = (error) => {
    console.error('Error sending message:', error);
    const errorMessage = {
      role: 'assistant',
      content: 'Sorry, I encountered an error processing your request. Please try again.',
      timestamp: new Date().toISOString(),
      isError: true
    };

    if (activeChatId) {
      const updatedMessages = [...messages, errorMessage];
      setMessages(updatedMessages);
      updateChat(activeChatId, updatedMessages);
    }
  };

  const handleSendMessage = async (messageContent) => {
    if (!user) {
      console.error('User not authenticated');
      return;
    }

    const userMessage = {
      role: 'user',
      content: messageContent,
      timestamp: new Date().toISOString()
    };

    let currentChatId = activeChatId;
    
    // If no active chat, create a new one
    if (!currentChatId) {
      currentChatId = await createNewChat(userMessage);
      if (!currentChatId) {
        handleMessageError(new Error('Failed to create new chat'));
        return;
      }
    } else {
      // Add user message to existing chat in database
      try {
        await ChatService.addMessageToSession(currentChatId, userMessage.role, userMessage.content);
        
        // Update local state
        const updatedMessages = [...messages, userMessage];
        setMessages(updatedMessages);
        updateChat(currentChatId, updatedMessages);
      } catch (error) {
        console.error('Error adding message to session:', error);
        handleMessageError(error);
        return;
      }
    }

    setIsLoading(true);

    try {
      // Prepare messages for API call
      const apiMessages = messages.concat([userMessage]).map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      // Call backend API
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/prompt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: apiMessages
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const aiMessage = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString()
      };

      // Add AI response to database
      await ChatService.addMessageToSession(currentChatId, aiMessage.role, aiMessage.content);
      
      // Update local state
      setMessages(prev => [...prev, aiMessage]);
      const finalMessages = [...messages, userMessage, aiMessage];
      updateChat(currentChatId, finalMessages);

    } catch (error) {
      handleMessageError(error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle authentication redirects
  useEffect(() => {
    if (loading) return; // Don't process redirects while still loading
    
    if (!user && !location.pathname.startsWith('/auth')) {
      navigate('/');
    } else if (user && location.pathname === '/') {
      navigate('/chat');
    }
  }, [user, location.pathname, navigate, loading]);

  // Show loading spinner while auth state is being determined
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-20 bg-white dark:bg-gray-800 shadow-sm p-2 flex justify-between items-center">
        <button
          onClick={toggleMobileSidebar}
          className="p-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Toggle sidebar"
        >
          <FiMenu className="w-6 h-6" />
        </button>
        
        <h1 className="text-xl font-bold text-blue-600 dark:text-blue-400">PatchAI</h1>
        
        <button
          onClick={handleSignOut}
          className="p-2 text-gray-600 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400 focus:outline-none"
          title="Sign out"
        >
          <FiLogOut className="w-6 h-6" />
        </button>
      </div>

      {/* Desktop Sidebar - Always visible on desktop */}
      <div className="hidden md:flex flex-col h-full w-64 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="flex-1 overflow-y-auto">
          <Sidebar
            chatHistory={chats}
            activeChatId={activeChatId}
            onSelectChat={handleSelectChat}
            onNewChat={handleNewChat}
            onDeleteChat={(chatId, e) => handleDeleteChat(chatId, e)}
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={handleToggleCollapse}
          />
        </div>
      </div>

      {/* Mobile Sidebar - Hidden by default */}
      <div
        ref={sidebarRef}
        className={`md:hidden fixed inset-y-0 left-0 flex flex-col transform ${
          showMobileSidebar ? 'translate-x-0' : '-translate-x-full'
        } z-30 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-transform duration-300 ease-in-out`}
      >
        <div className="flex-1 overflow-y-auto">
          <Sidebar
            chatHistory={chats}
            activeChatId={activeChatId}
            onSelectChat={handleSelectChatWrapper}
            onNewChat={handleNewChatWrapper}
            onDeleteChat={(chatId, e) => handleDeleteChat(chatId, e)}
            isCollapsed={false}
            onToggleCollapse={toggleMobileSidebar}
          />
        </div>
      </div>

      {/* Overlay for mobile */}
      {showMobileSidebar && (
        <div 
          className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-20"
          onClick={toggleMobileSidebar}
        />
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full overflow-hidden pt-14 md:pt-0 md:ml-64">
        {/* Chat Feed with padding and scrollable area */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6">
          <div className="max-w-3xl mx-auto w-full pb-24">
            <ChatFeed messages={messages} isLoading={isLoading} />
          </div>
        </div>
        
        {/* Fixed input container at the bottom */}
        <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <div className="max-w-3xl mx-auto w-full px-4 md:px-6 py-4">
            <ChatInput onSendMessage={handleSendMessage} isSending={isLoading} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
