import React from 'react';
import { formatMessage, createMarkup } from '../utils/formatMessage';

/**
 * MessageBubble component for displaying individual chat messages
 * @param {Object} props
 * @param {string} props.role - 'user' or 'assistant'
 * @param {string} props.content - Message content
 * @param {string} props.timestamp - Optional timestamp
 * @param {boolean} props.isError - Whether this is an error message
 * @param {boolean} props.isRateLimitError - Whether this is a rate limit error
 */
const MessageBubble = ({ role, content, timestamp, isError = false, isRateLimitError = false }) => {
  const isUser = role === 'user';
  const formattedContent = formatMessage(content);

  // Determine styling based on message type
  let bubbleClasses = '';
  let avatarClasses = '';
  let avatarText = '';
  
  if (isError) {
    if (isRateLimitError) {
      bubbleClasses = 'bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 rounded-bl-none';
      avatarClasses = 'bg-red-500';
      avatarText = '🚫';
    } else {
      bubbleClasses = 'bg-yellow-50 dark:bg-yellow-900/20 border-2 border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-200 rounded-bl-none';
      avatarClasses = 'bg-yellow-500';
      avatarText = '⚠️';
    }
  } else if (isUser) {
    bubbleClasses = 'bg-blue-500 text-white rounded-br-none';
    avatarClasses = 'bg-blue-500';
    avatarText = 'U';
  } else {
    bubbleClasses = 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-bl-none';
    avatarClasses = 'bg-green-500';
    avatarText = 'AI';
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${avatarClasses}`}
          >
            {avatarText}
          </div>
        </div>

        {/* Message Content */}
        <div className={`px-4 py-3 rounded-lg shadow-sm ${bubbleClasses}`}>
          {/* Error Banner for Rate Limits */}
          {isRateLimitError && (
            <div className="mb-3 p-2 bg-red-100 dark:bg-red-800/30 rounded border border-red-300 dark:border-red-700">
              <div className="flex items-center">
                <span className="text-red-600 dark:text-red-400 font-semibold text-sm">
                  🚫 RATE LIMIT EXCEEDED
                </span>
              </div>
            </div>
          )}
          
          {/* Message Text */}
          <div
            className={`text-sm leading-relaxed space-y-2 ${
              isError 
                ? (isRateLimitError ? 'text-red-800 dark:text-red-200' : 'text-yellow-800 dark:text-yellow-200')
                : (isUser ? 'text-white' : 'text-gray-900 dark:text-gray-100')
            }`}
            dangerouslySetInnerHTML={createMarkup(formattedContent)}
          />
          
          {/* Timestamp */}
          {timestamp && (
            <div
              className={`text-xs mt-2 opacity-70 ${
                isError 
                  ? (isRateLimitError ? 'text-red-700 dark:text-red-300' : 'text-yellow-700 dark:text-yellow-300')
                  : (isUser ? 'text-blue-100' : 'text-gray-500 dark:text-gray-400')
              }`}
            >
              {new Date(timestamp).toLocaleTimeString()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
