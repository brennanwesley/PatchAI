import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ChatProvider, useChatStore } from './hooks/useChatStore';
import Login from './components/Login';
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

// Protected Route Component
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading PatchAI...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  return (
    <ChatProvider>
      {children}
    </ChatProvider>
  );
}

// Main App Component
function App() {
  return (
    <AuthProvider>
      <div className="App">
        <Routes>
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <Navigate to="/chat" replace />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/chat" 
            element={
              <ProtectedRoute>
                <ChatLayout />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/chat/:chatId" 
            element={
              <ProtectedRoute>
                <ChatLayout />
              </ProtectedRoute>
            } 
          />
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Routes>
      </div>
    </AuthProvider>
  );
}

export default App;
