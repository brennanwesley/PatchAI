import { render, screen } from '@testing-library/react';
import App from './App';

jest.mock('./hooks/useChatStore', () => ({
  ChatProvider: ({ children }) => children,
  useChatStore: () => ({
    chats: [{ id: 'chat-1' }],
    isLoading: false,
    error: null,
  }),
}));

jest.mock('./hooks/useMobileLayout', () => ({
  useMobileLayout: () => ({
    isMobile: false,
    sidebarOpen: false,
    toggleSidebar: jest.fn(),
    closeSidebar: jest.fn(),
  }),
}));

jest.mock('./hooks/useSubscription', () => ({
  useSubscription: () => ({
    needsPayment: false,
    hasActiveSubscription: true,
    loading: false,
    refetch: jest.fn(),
  }),
}));

jest.mock('./contexts/AuthContext', () => ({
  AuthProvider: ({ children }) => children,
  useAuth: () => ({
    user: { id: 'user-1' },
  }),
}));

jest.mock('./utils/paywallEvents', () => ({
  PAYWALL_EVENTS: {
    PAYMENT_REQUIRED: 'PAYMENT_REQUIRED',
  },
  paywallEvents: {
    subscribe: jest.fn(() => jest.fn()),
  },
}));

jest.mock('./components/ChatSidebar', () => function MockChatSidebar() {
  return <div>Chat Sidebar</div>;
});

jest.mock('./components/ChatWindow', () => function MockChatWindow() {
  return <div>Chat Window</div>;
});

jest.mock('./components/InputBar', () => function MockInputBar() {
  return <div>Input Bar</div>;
});

jest.mock('./components/StatusCards', () => function MockStatusCards() {
  return <div>Status Cards</div>;
});

jest.mock('./components/MobileHeader', () => function MockMobileHeader() {
  return <div>Mobile Header</div>;
});

jest.mock('./components/BackendTest', () => function MockBackendTest() {
  return <div>Backend Test</div>;
});

jest.mock('./components/Paywall', () => function MockPaywall() {
  return <div>Paywall</div>;
});

jest.mock('./components/SubscriptionStatus', () => function MockSubscriptionStatus() {
  return <div>Subscription Status</div>;
});

test('renders the desktop app shell', () => {
  render(<App />);

  expect(screen.getByText('Chat Sidebar')).toBeInTheDocument();
  expect(screen.getByText('Chat Window')).toBeInTheDocument();
  expect(screen.getByText('Input Bar')).toBeInTheDocument();
  expect(screen.getByText('Status Cards')).toBeInTheDocument();
  expect(screen.getByText('Subscription Status')).toBeInTheDocument();
});
