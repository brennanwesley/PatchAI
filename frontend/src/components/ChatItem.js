import React, { useState } from 'react';

export default function ChatItem({ 
  chat, 
  isActive, 
  onSelect, 
  onEdit, 
  onDelete, 
  formatDate 
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(chat.title || 'New Chat');

  const handleEditSubmit = () => {
    if (editTitle.trim()) {
      onEdit(chat.id, editTitle.trim());
    }
    setIsEditing(false);
  };

  const handleEditCancel = () => {
    setEditTitle(chat.title || 'New Chat');
    setIsEditing(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleEditSubmit();
    } else if (e.key === 'Escape') {
      handleEditCancel();
    }
  };

  const handleDeleteClick = (e) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this chat?')) {
      onDelete(chat.id);
    }
  };

  const handleEditClick = (e) => {
    e.stopPropagation();
    setIsEditing(true);
  };

  return (
    <div
      className={`relative group border rounded-lg mb-2 transition-all duration-200 ${
        isActive
          ? 'bg-blue-50 border-blue-200 shadow-sm'
          : 'bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300'
      }`}
    >
      <button
        onClick={() => !isEditing && onSelect(chat)}
        className="w-full text-left p-3 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
        disabled={isEditing}
      >
        <div className="flex justify-between items-start mb-1">
          {isEditing ? (
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              onBlur={handleEditSubmit}
              onKeyDown={handleKeyPress}
              className="flex-1 text-sm font-medium text-gray-900 bg-white border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <h3 className="font-medium text-gray-900 text-sm truncate flex-1 pr-2">
              {chat.title || 'New Chat'}
            </h3>
          )}
          
          {!isEditing && (
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              <button
                onClick={handleEditClick}
                className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-100 rounded transition-colors duration-200"
                title="Edit chat name"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button
                onClick={handleDeleteClick}
                className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-100 rounded transition-colors duration-200"
                title="Delete chat"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          )}
          
          <span className="text-xs text-gray-500 ml-2 flex-shrink-0">
            {formatDate(chat.createdAt)}
          </span>
        </div>
        
        {chat.lastMessage && !isEditing && (
          <p className="text-xs text-gray-600 truncate">
            {chat.lastMessage}
          </p>
        )}
      </button>
    </div>
  );
}
