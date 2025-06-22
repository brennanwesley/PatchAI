import React from 'react';
import { useChatStore } from '../hooks/useChatStore';

export default function MobileHeader({ onToggleSidebar, chatTitle }) {
  const { activeChat } = useChatStore();

  const displayTitle = chatTitle || activeChat?.title || 'New Chat';

  return (
    <div className="md:hidden bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
      {/* Hamburger Menu Button */}
      <button
        onClick={onToggleSidebar}
        className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        aria-label="Toggle sidebar"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Chat Title */}
      <div className="flex-1 text-center">
        <h1 className="text-lg font-semibold text-gray-900 truncate px-4">
          {displayTitle}
        </h1>
      </div>

      {/* Spacer to balance the hamburger button */}
      <div className="w-10"></div>
    </div>
  );
}
