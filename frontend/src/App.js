import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ChatFeed from './components/ChatFeed';
import ChatInput from './components/ChatInput';
import { v4 as uuidv4 } from 'uuid';
import { FiMenu, FiLogOut } from 'react-icons/fi';
import { supabase } from './supabaseClient';
import './App.css';

const MOBILE_BREAKPOINT = 768;

function App() {
  const navigate = useNavigate();
  
  // Auth state
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Check auth state on mount
  useEffect(() => {
    // Check active sessions and sets the user
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        const currentUser = session?.user || null;
        setUser(currentUser);
        
        if (currentUser) {
          // User is signed in
          setLoading(false);
        } else {
          // User is not signed in, redirect to landing page
          navigate('/');
        }
      }
    );

    // Check for existing session
    const checkSession = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
          navigate('/');
        }
      } catch (error) {
        console.error('Error checking session:', error);
      } finally {
        setLoading(false);
      }
    };
    
    checkSession();
    
    return () => {
      // Cleanup subscription on unmount
      subscription?.unsubscribe();
    };
  }, [navigate]);

  // Handle sign out
  const handleSignOut = async () => {
    try {
      await supabase.auth.signOut();
      navigate('/');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  // Layout state
  const [isMobile, setIsMobile] = useState(window.innerWidth < MOBILE_BREAKPOINT);
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);
  const sidebarRef = useRef(null);
  
  // Chat state
  const [chats, setChats] = useState(() => {
    const savedChats = localStorage.getItem('patchai-chats');
    return savedChats ? JSON.parse(savedChats) : [];
  });
  const [activeChatId, setActiveChatId] = useState(() => {
    return localStorage.getItem('patchai-active-chat') || null;
  });
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

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
  }, [isMobile]);
  
  // Toggle sidebar collapse (desktop)
  const handleToggleCollapse = useCallback(() => {
    setIsSidebarCollapsed(prev => !prev);
  }, []);

  // Load messages for active chat
  useEffect(() => {
    if (activeChatId) {
      const activeChat = chats.find(chat => chat.id === activeChatId);
      setMessages(activeChat ? activeChat.messages : []);
    } else {
      setMessages([]);
    }
  }, [activeChatId, chats]);

  // Save chats to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('patchai-chats', JSON.stringify(chats));
    if (activeChatId) {
      localStorage.setItem('patchai-active-chat', activeChatId);
    }
  }, [chats, activeChatId]);

  const createNewChat = (firstMessage) => {
    const newChatId = uuidv4();
    const newChat = {
      id: newChatId,
      title: firstMessage.content.length > 30 
        ? `${firstMessage.content.substring(0, 30)}...` 
        : firstMessage.content,
      messages: [firstMessage],
      timestamp: new Date().toISOString(),
      messageCount: 1
    };
    
    setChats(prevChats => [newChat, ...prevChats]);
    setActiveChatId(newChatId);
    return newChatId;
  };

  const updateChat = (chatId, newMessages) => {
    const chatIndex = chats.findIndex(chat => chat.id === chatId);
    if (chatIndex === -1) return;

    const updatedChats = [...chats];
    updatedChats[chatIndex] = {
      ...updatedChats[chatIndex],
      messages: newMessages,
      messageCount: newMessages.length,
      lastMessage: newMessages[newMessages.length - 1]?.content || '',
      timestamp: new Date().toISOString()
    };

    // Move to top of the list
    const [movedChat] = updatedChats.splice(chatIndex, 1);
    updatedChats.unshift(movedChat);
    
    setChats(updatedChats);
  };

  const handleNewChat = () => {
    setActiveChatId(null);
    setMessages([]);
  };

  const handleDeleteChat = (chatId, e) => {
    e.stopPropagation();
    
    setChats(prevChats => {
      const updatedChats = prevChats.filter(chat => chat.id !== chatId);
      
      // If the deleted chat was active, clear the active chat
      if (chatId === activeChatId) {
        setActiveChatId(null);
        setMessages([]);
      }
      
      return updatedChats;
    });
  };

  const handleSelectChat = (chatId) => {
    setActiveChatId(chatId);
  };

  const handleMessageError = (error) => {
    console.error('Error sending message:', error);
    const errorMessage = {
      id: uuidv4(),
      role: 'system',
      content: 'Sorry, there was an error processing your message. Please try again.',
      timestamp: new Date().toISOString(),
      isError: true
    };
    
    if (activeChatId) {
      const updatedMessages = [...messages, errorMessage];
      setMessages(updatedMessages);
      updateChat(activeChatId, updatedMessages);
    }
  };

  const handleSendMessage = async (content) => {
    const userMessage = {
      id: uuidv4(),
      role: 'user',
      content: content,
      timestamp: new Date().toISOString()
    };

    let currentChatId = activeChatId;
    
    // If no active chat, create a new one
    if (!currentChatId) {
      currentChatId = createNewChat(userMessage);
    } else {
      // Update existing chat with new message
      const updatedMessages = [...messages, userMessage];
      setMessages(updatedMessages);
      updateChat(currentChatId, updatedMessages);
    }
    
    setIsLoading(true);

    try {
      // Call the backend API
      const response = await fetch('https://patchai-backend.onrender.com/prompt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [
            ...messages.map(msg => ({
              role: msg.role,
              content: msg.content
            })),
            { role: 'user', content: content }
          ]
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const aiMessage = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toLocaleTimeString()
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      handleMessageError(error);
    } finally {
      setIsLoading(false);
    }
  };





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
      
      {/* Desktop sidebar toggle */}
      <button
        onClick={handleToggleCollapse}
        className="hidden md:block fixed top-4 left-4 z-20 p-2 rounded-md bg-white dark:bg-gray-800 shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        aria-label={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        <FiMenu className="w-6 h-6" />
      </button>
      
      {/* Mobile Sidebar - Hidden by default */}
      <div
        ref={sidebarRef}
        className={`fixed inset-y-0 left-0 flex flex-col transform ${
          showMobileSidebar ? 'translate-x-0' : '-translate-x-full'
        } z-30 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-transform duration-300 ease-in-out`}
      >
        <div className="flex-1 overflow-y-auto">
          <Sidebar
            chatHistory={chats}
            activeChatId={activeChatId}
            onSelectChat={handleSelectChatWrapper}
            onNewChat={handleNewChatWrapper}
            onDeleteChat={handleDeleteChat}
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={handleToggleCollapse}
          />
        </div>
      </div>

      {/* Overlay for mobile */}
      {showMobileSidebar && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-20"
          onClick={toggleMobileSidebar}
        />
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full overflow-hidden pt-14 md:pt-0">
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
