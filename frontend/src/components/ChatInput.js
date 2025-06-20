import React, { useState, useRef, useEffect } from 'react';
import { getCurrentUser } from '../supabaseClient';
import { FiPaperclip, FiX, FiSend, FiAlertCircle } from 'react-icons/fi';

/**
 * ChatInput component with multi-line textarea support and file attachments
 * @param {Object} props
 * @param {function} props.onSendMessage - Callback when message is sent
 * @param {boolean} props.isLoading - Whether a message is being sent
 * @param {string} props.placeholder - Placeholder text
 * @param {number} props.maxLength - Maximum message length (default: 2000)
 */
const ChatInput = ({ 
  onSendMessage, 
  isLoading = false,
  placeholder = "Message PatchAI...",
  maxLength = 2000
}) => {
  const [message, setMessage] = useState('');
  const [files, setFiles] = useState([]);
  const [error, setError] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const user = await getCurrentUser();
        setIsAuthenticated(!!user);
      } catch (err) {
        console.error('Auth check failed:', err);
        setIsAuthenticated(false);
      }
    };
    checkAuth();
  }, []);

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  }, [message]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!isAuthenticated) {
      setError('Please sign in to send messages');
      return;
    }

    const trimmedMessage = message.trim();
    if (!trimmedMessage && files.length === 0) return;
    
    try {
      await onSendMessage({
        content: trimmedMessage,
        files: files.map(file => ({
          name: file.name,
          type: file.type,
          size: file.size,
          data: file // Will be processed by the parent
        }))
      });
      
      // Reset form
      setMessage('');
      setFiles([]);
      setError(null);
    } catch (err) {
      console.error('Failed to send message:', err);
      setError(err.message || 'Failed to send message');
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift), new line on Shift+Enter
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
    // Also allow Cmd+Enter or Ctrl+Enter for submission
    else if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleChange = (e) => {
    if (e.target.value.length <= maxLength) {
      setMessage(e.target.value);
    }
  };

  const handleFileChange = (e) => {
    const newFiles = Array.from(e.target.files);
    // Check total size (max 10MB)
    const totalSize = [...files, ...newFiles].reduce((acc, file) => acc + file.size, 0);
    if (totalSize > 10 * 1024 * 1024) {
      setError('Total file size must be less than 10MB');
      return;
    }
    setFiles(prev => [...prev, ...newFiles]);
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  // Calculate remaining characters
  const remainingChars = maxLength - message.length;
  const isNearLimit = remainingChars < 100;
  const isOverLimit = remainingChars < 0;
  const isDisabled = isLoading || !isAuthenticated || (message.trim() === '' && files.length === 0) || isOverLimit;

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-t border-gray-200/50 dark:border-gray-700/50 px-4 py-3 md:py-4 md:px-6">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
        {/* File previews */}
        {files.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-2 max-h-32 overflow-y-auto">
            {files.map((file, index) => (
              <div 
                key={index}
                className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg px-3 py-2 text-sm"
              >
                <span className="truncate max-w-xs">
                  {file.name} ({(file.size / 1024).toFixed(1)} KB)
                </span>
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="ml-2 text-gray-500 hover:text-red-500"
                  aria-label="Remove file"
                >
                  <FiX className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="flex items-center text-red-500 dark:text-red-400 text-sm mb-2 px-2">
            <FiAlertCircle className="mr-1.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex items-end space-x-2">
          {/* File upload button */}
          <div className="relative">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading || !isAuthenticated}
              className="p-2 rounded-full text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Attach files"
            >
              <FiPaperclip className="w-5 h-5" />
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
              multiple
              disabled={isLoading || !isAuthenticated}
            />
          </div>

          {/* Message input */}
          <div className="flex-1 relative bg-white dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-gray-600 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              placeholder={isAuthenticated ? placeholder : 'Please sign in to chat'}
              disabled={isLoading || !isAuthenticated}
              rows="1"
              className="w-full px-4 py-3 pr-12 text-gray-900 dark:text-white bg-transparent border-0 focus:ring-0 resize-none overflow-hidden text-sm md:text-base"
              style={{ minHeight: '44px', maxHeight: '200px' }}
            />
            
            {/* Character counter */}
            {isNearLimit && (
              <div className={`absolute right-2 bottom-1 text-xs ${
                isOverLimit ? 'text-red-500' : 'text-gray-400 dark:text-gray-500'
              }`}>
                {remainingChars}
              </div>
            )}
          </div>

          {/* Send button */}
          <button
            type="submit"
            disabled={isDisabled}
            className={`p-2.5 rounded-full flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors ${
              isDisabled
                ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-600 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
            aria-label="Send message"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <FiSend className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Help text */}
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
          {isAuthenticated ? (
            <>
              Press {navigator.platform.includes('Mac') ? '⌘' : 'Ctrl'}+Enter to send • 
              {files.length > 0 ? `${files.length} file${files.length > 1 ? 's' : ''} attached • ` : ''}
              Patch can make mistakes, please verify important information.
            </>
          ) : (
            'Please sign in to start chatting with PatchAI'
          )}
        </div>
      </form>
    </div>
  );
};

export default ChatInput;
