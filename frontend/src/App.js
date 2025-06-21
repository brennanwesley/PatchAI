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

  // Create new chat session with first message
  const createNewChat = async (firstMessage) => {
    console.log('🆕 createNewChat called with:', firstMessage);
    
    if (!user) {
      console.error('❌ User not authenticated');
      return null;
    }

    try {
      // Create a title from the first message (first 30 chars)
      const chatTitle = firstMessage.content.substring(0, 30) + (firstMessage.content.length > 30 ? '...' : '');
      
      console.log('📝 Creating new chat with title:', chatTitle);
      
      // Create new chat session in database
      const newChat = await ChatService.createChatSession(chatTitle, firstMessage);
      console.log('✅ New chat created:', newChat);
      
      if (!newChat || !newChat.id) {
        throw new Error('Failed to create new chat session');
      }
      
      // Create the chat object with proper structure
      const newChatObj = {
        id: newChat.id,
        title: chatTitle,
        messages: [firstMessage],
        messageCount: 1,
        lastMessage: firstMessage.content,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      // Update local state
      setChats(prevChats => {
        const updatedChats = [newChatObj, ...prevChats];
        console.log('🔄 Updated chats list:', updatedChats);
        return updatedChats;
      });
      
      setActiveChatId(newChat.id);
      setMessages([firstMessage]);
      
      console.log('✅ Updated local state with new chat:', newChatObj);
      
      return newChat.id;
    } catch (error) {
      console.error('❌ Error creating new chat:', error);
      // Rethrow the error to be caught by the caller
      throw new Error(`Failed to create new chat: ${error.message || 'Unknown error'}`);
    }
  };

  // Update chat with new messages
  const updateChat = async (chatId, newMessages) => {
    if (!chatId) {
      console.warn('⚠️ Cannot update chat: No chat ID provided');
      return;
    }
    
    console.log(`🔄 Updating chat ${chatId} with ${newMessages?.length || 0} messages`);
    
    try {
      // Ensure we have valid messages
      const validMessages = Array.isArray(newMessages) ? newMessages : [];
      
      // Update local state immediately for responsiveness
      setChats(prevChats => {
        const chatExists = prevChats.some(chat => chat.id === chatId);
        
        if (!chatExists) {
          console.log(`➕ Adding new chat ${chatId} to the list`);
          // If this is a new chat, add it to the beginning of the list
          return [{
            id: chatId,
            title: validMessages[0]?.content?.substring(0, 30) + (validMessages[0]?.content?.length > 30 ? '...' : '') || 'New Chat',
            messages: validMessages,
            messageCount: validMessages.length,
            lastMessage: validMessages[validMessages.length - 1]?.content || '',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          }, ...prevChats];
        }
        
        // Otherwise, update the existing chat
        return prevChats.map(chat => {
          if (chat.id === chatId) {
            return {
              ...chat,
              messages: validMessages,
              messageCount: validMessages.length,
              lastMessage: validMessages[validMessages.length - 1]?.content || '',
              updatedAt: new Date().toISOString()
            };
          }
          return chat;
        });
      });
      
      // If this is the active chat, update the messages
      if (chatId === activeChatId) {
        console.log(`🔄 Updating active chat messages (${validMessages.length} messages)`);
        setMessages(validMessages);
      }
      
      // Update the chat title if it's a new chat or if the first message has changed
      if (validMessages.length > 0) {
        const firstMessage = validMessages[0];
        if (firstMessage.role === 'user' && firstMessage.content) {
          const newTitle = firstMessage.content.substring(0, 30) + 
                         (firstMessage.content.length > 30 ? '...' : '');
          
          setChats(prevChats => 
            prevChats.map(chat => 
              chat.id === chatId && chat.title !== newTitle
                ? { ...chat, title: newTitle }
                : chat
            )
          );
          
          // Also update the chat title in the database
          try {
            await ChatService.updateSessionTitle(chatId, newTitle);
          } catch (error) {
            console.error('❌ Failed to update chat title:', error);
          }
        }
      }
      
    } catch (error) {
      console.error('❌ Error updating chat:', error);
      // Even if there's an error, we don't want to break the UI
      // The next refresh or navigation will correct any inconsistencies
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
      role: 'assistant',
      content: `Error: ${errorMessage}`,
      timestamp: new Date().toISOString(),
      isError: true
    };

    // Only update messages if we have an active chat
    if (activeChatId && messages) {
      console.log('📝 Adding error message to chat:', activeChatId);
      const updatedMessages = [...messages, errorMessageObj];
      setMessages(updatedMessages);
      updateChat(activeChatId, updatedMessages);
    } else {
      console.warn('⚠️ No active chat or messages array to update with error');
      // If there's no active chat but we need to show the error
      setMessages(prev => [...(prev || []), errorMessageObj]);
    }
  };

  const handleSendMessage = async (messageInput) => {
    console.log('🚀 handleSendMessage called with:', messageInput);
    
    // Handle both string and object inputs from ChatInput
    const messageContent = typeof messageInput === 'string' ? messageInput : messageInput.content;
    const messageFiles = typeof messageInput === 'object' ? messageInput.files : [];
    
    console.log('📝 Processed message content:', messageContent);
    console.log('📎 Message files:', messageFiles);
    
    if (!messageContent?.trim()) {
      console.error('❌ Empty message content');
      return;
    }
    
    if (!user) {
      console.error('❌ User not authenticated');
      return;
    }

    // Create a temporary ID that will be replaced when the message is saved
    const tempMessageId = `temp-${Date.now()}`;
    
    // Create user message object
    const userMessage = {
      id: tempMessageId,
      role: 'user',
      content: messageContent.trim(),
      timestamp: new Date().toISOString(),
      files: messageFiles,
      isSending: true // Mark as sending until confirmed saved
    };

    console.log('✅ Created user message:', userMessage);

    let currentChatId = activeChatId;
    let updatedMessages = [];
    
    try {
      // Set loading state immediately
      setIsLoading(true);

      // Optimistically update the UI with the user's message
      updatedMessages = currentChatId ? [...messages, userMessage] : [userMessage];
      setMessages(updatedMessages);

      // If no active chat, create a new one
      if (!currentChatId) {
        console.log('🆕 Creating new chat...');
        try {
          currentChatId = await createNewChat(userMessage);
          console.log('🆔 New chat ID:', currentChatId);
          
          // Update the active chat ID
          setActiveChatId(currentChatId);
          
          // Update the URL to reflect the new chat
          navigate(`/chat/${currentChatId}`, { replace: true });
          
        } catch (error) {
          console.error('❌ Failed to create new chat:', error);
          // Remove the optimistic update if chat creation fails
          setMessages([]);
          throw error;
        }
      } else {
        console.log('📝 Adding message to existing chat:', currentChatId);
        try {
          // Add user message to database
          await ChatService.addMessageToSession(currentChatId, userMessage.role, userMessage.content);
          console.log('✅ Message added to database');
          
          // Update the message with a permanent ID if needed
          // (the backend might have assigned a new ID)
          
        } catch (error) {
          console.error('❌ Failed to add message to database:', error);
          // Remove the optimistic update if message save fails
          setMessages(messages);
          throw error;
        }
      }

      // Prepare messages for API call (include all previous messages for context)
      const apiMessages = updatedMessages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      console.log('📡 Sending to API:', apiMessages);

      try {
        // Call backend API through ApiService
        const response = await ApiService.sendPrompt(apiMessages);
        console.log('✅ API Response received:', response);

        const assistantMessage = {
          id: `msg-${Date.now()}`,
          role: 'assistant',
          content: response.response || response.content || 'No response from assistant',
          timestamp: new Date().toISOString()
        };
        
        console.log('🤖 Assistant message:', assistantMessage);

        try {
          // Add AI response to database
          await ChatService.addMessageToSession(currentChatId, assistantMessage.role, assistantMessage.content);
          console.log('✅ AI message added to database');
          
          // Update local state with both user and assistant messages
          const finalMessages = [...updatedMessages, assistantMessage];
          setMessages(finalMessages);
          
          // Update the chat in the sidebar
          updateChat(currentChatId, finalMessages);
          
        } catch (dbError) {
          console.error('❌ Failed to save assistant message to database:', dbError);
          // Even if DB save fails, we'll still show the message to the user
          // but we'll mark it as potentially unsaved
          const finalMessages = [...updatedMessages, {
            ...assistantMessage,
            error: 'Failed to save to database'
          }];
          setMessages(finalMessages);
          updateChat(currentChatId, finalMessages);
        }
        
      } catch (apiError) {
        console.error('❌ API Error:', apiError);
        
        // Add an error message to the chat
        const errorMessage = {
          id: `error-${Date.now()}`,
          role: 'system',
          content: 'Sorry, I encountered an error processing your request. Please try again.',
          isError: true,
          timestamp: new Date().toISOString()
        };
        
        const finalMessages = [...updatedMessages, errorMessage];
        setMessages(finalMessages);
        updateChat(currentChatId, finalMessages);
        
        throw apiError;
      }

    } catch (error) {
      console.error('❌ Error in handleSendMessage:', error);
      handleMessageError(error);
    } finally {
      console.log('🔄 Clearing loading state...');
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
                    <div className="p-6 pb-24">
                      <ChatFeed messages={messages} isLoading={isLoading} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Fixed input container at the bottom */}
            <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-lg">
              <div className="px-6 py-4">
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
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
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
