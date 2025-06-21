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
  
  // SIMPLIFIED CHAT STATE - Clean slate approach
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [chatsLoading, setChatsLoading] = useState(true);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < MOBILE_BREAKPOINT;
      setIsMobile(mobile);
      if (!mobile) {
        setShowMobileSidebar(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Handle clicks outside sidebar on mobile
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isMobile && showMobileSidebar && sidebarRef.current && !sidebarRef.current.contains(event.target)) {
        setShowMobileSidebar(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isMobile, showMobileSidebar]);

  // LOAD CHATS ON MOUNT - Simple and clean
  useEffect(() => {
    if (user) {
      loadChats();
    }
  }, [user]);

  // LOAD MESSAGES WHEN CHAT CHANGES - Simple and clean
  useEffect(() => {
    if (activeChatId) {
      loadMessages(activeChatId);
    } else {
      setMessages([]);
    }
  }, [activeChatId]);

  // SIMPLE CHAT LOADING
  const loadChats = async () => {
    try {
      console.log('📂 Loading chats...');
      setChatsLoading(true);
      const userChats = await ChatService.getUserChatSessions();
      console.log('✅ Chats loaded:', userChats.length);
      setChats(userChats);
    } catch (error) {
      console.error('❌ Failed to load chats:', error);
      setChats([]);
    } finally {
      setChatsLoading(false);
    }
  };

  // SIMPLE MESSAGE LOADING
  const loadMessages = async (chatId) => {
    try {
      console.log('📋 Loading messages for chat:', chatId);
      const chat = chats.find(c => c.id === chatId);
      if (chat && chat.messages) {
        setMessages(Array.isArray(chat.messages) ? chat.messages : []);
        console.log('✅ Messages loaded:', chat.messages.length);
      } else {
        // Fallback: load from database
        const chatData = await ChatService.getChatSession(chatId);
        if (chatData && chatData.messages) {
          setMessages(Array.isArray(chatData.messages) ? chatData.messages : []);
        } else {
          setMessages([]);
        }
      }
    } catch (error) {
      console.error('❌ Failed to load messages:', error);
      setMessages([]);
    }
  };

  // SIMPLE CHAT SELECTION
  const handleChatSelect = (chatId) => {
    console.log('🎯 Selecting chat:', chatId);
    setActiveChatId(chatId);
    navigate(`/chat/${chatId}`);
    if (isMobile) {
      setShowMobileSidebar(false);
    }
  };

  // SIMPLE NEW CHAT
  const handleNewChat = () => {
    console.log('🆕 Starting new chat');
    setActiveChatId(null);
    setMessages([]);
    navigate('/chat');
    if (isMobile) {
      setShowMobileSidebar(false);
    }
  };

  // COMPLETELY REBUILT MESSAGE SENDING - Clean and simple
  const handleSendMessage = async (messageInput) => {
    console.log('🚀 Sending message:', messageInput);
    
    try {
      setIsLoading(true);

      // Extract message content
      const messageText = typeof messageInput === 'string' ? messageInput : messageInput.content;
      const files = typeof messageInput === 'object' ? messageInput.files : [];
      
      if (!messageText?.trim()) {
        console.warn('⚠️ Empty message');
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

      // STEP 1: Add user message to UI immediately
      setMessages(prev => [...prev, userMessage]);
      console.log('✅ User message added to UI');

      let chatId = activeChatId;

      // STEP 2: Create new chat if needed
      if (!chatId) {
        console.log('🆕 Creating new chat...');
        
        const chatTitle = messageText.substring(0, 30) + (messageText.length > 30 ? '...' : '');
        const newChat = await ChatService.createChatSession(chatTitle, userMessage);
        
        chatId = newChat.id;
        setActiveChatId(chatId);
        
        // Add to chats list
        setChats(prev => [newChat, ...prev]);
        
        // Update URL
        navigate(`/chat/${chatId}`, { replace: true });
        
        console.log('✅ New chat created:', chatId);
      } else {
        // Save user message to existing chat
        await ChatService.addMessageToSession(chatId, userMessage.role, userMessage.content);
        console.log('✅ User message saved to existing chat');
      }

      // STEP 3: Get AI response
      console.log('🤖 Getting AI response...');
      console.log('📤 Sending to API:', { messages: apiMessages, chatId });
      
      const currentMessages = [...messages, userMessage];
      const apiMessages = currentMessages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      const response = await ApiService.sendPrompt(apiMessages, chatId);
      console.log('✅ AI response received:', response);

      // Create AI message
      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response || response.content || 'No response received',
        timestamp: new Date().toISOString()
      };

      // STEP 4: Add AI message to UI
      setMessages(prev => [...prev, assistantMessage]);
      console.log('✅ AI message added to UI');

      // STEP 5: Save AI message to database
      await ChatService.addMessageToSession(chatId, assistantMessage.role, assistantMessage.content);
      console.log('✅ AI message saved to database');

      // STEP 6: Update chat in sidebar
      setChats(prev => prev.map(chat => 
        chat.id === chatId 
          ? { 
              ...chat, 
              messages: [...(chat.messages || []), userMessage, assistantMessage],
              lastMessage: assistantMessage.content,
              updatedAt: new Date().toISOString()
            }
          : chat
      ));
      console.log('✅ Chat updated in sidebar');

    } catch (error) {
      console.error('❌ Send message failed:', error);
      console.error('❌ Error details:', {
        message: error.message,
        status: error.status,
        isAuthError: error.isAuthError,
        stack: error.stack
      });
      
      // Add error message
      const errorMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.message}. Please try again.`,
        timestamp: new Date().toISOString(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // SIMPLE CHAT DELETION
  const handleDeleteChat = async (chatId, e) => {
    e.stopPropagation();
    
    try {
      console.log('🗑️ Deleting chat:', chatId);
      
      await ChatService.deleteSession(chatId);
      
      setChats(prev => prev.filter(chat => chat.id !== chatId));
      
      if (chatId === activeChatId) {
        setActiveChatId(null);
        setMessages([]);
        navigate('/chat');
      }
      
      console.log('✅ Chat deleted');
    } catch (error) {
      console.error('❌ Failed to delete chat:', error);
    }
  };

  // Toggle mobile sidebar
  const handleToggleMobileSidebar = useCallback(() => {
    setShowMobileSidebar(prev => !prev);
  }, []);

  // Toggle sidebar collapse (desktop)
  const handleToggleCollapse = useCallback(() => {
    setIsSidebarCollapsed(prev => !prev);
  }, []);

  // Show loading screen while auth is loading
  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!user) {
    navigate('/');
    return null;
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Mobile Header */}
      {isMobile && (
        <div className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 h-16">
          <button 
            className="p-2 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400"
            onClick={handleToggleMobileSidebar}
            aria-label="Toggle menu"
          >
            <FiMenu size={20} />
          </button>
          <h1 className="text-lg font-bold text-blue-600 dark:text-blue-400">PatchAI</h1>
          <button 
            className="p-2 text-gray-600 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400"
            onClick={handleSignOut}
            aria-label="Sign out"
          >
            <FiLogOut size={18} />
          </button>
        </div>
      )}

      {/* Desktop Header */}
      {!isMobile && (
        <div className="flex items-center justify-between px-6 py-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 h-16">
          <h1 className="text-xl font-bold text-blue-600 dark:text-blue-400">PatchAI</h1>
          <button
            onClick={handleSignOut}
            className="p-2 text-gray-600 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400 focus:outline-none"
            title="Sign out"
          >
            <FiLogOut className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Main Layout Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Desktop Sidebar */}
        {!isMobile && (
          <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
            <Sidebar
              chats={chats}
              activeChatId={activeChatId}
              onChatSelect={handleChatSelect}
              onNewChat={handleNewChat}
              onDeleteChat={handleDeleteChat}
              onSignOut={handleSignOut}
              onToggleCollapse={handleToggleCollapse}
              isCollapsed={isSidebarCollapsed}
              isMobile={false}
              loading={chatsLoading}
            />
          </div>
        )}

        {/* Mobile Sidebar */}
        {isMobile && (
          <>
            {/* Mobile Sidebar Overlay */}
            {showMobileSidebar && (
              <div 
                className="fixed inset-0 bg-black bg-opacity-50 z-40"
                onClick={() => setShowMobileSidebar(false)}
              />
            )}
            
            {/* Mobile Sidebar */}
            <div
              ref={sidebarRef}
              className={`fixed inset-y-0 left-0 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform duration-300 ease-in-out z-50 ${
                showMobileSidebar ? 'translate-x-0' : '-translate-x-full'
              }`}
            >
              <Sidebar
                chats={chats}
                activeChatId={activeChatId}
                onChatSelect={(chatId) => {
                  handleChatSelect(chatId);
                  setShowMobileSidebar(false);
                }}
                onNewChat={() => {
                  handleNewChat();
                  setShowMobileSidebar(false);
                }}
                onDeleteChat={handleDeleteChat}
                onSignOut={handleSignOut}
                onToggleCollapse={() => setShowMobileSidebar(false)}
                isCollapsed={false}
                isMobile={true}
                loading={chatsLoading}
              />
            </div>
          </>
        )}

        {/* Chat Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="max-w-4xl mx-auto">
              <ChatFeed messages={messages} isLoading={isLoading} activeChatId={activeChatId} />
            </div>
          </div>
          
          {/* Chat Input */}
          <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
            <div className="max-w-4xl mx-auto">
              <ChatInput 
                onSendMessage={handleSendMessage}
                disabled={isLoading}
                placeholder={activeChatId ? "Type your message..." : "Start a new conversation..."}
              />
            </div>
          </div>
        </div>

        {/* Right Sidebar - Desktop Only */}
        {!isMobile && (
          <div className="w-80 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 overflow-y-auto">
            <div className="p-4 space-y-4">
              {/* Quick Prompts */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Quick Prompts
                </h3>
                <div className="space-y-2">
                  {[
                    "Oil market trends",
                    "WTI vs Brent pricing",
                    "Drilling techniques",
                    "Environmental regs",
                    "Investment opportunities"
                  ].map((prompt, index) => (
                    <button
                      key={index}
                      onClick={() => handleSendMessage(prompt)}
                      className="w-full text-left p-2 text-xs bg-white dark:bg-gray-600 hover:bg-blue-50 dark:hover:bg-blue-900 rounded border border-gray-200 dark:border-gray-500 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* WTI Price */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                  WTI Price
                </h3>
                <div className="text-center">
                  <div className="text-lg font-bold text-green-600 dark:text-green-400">$72.45</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">+1.2% today</div>
                </div>
              </div>
              
              {/* Recent Deals */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H7m2 0v-4a2 2 0 012-2h2a2 2 0 012 2v4" />
                  </svg>
                  Recent Deals
                </h3>
                <div className="space-y-2">
                  <div className="text-xs">
                    <div className="font-medium text-gray-900 dark:text-gray-100">ExxonMobil</div>
                    <div className="text-gray-500 dark:text-gray-400">$60B Permian</div>
                  </div>
                  <div className="text-xs">
                    <div className="font-medium text-gray-900 dark:text-gray-100">Chevron</div>
                    <div className="text-gray-500 dark:text-gray-400">$53B Hess</div>
                  </div>
                </div>
              </div>
              
              {/* Market Insights */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  Insights
                </h3>
                <div className="text-xs text-gray-600 dark:text-gray-300">
                  <p>Oil demand up 2.4% this quarter.</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
