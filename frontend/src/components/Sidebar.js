import React, { useState } from 'react';

/**
 * Sidebar component with chat history and new chat functionality
 * @param {Object} props
 * @param {Array} props.chatHistory - Array of past chat objects
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
  onToggleCollapse = () => {}
}) => {
  const [hoveredChatId, setHoveredChatId] = useState(null);

  // Mock chat history if none provided
  const mockChats = chatHistory.length > 0 ? chatHistory : [
    {
      id: '1',
      title: 'How to drill horizontal wells?',
      lastMessage: 'You need a whipstock, a mud motor...',
      timestamp: '2 hours ago',
      messageCount: 8
    },
    {
      id: '2', 
      title: 'Completion design questions',
      lastMessage: 'The perforation strategy depends...',
      timestamp: '1 day ago',
      messageCount: 12
    },
    {
      id: '3',
      title: 'Reservoir modeling help',
      lastMessage: 'For pressure transient analysis...',
      timestamp: '3 days ago',
      messageCount: 6
    },
    {
      id: '4',
      title: 'Production optimization',
      lastMessage: 'Consider implementing ESP...',
      timestamp: '1 week ago',
      messageCount: 15
    }
  ];

  const truncateText = (text, maxLength = 50) => {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  return (
    <>
      {/* Mobile Overlay */}
      {!isCollapsed && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggleCollapse}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed lg:relative inset-y-0 left-0 z-50 lg:z-0
        w-80 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700
        transform transition-transform duration-300 ease-in-out
        ${isCollapsed ? '-translate-x-full lg:translate-x-0' : 'translate-x-0'}
        flex flex-col h-full
      `}>
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              PatchAI
            </h2>
            <button
              onClick={onToggleCollapse}
              className="lg:hidden p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {/* New Chat Button */}
          <button
            onClick={onNewChat}
            className="w-full mt-3 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors duration-200 flex items-center justify-center space-x-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>New Chat</span>
          </button>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="p-2">
            <h3 className="px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Recent Chats
            </h3>
            
            {mockChats.length === 0 ? (
              <div className="px-3 py-8 text-center">
                <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-3">
                  <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  No chats yet
                </p>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                  Start a new conversation
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                {mockChats.map((chat) => (
                  <button
                    key={chat.id}
                    onClick={() => onSelectChat(chat.id)}
                    onMouseEnter={() => setHoveredChatId(chat.id)}
                    onMouseLeave={() => setHoveredChatId(null)}
                    className={`
                      w-full p-3 rounded-lg text-left transition-colors duration-200
                      ${activeChatId === chat.id 
                        ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800' 
                        : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                      }
                    `}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h4 className={`
                          text-sm font-medium truncate
                          ${activeChatId === chat.id 
                            ? 'text-blue-700 dark:text-blue-300' 
                            : 'text-gray-900 dark:text-gray-100'
                          }
                        `}>
                          {truncateText(chat.title, 30)}
                        </h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
                          {truncateText(chat.lastMessage, 40)}
                        </p>
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs text-gray-400 dark:text-gray-500">
                            {chat.timestamp}
                          </span>
                          <span className="text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-1 rounded-full">
                            {chat.messageCount}
                          </span>
                        </div>
                      </div>
                      
                      {/* Options Menu */}
                      {hoveredChatId === chat.id && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            // Handle chat options (delete, rename, etc.)
                          }}
                          className="ml-2 p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
                        >
                          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">U</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                User
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Free Plan
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
