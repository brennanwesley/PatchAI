import React from 'react';
import ReactDOM from 'react-dom';
import { useChatStore } from '../hooks/useChatStore';
import { useAuth } from '../contexts/AuthContext';
import ChatItem from './ChatItem';
import Profile from './Profile';

export default function ChatSidebar({ isOpen, onClose, isMobile }) {
  const { chats, activeChat, createNewChat, selectChat, updateChatTitle, deleteChat, isLoading } = useChatStore();
  const { user, signOut } = useAuth();

  // Safety check to ensure chats is always an array
  const safeChats = Array.isArray(chats) ? chats : [];

  const handleNewChat = async () => {
    await createNewChat();
    // Auto-close sidebar on mobile after creating new chat
    if (isMobile && onClose) {
      onClose();
    }
  };

  const handleSelectChat = (chat) => {
    selectChat(chat);
    // Auto-close sidebar on mobile after selecting chat
    if (isMobile && onClose) {
      onClose();
    }
  };

  const formatDate = (dateString) => {
    // Validate input - handle null, undefined, or empty strings
    if (!dateString) {
      return 'Unknown';
    }
    
    const date = new Date(dateString);
    
    // Check if the date is valid
    if (isNaN(date.getTime())) {
      return 'Unknown';
    }
    
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  // Profile modal state
  const [isProfileOpen, setIsProfileOpen] = React.useState(false);

  // Helper function to get user initials
  const getInitials = (name) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .substring(0, 2);
  };

  // Profile modal handlers
  const handleProfileOpen = () => {
    console.log('🔍 Profile modal opened from ChatSidebar');
    setIsProfileOpen(true);
  };

  const handleProfileClose = () => {
    console.log('🔍 Profile modal closed from ChatSidebar');
    setIsProfileOpen(false);
  };

  // Mobile overlay backdrop
  const backdrop = isMobile && isOpen && (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
      onClick={onClose}
      aria-hidden="true"
    />
  );

  // Sidebar classes for responsive behavior
  const sidebarClasses = isMobile 
    ? `fixed left-0 top-0 h-full w-80 bg-gray-50 border-r border-gray-200 z-50 transform transition-transform duration-300 ease-in-out ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      } md:relative md:translate-x-0 md:z-auto`
    : 'w-80 bg-gray-50 border-r border-gray-200 flex flex-col h-full';

  return (
    <>
      {backdrop}
      <div className={sidebarClasses}>
        {/* Mobile Close Button */}
        {isMobile && (
          <div className="md:hidden p-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">Chats</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              aria-label="Close sidebar"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={handleNewChat}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Chat
          </button>
        </div>

        {/* Chat List */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-sm">Loading chats...</p>
            </div>
          ) : safeChats.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <p className="text-sm">No chats yet</p>
              <p className="text-xs text-gray-400 mt-1">Start a new conversation!</p>
            </div>
          ) : (
            <div className="p-2">
              {safeChats.map((chat) => (
                <ChatItem
                  key={chat.id}
                  chat={chat}
                  isActive={activeChat?.id === chat.id}
                  onSelect={handleSelectChat}
                  onEdit={updateChatTitle}
                  onDelete={deleteChat}
                  formatDate={formatDate}
                />
              ))}
            </div>
          )}
        </div>

        {/* User Info Section */}
        <div className="p-4 border-t border-gray-200">
          {/* Clickable User Info */}
          <button
            onClick={handleProfileOpen}
            className="w-full flex items-center gap-3 p-2 rounded-md hover:bg-gray-50 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-medium">
                {getInitials(user?.email) || 'U'}
              </span>
            </div>
            <div className="flex-1 min-w-0 text-left">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user?.email || 'User'}
              </p>
              <p className="text-xs text-gray-500">
                Click to view profile
              </p>
            </div>
          </button>
          
          {/* Sign Out Button */}
          <button
            onClick={signOut}
            className="w-full mt-2 flex items-center gap-3 p-2 text-gray-500 hover:text-red-600 hover:bg-gray-50 rounded-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
            title="Sign out"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span className="text-sm">Sign Out</span>
          </button>
        </div>
      </div>
      {isProfileOpen && ReactDOM.createPortal(
        <Profile
          isOpen={isProfileOpen}
          onClose={handleProfileClose}
        />,
        document.body
      )}
    </>
  );
}
