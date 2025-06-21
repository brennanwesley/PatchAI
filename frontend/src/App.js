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
import { ApiService } from './services/apiService';
import './App.css';

// Constants
const MOBILE_BREAKPOINT = 768;

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, signOut, loading } = useAuth();
  
  // Handle sign out
  const handleSignOut = async () => {
    try {
      await signOut();
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
  const [isLoadingChats, setIsLoadingChats] = useState(false); // Prevent multiple simultaneous calls
  const [isCreatingNewChat, setIsCreatingNewChat] = useState(false); // Prevent useEffect from clearing messages during chat creation

  // Controlled function to refresh chats from database
  const refreshChats = useCallback(async () => {
    try {
      console.log('🔄 Refreshing chats from database...');
      const userChats = await ChatService.getUserChatSessions();
      setChats(userChats);
      console.log('✅ Chats refreshed:', userChats.length);
    } catch (error) {
      console.error('❌ Error refreshing chats:', error);
    }
  }, []);

  // Load user's chat sessions from database
  useEffect(() => {
    const loadUserChats = async () => {
      // Prevent multiple simultaneous calls
      if (isLoadingChats) {
        console.log('Chat loading already in progress, skipping...');
        return;
      }

      if (!user) {
        setChats([]);
        setActiveChatId(null);
        setMessages([]);
        setChatsLoading(false);
        return;
      }

      try {
        setIsLoadingChats(true);
        setChatsLoading(true);
        
        // Clear any legacy localStorage data
        ChatService.clearLocalStorageData();
        
        // Load chats from database
        const userChats = await ChatService.getUserChatSessions();
        setChats(userChats);
        
        // Only auto-select the most recent chat if no chat is currently active
        if (!activeChatId && userChats.length > 0 && !isCreatingNewChat) {
          const mostRecentChat = userChats[0]; // Already sorted by updated_at DESC
          setActiveChatId(mostRecentChat.id);
          setMessages(mostRecentChat.messages || []);
          console.log('🔄 Auto-selected most recent chat:', mostRecentChat.id);
        }
      } catch (error) {
        console.error('Error loading user chats:', error);
        
        // Handle authentication errors
        if (error?.isAuthError) {
          console.log('Authentication error detected, user needs to re-login');
          // Don't set error state, just clear data
          setChats([]);
          setActiveChatId(null);
          setMessages([]);
        } else {
          // For other errors, show empty state but don't break the app
          setChats([]);
          setActiveChatId(null);
          setMessages([]);
        }
      } finally {
        setIsLoadingChats(false);
        setChatsLoading(false);
      }
    };

    if (user) {
      loadUserChats();
    }
  }, [user]); // Only run when user changes to prevent interference with chat creation

  // Handle URL-based chat selection
  useEffect(() => {
    const path = location.pathname;
    const chatIdFromUrl = path.startsWith('/chat/') ? path.split('/chat/')[1] : null;
    
    if (chatIdFromUrl && chatIdFromUrl !== activeChatId) {
      console.log('🔗 URL-based chat selection:', chatIdFromUrl);
      handleSelectChat(chatIdFromUrl);
    }
  }, [location.pathname, activeChatId, handleSelectChat]);

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
    console.log('🔄 Selecting chat:', chatId);
    setActiveChatId(chatId);
    
    // Find and load messages for the selected chat
    const selectedChat = chats.find(chat => chat.id === chatId);
    if (selectedChat) {
      setMessages(selectedChat.messages || []);
      console.log('📄 Loaded messages for chat:', chatId, selectedChat.messages?.length || 0);
    } else {
      console.warn('⚠️ Chat not found in local state:', chatId);
      setMessages([]);
    }
  }, [chats]);

  // Define handleNewChat next since it's used in other callbacks
  const handleNewChat = useCallback(() => {
    console.log('🆕 Starting new chat...');
    setActiveChatId(null);
    setMessages([]);
    setIsCreatingNewChat(false); // Reset flag when starting fresh
    // Navigate to new chat URL
    navigate('/chat', { replace: true });
  }, [navigate]);

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

  // Load messages when active chat changes
  useEffect(() => {
    const activeChat = chats.find(chat => chat.id === activeChatId);
    if (activeChat) {
      const chatMessages = Array.isArray(activeChat.messages) ? activeChat.messages : [];
      console.log('📋 Loading chat messages for chat:', activeChatId);
      setMessages(chatMessages);
    } else if (activeChatId === null) {
      console.log('📋 No active chat, clearing messages');
      setMessages([]);
    }
  }, [activeChatId, chats]);

  const handleSendMessage = async (messageInput) => {
    console.log('🚀 SEND MESSAGE START:', messageInput);
    
    try {
      setIsLoading(true);

      // Handle different input types
      const messageText = typeof messageInput === 'string' ? messageInput : messageInput.content;
      const files = typeof messageInput === 'object' ? messageInput.files : [];
      
      if (!messageText?.trim()) {
        console.warn('⚠️ Empty message, not sending');
        setIsLoading(false);
        return;
      }

      // Create user message
      const userMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: messageText.trim(),
        timestamp: new Date().toISOString(),
        files: files || []
      };
      
      console.log('👤 User message created:', userMessage);

      let chatId = activeChatId;

      // If no active chat, create new one
      if (!chatId) {
        console.log('🆕 Creating new chat...');
        
        // Set flag to prevent useEffect from clearing messages during creation
        setIsCreatingNewChat(true);
        
        // Optimistically show the message
        setMessages([userMessage]);
        
        try {
          // Create chat in database
          const chatTitle = userMessage.content.substring(0, 30) + (userMessage.content.length > 30 ? '...' : '');
          const newChat = await ChatService.createChatSession(chatTitle, userMessage);
          
          chatId = newChat.id;
          console.log('✅ New chat created:', chatId);
          
          // Update state
          setActiveChatId(chatId);
          
          // Refresh chats from database to ensure new chat appears in sidebar
          await refreshChats();
          
          // Navigate to new chat
          navigate(`/chat/${chatId}`, { replace: true });
          
        } catch (error) {
          console.error('❌ Failed to create chat:', error);
          setMessages([]);
          setIsCreatingNewChat(false); // Reset flag on error
          setIsLoading(false);
          return;
        }
      } else {
        console.log('📝 Adding to existing chat:', chatId);
        
        // Add message to existing chat
        setMessages(prev => [...prev, userMessage]);
        
        try {
          // Save user message to database
          await ChatService.addMessageToSession(chatId, userMessage.role, userMessage.content);
          console.log('✅ User message saved to database');
        } catch (error) {
          console.error('❌ Failed to save user message:', error);
          // Don't return here, still try to get AI response
        }
      }

      // Get AI response
      try {
        console.log('🤖 Getting AI response...');
        
        // Prepare messages for API (get current messages including the new user message)
        const currentMessages = chatId ? 
          [...(messages || []), userMessage] : 
          [userMessage];
          
        const apiMessages = currentMessages.map(msg => ({
          role: msg.role,
          content: msg.content
        }));

        console.log('📡 Sending to API:', apiMessages);
        const response = await ApiService.sendPrompt(apiMessages);
        console.log('✅ AI response received:', response);

        const assistantMessage = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: response.response || response.content || 'No response from assistant',
          timestamp: new Date().toISOString()
        };

        // Add AI response to UI
        setMessages(prev => [...prev, assistantMessage]);

        // Save AI response to database
        try {
          await ChatService.addMessageToSession(chatId, assistantMessage.role, assistantMessage.content);
          console.log('✅ AI response saved to database');
        } catch (error) {
          console.error('❌ Failed to save AI response:', error);
        }

        // Update chat in chats array
        setChats(prevChats => 
          prevChats.map(chat => 
            chat.id === chatId 
              ? { 
                  ...chat, 
                  messages: [...(chat.messages || []), userMessage, assistantMessage],
                  lastMessage: assistantMessage.content,
                  updatedAt: new Date().toISOString()
                }
              : chat
          )
        );

      } catch (error) {
        console.error('❌ AI response failed:', error);
        
        const errorMessage = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your message. Please try again.',
          timestamp: new Date().toISOString(),
          isError: true
        };
        
        setMessages(prev => [...prev, errorMessage]);
      }

    } catch (error) {
      console.error('❌ Send message failed:', error);
    } finally {
      setIsLoading(false);
      setIsCreatingNewChat(false); // Reset flag
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
    console.error('Error in chat:', error);
    
    // Extract error message from different error formats
    let errorMessage = 'Sorry, I encountered an error processing your request. Please try again.';
    
    if (typeof error === 'string') {
      errorMessage = error;
    } else if (error?.message) {
      errorMessage = error.message;
    } else if (error?.response?.data?.detail) {
      errorMessage = error.response.data.detail;
    } else if (error?.details) {
      errorMessage = error.details;
    }
    
    console.log('📝 Error details:', { 
      error, 
      activeChatId, 
      messageCount: messages?.length || 0 
    });
    
    const errorMessageObj = {
      id: `error-${Date.now()}`,
      role: 'assistant',
      content: `Error: ${errorMessage}`,
      timestamp: new Date().toISOString(),
      isError: true
    };

    // Ensure messages is always an array before spreading to prevent recursive errors
    const safeMessages = Array.isArray(messages) ? messages : [];
    
    // Only update messages if we have an active chat
    if (activeChatId) {
      console.log('📝 Adding error message to chat:', activeChatId);
      const updatedMessages = [...safeMessages, errorMessageObj];
      setMessages(updatedMessages);
      
      // Update the chat in chats array
      setChats(prevChats => 
        prevChats.map(chat => 
          chat.id === activeChatId 
            ? { 
                ...chat, 
                messages: updatedMessages,
                lastMessage: errorMessageObj.content,
                updatedAt: new Date().toISOString()
              }
            : chat
        )
      );
    } else {
      console.warn('⚠️ No active chat, adding error to current messages');
      // If there's no active chat but we need to show the error
      setMessages([...safeMessages, errorMessageObj]);
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
            onLogOut={handleSignOut}
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
            onLogOut={handleSignOut}
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
      <div className="flex-1 flex flex-col h-full overflow-hidden pt-14 md:pt-0">
        {/* Mobile Layout - Full width chat */}
        <div className="md:hidden flex-1 overflow-y-auto overflow-x-hidden p-4">
          <div className="max-w-3xl mx-auto w-full pb-24">
            <ChatFeed messages={messages} isLoading={isLoading} />
          </div>
        </div>
        
        {/* Desktop Layout - Chat + Right Sidebar */}
        <div className="hidden md:flex flex-1 h-full">
          {/* Main Chat Area */}
          <div className="flex-1 flex flex-col h-full min-w-0">
            {/* Chat Feed Container with depth */}
            <div className="flex-1 overflow-y-auto bg-gray-100 dark:bg-gray-900 p-6">
              <div className="h-full bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
                <div className="h-full flex flex-col">
                  <div className="flex-1 overflow-y-auto">
                    <div className="max-w-4xl mx-auto p-6 pb-24">
                      <ChatFeed messages={messages} isLoading={isLoading} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Fixed input container at the bottom */}
            <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-lg">
              <div className="max-w-4xl mx-auto px-6 py-4">
                <ChatInput onSendMessage={handleSendMessage} isSending={isLoading} />
              </div>
            </div>
          </div>
          
          {/* Right Sidebar with Status Cards - Desktop Only */}
          <div className="w-80 bg-gray-50 dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 p-6 overflow-y-auto">
            <div className="space-y-6">
              {/* Prompt Suggestions Card */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 p-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Quick Prompts
                </h3>
                <div className="space-y-2">
                  {[
                    "Analyze recent oil market trends",
                    "Compare WTI vs Brent pricing",
                    "Explain drilling techniques",
                    "Review environmental regulations",
                    "Assess investment opportunities"
                  ].map((prompt, index) => (
                    <button
                      key={index}
                      onClick={() => handleSendMessage(prompt)}
                      className="w-full text-left p-3 text-sm bg-gray-50 dark:bg-gray-700 hover:bg-blue-50 dark:hover:bg-blue-900 rounded-md border border-gray-200 dark:border-gray-600 transition-colors duration-200"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Placeholder for WTI Price Card */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 p-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                  WTI Price
                </h3>
                <div className="text-center py-4">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">$72.45</div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">+1.2% today</div>
                  <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">Live data coming soon</div>
                </div>
              </div>
              
              {/* Placeholder for Recent Acquisitions Card */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 p-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H7m2 0v-4a2 2 0 012-2h2a2 2 0 012 2v4" />
                  </svg>
                  Recent Deals
                </h3>
                <div className="space-y-2">
                  <div className="text-sm">
                    <div className="font-medium text-gray-900 dark:text-gray-100">ExxonMobil Acquisition</div>
                    <div className="text-gray-500 dark:text-gray-400">$60B Permian Basin</div>
                  </div>
                  <div className="text-sm">
                    <div className="font-medium text-gray-900 dark:text-gray-100">Chevron Deal</div>
                    <div className="text-gray-500 dark:text-gray-400">$53B Hess Corp</div>
                  </div>
                  <div className="text-xs text-gray-400 dark:text-gray-500 mt-2">Live data coming soon</div>
                </div>
              </div>
              
              {/* Placeholder for Market Insights Card */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 p-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  Market Insights
                </h3>
                <div className="text-sm text-gray-600 dark:text-gray-300">
                  <p className="mb-2">Oil demand expected to rise 2.4% this quarter driven by winter heating needs.</p>
                  <div className="text-xs text-gray-400 dark:text-gray-500">AI insights coming soon</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Mobile Fixed input container at the bottom */}
        <div className="md:hidden border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <div className="max-w-3xl mx-auto w-full px-4 py-4">
            <ChatInput onSendMessage={handleSendMessage} isSending={isLoading} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
