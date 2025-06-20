import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import ChatFeed from './components/ChatFeed';
import ChatInput from './components/ChatInput';
import { v4 as uuidv4 } from 'uuid';
import { FiMenu } from 'react-icons/fi';
import './App.css';

function App() {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);
  const sidebarRef = useRef(null);
  
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

  // Toggle mobile sidebar
  const toggleMobileSidebar = () => {
    setShowMobileSidebar(prev => !prev);
  };

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth >= 768) {
        setShowMobileSidebar(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
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

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden">
      {/* Mobile Header */}
      {isMobile && (
        <div className="md:hidden fixed top-0 left-0 right-0 h-14 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center px-4 z-20">
          <button
            onClick={toggleMobileSidebar}
            className="p-2 rounded-md text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 focus:outline-none"
            aria-label="Toggle sidebar"
          >
            <FiMenu className="w-6 h-6" />
          </button>
          <h1 className="ml-2 text-xl font-semibold text-gray-800 dark:text-white">PatchAI</h1>
        </div>
      )}

      {/* Sidebar - Mobile */}
      <div
        ref={sidebarRef}
        className={`fixed inset-y-0 left-0 transform ${
          isMobile
            ? `${showMobileSidebar ? 'translate-x-0' : '-translate-x-full'}`
            : 'hidden'
        } md:relative md:translate-x-0 md:flex md:flex-shrink-0 z-30 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-transform duration-300 ease-in-out`}
      >
        <Sidebar
          chatHistory={chats}
          activeChatId={activeChatId}
          onSelectChat={(chatId) => {
            handleSelectChat(chatId);
            if (isMobile) setShowMobileSidebar(false);
          }}
          onNewChat={() => {
            handleNewChat();
            if (isMobile) setShowMobileSidebar(false);
          }}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={setIsSidebarCollapsed}
        />
      </div>

      {/* Overlay for mobile */}
      {isMobile && showMobileSidebar && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-20 md:hidden"
          onClick={() => setShowMobileSidebar(false)}
        />
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <div className={`flex-1 overflow-auto ${isMobile ? 'pt-14 pb-24' : 'pb-4'}`}>
          <ChatFeed messages={messages} isLoading={isLoading} />
        </div>
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800">
          <ChatInput onSendMessage={handleSendMessage} isSending={isLoading} />
        </div>
      </div>
    </div>
  );
}

export default App;
