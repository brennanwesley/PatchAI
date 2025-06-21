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
    if (!trimmedMessage && files.length === 0) {
      setError('Please enter a message or attach a file');
      return;
    }
    
    try {
      // Prepare the message object
      const messageData = {
        content: trimmedMessage,
        files: files.map(file => ({
          name: file.name,
          type: file.type,
          size: file.size,
          data: file // Will be processed by the parent
        }))
      };
      
      console.log('📤 Sending message:', { 
        content: trimmedMessage, 
        fileCount: files.length,
        hasContent: !!trimmedMessage
      });
      
      // Clear error state before sending
      setError(null);
      
      // Call the parent's send handler
      await onSendMessage(trimmedMessage ? messageData : { files: messageData.files });
      
      // Reset form only if the message was sent successfully
      setMessage('');
      setFiles([]);
      
    } catch (err) {
      console.error('❌ Failed to send message:', err);
      // Show a user-friendly error message
      const errorMessage = err.message || 'Failed to send message';
      setError(errorMessage);
      
      // Auto-hide error after 5 seconds
      const errorTimer = setTimeout(() => {
        setError(null);
      }, 5000);
      
      // Cleanup timer on component unmount
      return () => clearTimeout(errorTimer);
    }
  };

  const handleKeyDown = (e) => {
    // Don't submit if the user is selecting text with shift key
    if (e.shiftKey && e.key === 'Enter') {
      // Allow Shift+Enter for new lines
      return;
    }
    
    // Submit on Enter (without Shift) or Cmd+Enter/Ctrl+Enter
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      
      // Don't submit if the message is empty and there are no files
      if (!message.trim() && files.length === 0) {
        return;
      }
      
      // Only submit if not already loading
      if (!isLoading) {
        handleSubmit(e);
      }
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
  
  // Get disabled reason for tooltip
  const getDisabledReason = () => {
    if (!isAuthenticated) return 'Please sign in to send messages';
    if (isLoading) return 'Sending message...';
    if (isOverLimit) return `Message too long (max ${maxLength} characters)`;
    if (message.trim() === '' && files.length === 0) return 'Enter a message or attach a file';
    return '';
  };
  
  const disabledReason = isDisabled ? getDisabledReason() : '';

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
          <div className="relative">
            <button
              type="button"
              onClick={() => fileInputRef.current && fileInputRef.current.click()}
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

            {isNearLimit && (
              <div className={`absolute right-2 bottom-1 text-xs ${isOverLimit ? 'text-red-500' : 'text-gray-400 dark:text-gray-500'}`}>
                {remainingChars}
              </div>
            )}
          </div>

          <div className="relative group">
            <button
              type="submit"
              disabled={isDisabled}
              className={`p-2.5 rounded-full flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors ${isDisabled ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-600 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white'}`}
              aria-label={isDisabled ? disabledReason : 'Send message'}
              data-tooltip={disabledReason}
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <FiSend className="w-5 h-5" />
              )}
            </button>

            {isDisabled && disabledReason && (
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-xs text-white bg-gray-800 dark:bg-gray-700 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                {disabledReason}
              </div>
            )}
          </div>
        </div>

        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
          {isAuthenticated ? (
            <span>
              Press{' '}
              <kbd className="px-1.5 py-0.5 text-xs font-semibold text-gray-800 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded">
                Enter
              </kbd>{' '}
              to send,{' '}
              <kbd className="px-1.5 py-0.5 text-xs font-semibold text-gray-800 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded">
                Shift+Enter
              </kbd>{' '}
              for new line
            </span>
          ) : (
            <span>Please sign in to start chatting</span>
          )}
        </div>
      </form>
    </div>
  );
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
<div className="relative group">
<button
type="submit"
disabled={isDisabled}
className={`p-2.5 rounded-full flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors ${
isDisabled
? 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-600 cursor-not-allowed'
: 'bg-blue-600 hover:bg-blue-700 text-white'
}`}
aria-label={isDisabled ? disabledReason : 'Send message'}
data-tooltip={disabledReason}
>
{isLoading ? (
<div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
) : (
<FiSend className="w-5 h-5" />
)}
</button>

{/* Tooltip for disabled state */}
{isDisabled && disabledReason && (
<div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-xs text-white bg-gray-800 dark:bg-gray-700 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
{disabledReason}
</div>
)}
</div>
</div>

{/* Help text */}
<div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
{isAuthenticated ? (
<span>Press <kbd className="px-1.5 py-0.5 text-xs font-semibold text-gray-800 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 text-xs font-semibold text-gray-800 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded">Shift+Enter</kbd> for new line</span>
) : (
<span>Please sign in to start chatting</span>
)}
</div>
</form>
</div>
);
};

export default ChatInput;
