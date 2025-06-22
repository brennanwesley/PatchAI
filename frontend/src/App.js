import React, { useEffect } from 'react';
import { ChatProvider, useChatStore } from './hooks/useChatStore';
import ChatSidebar from './components/ChatSidebar';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';
import StatusCards from './components/StatusCards';
import BackendTest from './components/BackendTest';
import './App.css';

// Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('App Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-screen flex items-center justify-center bg-gray-100">
          <div className="text-center p-8 bg-white rounded-lg shadow-lg max-w-md">
            <h2 className="text-xl font-bold text-red-600 mb-4">Something went wrong</h2>
            <p className="text-gray-600 mb-4">
              The chat interface encountered an error. Please refresh the page to try again.
            </p>
            <button 
              onClick={() => window.location.reload()} 
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Check if test mode is enabled via URL parameter
const isTestMode = () => {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('test') === 'backend';
};

// Main Chat Layout Component
function ChatLayout() {
  const { chats, isLoading, error } = useChatStore();

  // Show backend test if test mode is enabled
  if (isTestMode()) {
    return (
      <div className="min-h-screen bg-gray-100 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6 text-center">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">PatchAI Backend Integration Test</h1>
            <p className="text-gray-600">
              Testing all API endpoints and authentication. 
              <a href="/" className="text-blue-500 hover:underline ml-2">← Back to Chat</a>
            </p>
          </div>
          <BackendTest />
        </div>
      </div>
    );
  }

  // Show loading state while initializing
  if (isLoading && chats.length === 0) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading chat interface...</p>
        </div>
      </div>
    );
  }

  // Show error state if there's a critical error
  if (error && chats.length === 0) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center p-8 bg-white rounded-lg shadow-lg max-w-md">
          <h2 className="text-xl font-bold text-red-600 mb-4">Connection Error</h2>
          <p className="text-gray-600 mb-4">
            Unable to connect to the chat service. Please check your internet connection and try again.
          </p>
          <p className="text-sm text-gray-500 mb-4">Error: {error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

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
    <ErrorBoundary>
      <ChatProvider>
        <ChatLayout />
      </ChatProvider>
    </ErrorBoundary>
  );
}

export default App;
