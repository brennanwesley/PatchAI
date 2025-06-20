import React, { useState, useMemo, useEffect } from 'react';
import { formatDistanceToNow } from 'date-fns';
import PropTypes from 'prop-types';

/**
 * Sidebar component with chat history and new chat functionality
 * @param {Object} props
 * @param {Array} props.chatHistory - Array of chat objects
 * @param {string} props.activeChatId - ID of currently active chat
 * @param {function} props.onSelectChat - Callback when a chat is selected
 * @param {function} props.onNewChat - Callback when new chat is created
 * @param {boolean} props.isCollapsed - Whether sidebar is collapsed (mobile)
 * @param {function} props.onToggleCollapse - Toggle sidebar collapse
 */
const Sidebar = ({ 
  chatHistory = [], 
  activeChatId = null,
  onSelectChat = () => {},
  onNewChat = () => {},
  isCollapsed = false,
  onToggleCollapse
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [hoveredChatId, setHoveredChatId] = useState(null);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  // Handle window resize for mobile detection
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Format chat timestamps
  const formattedChats = useMemo(() => {
    return chatHistory.map(chat => {
      const messages = chat.messages || [];
      const lastMessage = messages.length > 0 ? messages[messages.length - 1].content : 'No messages yet';
      const timestamp = chat.timestamp ? new Date(chat.timestamp) : null;
      
      return {
        ...chat,
        formattedTime: timestamp 
          ? formatDistanceToNow(timestamp, { addSuffix: true })
          : 'Just now',
        lastMessage,
        messageCount: messages.length
      };
    });
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

  const truncateText = (text, maxLength = 50) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };
  
  // Get first letter of title or return '?'
  const getInitial = (title) => {
    if (!title || typeof title !== 'string') return '?';
    return title.charAt(0).toUpperCase();
  };

  return (
    <div 
      className={`h-full flex flex-col bg-white dark:bg-gray-800 transition-all duration-300 ease-in-out ${
        isCollapsed && !isMobile ? 'w-16' : 'w-full md:w-64'
      }`}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
              <h2 className={`font-semibold text-gray-800 dark:text-white ${isCollapsed ? 'hidden' : 'block'}`}>
                Chat History
              </h2>
              <button
                onClick={onToggleCollapse}
                className="p-1 rounded-md text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700 focus:outline-none"
                aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              >
                {isCollapsed ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                  </svg>
                )}
              </button>
            </div>
          )}
        
          {/* Search and New Chat Button */}
          {!isCollapsed && (
            <div className="mt-4 space-y-2">
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
              <div className="p-4">
                <button
                  onClick={onNewChat}
                  className={`w-full flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                    isCollapsed && !isMobile ? 'p-2' : ''
                  }`}
                >
                  <svg className={`${isCollapsed && !isMobile ? 'h-5 w-5' : '-ml-1 mr-2 h-5 w-5'}`} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
                  </svg>
                  {(!isCollapsed || isMobile) && 'New Chat'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto">
        {isCollapsed ? (
          <div className="py-2">
            <button
              onClick={onNewChat}
              className="w-full flex items-center justify-center p-3 text-gray-600 hover:text-blue-600 dark:text-gray-300 dark:hover:text-blue-400"
              title="New Chat"
              aria-label="New Chat"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredChats.length > 0 ? (
              filteredChats.map((chat) => (
                <li 
                  key={chat.id}
                  className={`px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer ${
                    activeChatId === chat.id ? 'bg-blue-50 dark:bg-gray-700' : ''
                  }`}
                  onClick={() => onSelectChat(chat.id)}
                  onMouseEnter={() => setHoveredChatId(chat.id)}
                  onMouseLeave={() => setHoveredChatId(null)}
                >
                  <div className="flex items-start">
                    <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-blue-600 dark:text-blue-300 font-medium">
                      {getInitial(chat.title)}
                    </div>
                    <div className="ml-3 flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {chat.title || 'New Chat'}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {truncateText(chat.lastMessage || 'No messages yet', 30)}
                      </p>
                    </div>
                    <div className="ml-2 flex flex-col items-end">
                      <span className="text-xs text-gray-400 dark:text-gray-500">
                        {chat.formattedTime || 'Just now'}
                      </span>
                      {chat.messageCount > 0 && (
                        <span className="mt-1 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                          {chat.messageCount}
                        </span>
                      )}
                    </div>
                  </div>
                </li>
              ))
            ) : (
              <li className="px-4 py-8 text-center">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {searchQuery ? 'No matching chats found' : 'No chats yet'}
                </p>
                <button
                  onClick={searchQuery ? () => setSearchQuery('') : onNewChat}
                  className="mt-2 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  {searchQuery ? 'Clear search' : 'Start a new chat'}
                </button>
              </li>
            )}
          </ul>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        {!isCollapsed ? (
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 rounded-full bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
                  {localStorage.getItem('userInitials') || 'U'}
                </span>
              </div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-200">
                {localStorage.getItem('userName') || 'User'}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {localStorage.getItem('userEmail') || 'user@example.com'}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex justify-center">
            <div className="h-8 w-8 rounded-full bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
                {(localStorage.getItem('userInitials') || 'U').charAt(0)}
              </span>
            </div>
          </div>
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
  isCollapsed: PropTypes.bool,
  onToggleCollapse: PropTypes.func
};

Sidebar.defaultProps = {
  chatHistory: [],
  activeChatId: null,
  onSelectChat: () => {},
  onNewChat: () => {},
  isCollapsed: false,
  onToggleCollapse: () => {}
};

export default Sidebar;
