import React, { useState, useMemo } from 'react';
import ReactDOM from 'react-dom';
import { formatDistanceToNow } from 'date-fns';
import { FiLogOut, FiUser } from 'react-icons/fi';
import PropTypes from 'prop-types';
import Profile from './Profile';

const MAX_TITLE_LENGTH = 30;
const MAX_MESSAGE_PREVIEW = 40;

/**
 * Get initials from a name string
 */
const getInitials = (name) => {
  if (!name) return 'U';
  return name
    .split(' ')
    .map(word => word.charAt(0))
    .join('')
    .toUpperCase()
    .substring(0, 2);
};

/**
 * Sidebar component for displaying chat history and navigation
 */
const Sidebar = ({
  chatHistory = [],
  activeChatId = null,
  onSelectChat = () => {},
  onNewChat = () => {},
  onDeleteChat = () => {},
  onLogOut = () => {}, 
  isCollapsed = false,
  onToggleCollapse = () => {}
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [hoveredChatId, setHoveredChatId] = useState(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  // Debug function to handle profile modal opening
  const handleProfileOpen = () => {
    console.log('🔍 Profile modal button clicked');
    console.log('🔍 Current isProfileOpen state:', isProfileOpen);
    setIsProfileOpen(true);
    console.log('🔍 Profile modal state set to true');
  };

  // Debug function to handle profile modal closing
  const handleProfileClose = () => {
    console.log('🔍 Profile modal close requested');
    setIsProfileOpen(false);
    console.log('🔍 Profile modal state set to false');
  };

  // Format chat title with ellipsis if too long
  const formatTitle = (title) => {
    if (!title) return 'New Chat';
    return title.length > MAX_TITLE_LENGTH 
      ? `${title.substring(0, MAX_TITLE_LENGTH)}...`
      : title;
  };
  
  // Truncate message preview text
  const truncateText = (text, maxLength = MAX_MESSAGE_PREVIEW) => {
    if (!text) return '';
    return text.length > maxLength 
      ? `${text.substring(0, maxLength)}...`
      : text;
  };
  
  // Format chat timestamps and prepare chat data
  const formattedChats = useMemo(() => {
    return chatHistory.map(chat => ({
      ...chat,
      formattedTime: chat.timestamp 
        ? formatDistanceToNow(new Date(chat.timestamp), { addSuffix: true })
        : 'Just now',
      lastMessage: chat.messages?.length > 0 
        ? chat.messages[chat.messages.length - 1].content 
        : 'No messages yet',
      messageCount: chat.messages?.length || 0
    }));
  }, [chatHistory]);

  // Filter chats based on search query
  const filteredChats = useMemo(() => {
    if (!searchQuery.trim()) return formattedChats;
    const query = searchQuery.toLowerCase();
    return formattedChats.filter(chat => {
      const title = chat.title || '';
      const lastMessage = chat.lastMessage || '';
      return (
        title.toLowerCase().includes(query) || 
        lastMessage.toLowerCase().includes(query)
      );
    });
  }, [formattedChats, searchQuery]);

  return (
    <div className={`h-full flex flex-col bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 ${
      isCollapsed ? 'w-16' : 'w-64'
    } transition-all duration-300 relative`}>
      <div className="flex-1 flex flex-col min-h-0">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        {!isCollapsed ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
                Chat History
              </h2>
              <button
                onClick={onToggleCollapse}
                className="md:hidden p-1 rounded-md text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
                aria-label="Collapse sidebar"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7M5 5l7 7-7 7" />
                </svg>
              </button>
            </div>
      
            {/* Search and New Chat Button */}
            <div className="space-y-2">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search chats..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
              </div>
              <button
                onClick={onNewChat}
                className="w-full flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg className="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
                </svg>
                New Chat
              </button>
            </div>
          </div>
        ) : (
          <div className="flex justify-center">
            <button
              onClick={onToggleCollapse}
              className="p-1 rounded-md text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
              aria-label="Expand sidebar"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        )}
      </div>
      
        {/* Chat List */}
        <div className="flex-1 overflow-y-auto py-2">
          {filteredChats.length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
              {searchQuery ? 'No matching chats found' : 'No chats yet'}
              {!searchQuery && (
                <button
                  onClick={onNewChat}
                  className="mt-2 block mx-auto text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  Start a new chat
                </button>
              )}
            </div>
          ) : (
            <ul className="space-y-1">
              {filteredChats.map((chat) => (
                <li key={chat.id}>
                  <button
                    onClick={() => onSelectChat(chat.id)}
                    onMouseEnter={() => setHoveredChatId(chat.id)}
                    onMouseLeave={() => setHoveredChatId(null)}
                    className={`w-full text-left px-4 py-3 flex items-center ${
                      activeChatId === chat.id
                        ? 'bg-blue-100 dark:bg-gray-700 text-blue-700 dark:text-white'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-blue-600 dark:text-blue-300 font-medium mr-3">
                      {getInitials(chat.title)}
                    </div>
                    {!isCollapsed && (
                      <div className="flex-1 min-w-0">
                        <p className="truncate font-medium">
                          {formatTitle(chat.title)}
                        </p>
                        <div className="flex items-center mt-1">
                          <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                            {truncateText(chat.lastMessage)}
                          </p>
                          <span className="mx-2 text-gray-300 dark:text-gray-600">•</span>
                          <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                            {chat.formattedTime}
                          </span>
                        </div>
                      </div>
                    )}
                    {hoveredChatId === chat.id && !isCollapsed && (
                      <button
                        onClick={(e) => onDeleteChat(chat.id, e)}
                        className="ml-2 p-1 text-gray-400 hover:text-red-500 transition-colors"
                        aria-label="Delete chat"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      
        {/* Desktop User Info - Stays at bottom */}
        <div className="hidden md:block p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 mt-auto">
          {/* Clickable User Info Section */}
          <button
            onClick={handleProfileOpen}
            className="w-full flex items-center mb-3 p-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            <div className="flex-shrink-0">
              <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-blue-600 dark:text-blue-300 font-medium">
                {getInitials(localStorage.getItem('customer_name') || 'User')}
              </div>
            </div>
            <div className="ml-3 overflow-hidden text-left">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-200 truncate">
                {localStorage.getItem('customer_name') || 'User'}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                {localStorage.getItem('userEmail') || 'user@example.com'}
              </p>
            </div>
          </button>
          
          {/* Log Out Button */}
          <button
            onClick={onLogOut}
            className="w-full flex items-center px-3 py-2 text-sm text-gray-600 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
          >
            <FiLogOut className="w-4 h-4 mr-3" />
            <span>Log Out</span>
          </button>
        </div>
        
        {/* Mobile User Info - Stays at bottom */}
        <div className="md:hidden p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 mt-auto">
          {!isCollapsed ? (
            <div>
              {/* Clickable User Info Section */}
              <button
                onClick={handleProfileOpen}
                className="w-full flex items-center mb-3 p-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-blue-600 dark:text-blue-300 font-medium">
                    {getInitials(localStorage.getItem('customer_name') || 'User')}
                  </div>
                </div>
                <div className="ml-3 overflow-hidden text-left">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-200 truncate">
                    {localStorage.getItem('customer_name') || 'User'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {localStorage.getItem('userEmail') || 'user@example.com'}
                  </p>
                </div>
              </button>
              
              {/* Mobile Log Out Button */}
              <button
                onClick={onLogOut}
                className="w-full flex items-center px-3 py-2 text-sm text-gray-600 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
              >
                <FiLogOut className="w-4 h-4 mr-3" />
                <span>Log Out</span>
              </button>
            </div>
          ) : (
            <button
              onClick={handleProfileOpen}
              className="flex justify-center p-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-blue-600 dark:text-blue-300 font-medium">
                {getInitials(localStorage.getItem('customer_name') || 'U')}
              </div>
            </button>
          )}
        </div>
        
        {/* Profile Modal */}
        {isProfileOpen && ReactDOM.createPortal(
          <Profile
            isOpen={isProfileOpen}
            onClose={handleProfileClose}
          />,
          document.body
        )}
      </div>
    </div>
  );
};

Sidebar.propTypes = {
  chatHistory: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      title: PropTypes.string,
      messages: PropTypes.array,
      timestamp: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
        PropTypes.instanceOf(Date)
      ])
    })
  ),
  activeChatId: PropTypes.string,
  onSelectChat: PropTypes.func,
  onNewChat: PropTypes.func,
  onDeleteChat: PropTypes.func,
  onLogOut: PropTypes.func, 
  isCollapsed: PropTypes.bool,
  onToggleCollapse: PropTypes.func
};

export default Sidebar;
