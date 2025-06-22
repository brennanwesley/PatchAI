import React, { useEffect } from 'react';
import { ChatProvider, useChatStore } from './hooks/useChatStore';
import ChatSidebar from './components/ChatSidebar';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';
import StatusCards from './components/StatusCards';
import './App.css';

// Main Chat Layout Component
function ChatLayout() {
  const { createNewChat } = useChatStore();

  // Auto-create new chat on mount
  useEffect(() => {
    createNewChat();
  }, []);

  return (
    <div className="h-screen flex bg-gray-100">
      {/* Left Sidebar - Chat List */}
      <ChatSidebar />
      
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        <ChatWindow />
        <InputBar />
      </div>
      
      {/* Right Sidebar - Status Cards */}
      <StatusCards />
    </div>
  );
}

// Main App Component
function App() {
  return (
    <ChatProvider>
      <ChatLayout />
    </ChatProvider>
  );
}

export default App;
