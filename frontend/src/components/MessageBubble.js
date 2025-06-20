import React from 'react';
import { formatMessage, createMarkup } from '../utils/formatMessage';

/**
 * MessageBubble component for displaying individual chat messages
 * @param {Object} props
 * @param {string} props.role - 'user' or 'assistant'
 * @param {string} props.content - Message content
 * @param {string} props.timestamp - Optional timestamp
 */
const MessageBubble = ({ role, content, timestamp }) => {
  const isUser = role === 'user';
  const formattedContent = formatMessage(content);

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${
              isUser 
                ? 'bg-blue-500' 
                : 'bg-green-500'
            }`}
          >
            {isUser ? 'U' : 'Patch'}
          </div>
        </div>

        {/* Message Content */}
        <div
          className={`px-4 py-3 rounded-lg shadow-sm ${
            isUser
              ? 'bg-blue-500 text-white rounded-br-none'
              : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-bl-none'
          }`}
        >
          {/* Message Text */}
          <div
            className={`text-sm leading-relaxed space-y-2 ${
              isUser ? 'text-white' : 'text-gray-900 dark:text-gray-100'
            }`}
            dangerouslySetInnerHTML={createMarkup(formattedContent)}
          />
          
          {/* Timestamp */}
          {timestamp && (
            <div
              className={`text-xs mt-2 opacity-70 ${
                isUser ? 'text-blue-100' : 'text-gray-500 dark:text-gray-400'
              }`}
            >
              {timestamp}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
