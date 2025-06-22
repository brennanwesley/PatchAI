import React from 'react';
import { ChatProvider, useChatStore } from './hooks/useChatStore';
import { useMobileLayout } from './hooks/useMobileLayout';
import { useSubscription } from './hooks/useSubscription';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { paywallEvents, PAYWALL_EVENTS } from './utils/paywallEvents';
import ChatSidebar from './components/ChatSidebar';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';
import StatusCards from './components/StatusCards';
import MobileHeader from './components/MobileHeader';
import BackendTest from './components/BackendTest';
import Paywall from './components/Paywall';
import SubscriptionStatus from './components/SubscriptionStatus';
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
  const { isMobile, sidebarOpen, toggleSidebar, closeSidebar } = useMobileLayout();
  const { needsPayment, hasActiveSubscription, loading: subscriptionLoading, refetch: refetchSubscription } = useSubscription();
  const { user } = useAuth();
  const [showPaywall, setShowPaywall] = React.useState(false);

  // Check for payment success in URL and refresh subscription
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const paymentStatus = urlParams.get('payment');
    
    if (paymentStatus === 'success') {
      console.log('💳 Payment success detected, refreshing subscription status...');
      // Clear the URL parameter
      window.history.replaceState({}, document.title, window.location.pathname);
      
      // Hide paywall immediately for better UX
      setShowPaywall(false);
      
      // Retry subscription refresh with exponential backoff
      const retrySubscriptionRefresh = async (attempt = 1, maxAttempts = 5) => {
        try {
          console.log(`🔄 Refreshing subscription status (attempt ${attempt}/${maxAttempts})...`);
          await refetchSubscription();
          
          // Check if subscription is now active
          if (hasActiveSubscription) {
            console.log('✅ Subscription status confirmed active');
            return;
          }
          
          // If not active yet and we have more attempts, retry
          if (attempt < maxAttempts) {
            const delay = Math.min(1000 * Math.pow(2, attempt), 10000); // Exponential backoff, max 10s
            console.log(`⏳ Subscription not active yet, retrying in ${delay}ms...`);
            setTimeout(() => retrySubscriptionRefresh(attempt + 1, maxAttempts), delay);
          } else {
            console.warn('⚠️ Subscription sync may be delayed. Please refresh the page if paywall persists.');
          }
        } catch (error) {
          console.error('❌ Error refreshing subscription:', error);
          if (attempt < maxAttempts) {
            const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
            setTimeout(() => retrySubscriptionRefresh(attempt + 1, maxAttempts), delay);
          }
        }
      };
      
      // Start the retry process after a small initial delay
      setTimeout(() => retrySubscriptionRefresh(), 1000);
    }
  }, [refetchSubscription, hasActiveSubscription]);

  // Show paywall if user needs payment (but not if we just processed a successful payment)
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const paymentStatus = urlParams.get('payment');
    
    if (user && !subscriptionLoading && needsPayment && paymentStatus !== 'success') {
      setShowPaywall(true);
    } else if (hasActiveSubscription) {
      setShowPaywall(false);
    }
  }, [user, subscriptionLoading, needsPayment, hasActiveSubscription]);

  // Listen for paywall events (402 errors)
  React.useEffect(() => {
    const unsubscribe = paywallEvents.subscribe((eventType, data) => {
      if (eventType === PAYWALL_EVENTS.PAYMENT_REQUIRED) {
        console.log('💳 App: Payment required event received, showing paywall');
        setShowPaywall(true);
      }
    });

    return unsubscribe;
  }, []);

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

  if (isMobile) {
    // Mobile Layout
    return (
      <div className="h-screen flex flex-col bg-gray-100">
        {/* Mobile Header with Hamburger */}
        <MobileHeader onToggleSidebar={toggleSidebar} />
        
        {/* Mobile Sidebar (Overlay) */}
        <ChatSidebar 
          isOpen={sidebarOpen} 
          onClose={closeSidebar} 
          isMobile={true} 
        />
        
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          <ChatWindow />
          <InputBar />
        </div>

        {/* Paywall Modal */}
        {showPaywall && (
          <Paywall onClose={() => setShowPaywall(false)} />
        )}
      </div>
    );
  }

  // Desktop Layout
  return (
    <div className="h-screen flex bg-gray-100 overflow-hidden">
      {/* Left Sidebar - Chat List */}
      <ChatSidebar 
        isOpen={true} 
        onClose={() => {}} 
        isMobile={false} 
      />
      
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-0">
        <ChatWindow />
        <InputBar />
      </div>
      
      {/* Right Sidebar - Status Cards (Desktop Only) */}
      <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
        {/* Subscription Status at top */}
        <div className="p-4 border-b border-gray-200">
          <SubscriptionStatus />
        </div>
        
        {/* Status Cards below */}
        <div className="flex-1 overflow-y-auto">
          <StatusCards />
        </div>
      </div>

      {/* Paywall Modal */}
      {showPaywall && (
        <Paywall onClose={() => setShowPaywall(false)} />
      )}
    </div>
  );
}

// Main App Component
function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ChatProvider>
          <ChatLayout />
        </ChatProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
