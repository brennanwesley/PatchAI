import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatFeed from './components/ChatFeed';
import ChatInput from './components/ChatInput';
import './App.css';

function App() {
  // Test case messages as requested
  const [messages, setMessages] = useState([
    { role: 'user', content: 'How do I drill a horizontal well?' },
    { 
      role: 'assistant', 
      content: 'You need a whipstock, a mud motor, and directional tools.\n• Start vertical\n• Kickoff point ~4000 ft\n• Maintain 8°–12° per 100 ft' 
    }
  ]);

  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [activeChatId, setActiveChatId] = useState('1');

  const handleSendMessage = (content) => {
    // Add user message
    const userMessage = {
      role: 'user',
      content: content,
      timestamp: new Date().toLocaleTimeString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Simulate AI response (replace with actual API call later)
    setTimeout(() => {
      const aiMessage = {
        role: 'assistant',
        content: `I received your message: "${content}"\n\nThis is a mock response. Here are some key points:\n• Point 1: This demonstrates bullet formatting\n• Point 2: Line breaks work correctly\n• Point 3: Ready for [backend integration](https://github.com/brennanwesley/PatchAI)`,
        timestamp: new Date().toLocaleTimeString()
      };
      
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const handleNewChat = () => {
    setMessages([]);
    setActiveChatId(null);
  };

  const handleSelectChat = (chatId) => {
    setActiveChatId(chatId);
    // In a real app, load messages for this chat
    console.log('Selected chat:', chatId);
  };

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <Sidebar
        activeChatId={activeChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={toggleSidebar}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile Header */}
        <div className="lg:hidden bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
          <div className="flex items-center justify-between">
            <button
              onClick={toggleSidebar}
              className="p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              PatchAI
            </h1>
            <div className="w-10" /> {/* Spacer */}
          </div>
        </div>

        {/* Chat Feed */}
        <ChatFeed
          messages={messages}
          isLoading={isLoading}
          chatTitle="Drilling Operations Chat"
        />

        {/* Chat Input */}
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isLoading}
        />
      </div>
    </div>
  );
}

export default App;
