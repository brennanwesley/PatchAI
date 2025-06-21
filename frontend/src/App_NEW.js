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
      
      const currentMessages = [...messages, userMessage];
      const apiMessages = currentMessages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      const response = await ApiService.sendPrompt(apiMessages, chatId);
      console.log('✅ AI response received');

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
      
      // Add error message
      const errorMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
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
    <div className="app">
      {/* Mobile Header */}
      {isMobile && (
        <div className="mobile-header">
          <button 
            className="mobile-menu-btn"
            onClick={handleToggleMobileSidebar}
            aria-label="Toggle menu"
          >
            <FiMenu size={24} />
          </button>
          <h1 className="mobile-title">PatchAI</h1>
          <button 
            className="mobile-logout-btn"
            onClick={handleSignOut}
            aria-label="Sign out"
          >
            <FiLogOut size={20} />
          </button>
        </div>
      )}

      {/* Mobile Sidebar Overlay */}
      {isMobile && showMobileSidebar && (
        <div className="mobile-sidebar-overlay" onClick={() => setShowMobileSidebar(false)} />
      )}

      {/* Sidebar */}
      <div 
        ref={sidebarRef}
        className={`sidebar-container ${isMobile ? 'mobile' : 'desktop'} ${
          isMobile ? (showMobileSidebar ? 'show' : 'hide') : (isSidebarCollapsed ? 'collapsed' : 'expanded')
        }`}
      >
        <Sidebar
          chats={chats}
          activeChatId={activeChatId}
          onChatSelect={handleChatSelect}
          onNewChat={handleNewChat}
          onDeleteChat={handleDeleteChat}
          onSignOut={handleSignOut}
          onToggleCollapse={handleToggleCollapse}
          isCollapsed={isSidebarCollapsed}
          isMobile={isMobile}
          loading={chatsLoading}
        />
      </div>

      {/* Main Chat Area */}
      <div className={`main-content ${isMobile ? 'mobile' : 'desktop'} ${
        isMobile ? 'full-width' : (isSidebarCollapsed ? 'sidebar-collapsed' : 'sidebar-expanded')
      }`}>
        <div className="chat-container">
          <ChatFeed 
            messages={messages} 
            isLoading={isLoading}
            activeChatId={activeChatId}
          />
          <ChatInput 
            onSendMessage={handleSendMessage}
            disabled={isLoading}
            placeholder={activeChatId ? "Type your message..." : "Start a new conversation..."}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
