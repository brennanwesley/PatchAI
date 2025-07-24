import React, { useState, useEffect } from 'react';
import { useChatStore } from '../hooks/useChatStore';
import wtiService from '../services/wtiService';

export default function StatusCards() {
  const { sendMessage, isTyping } = useChatStore();
  
  // WTI Oil Price state
  const [wtiData, setWtiData] = useState({
    price: 0,
    change: 0,
    changePercent: 0,
    lastUpdated: null,
    source: 'loading',
    isLive: false,
    loading: true
  });
  
  // Fetch WTI price data
  const fetchWTIData = async () => {
    try {
      console.log('[StatusCards] Fetching WTI data...');
      const data = await wtiService.getWTIPrice();
      console.log('[StatusCards] WTI data received:', data);
      setWtiData({ ...data, loading: false });
    } catch (error) {
      console.error('[StatusCards] Failed to fetch WTI data:', error);
      // Set fallback data with error state
      setWtiData({
        price: 65.00, // Fallback price close to expected range
        change: 0,
        changePercent: 0,
        lastUpdated: new Date().toISOString(),
        source: 'fallback',
        isLive: false,
        loading: false
      });
    }
  };
  
  // Initial fetch and setup interval
  useEffect(() => {
    // Fetch immediately
    fetchWTIData();
    
    // Set up 10-minute interval
    const interval = setInterval(fetchWTIData, 10 * 60 * 1000);
    
    // Cleanup interval on unmount
    return () => clearInterval(interval);
  }, []);

  const quickPrompts = [
    {
      id: 1,
      title: "Facility Design",
      prompt: "Lets design a new production facility, start with volume forecast.",
      icon: "📊",
      color: "bg-blue-50 border-blue-200 text-blue-800"
    },
    {
      id: 2,
      title: "Market Trends",
      prompt: "What are the current market trends in my industry?",
      icon: "📈",
      color: "bg-green-50 border-green-200 text-green-800"
    },
    {
      id: 3,
      title: "Cost Optimization",
      prompt: "Help me identify areas for cost optimization in my operations",
      icon: "💰",
      color: "bg-yellow-50 border-yellow-200 text-yellow-800"
    },
    {
      id: 4,
      title: "Strategic Planning",
      prompt: "Create a strategic plan for the next quarter",
      icon: "🎯",
      color: "bg-purple-50 border-purple-200 text-purple-800"
    }
  ];

  const handleQuickPrompt = async (prompt) => {
    if (!isTyping) {
      await sendMessage(prompt);
    }
  };

  return (
    <div className="w-80 bg-gray-50 border-l border-gray-200 p-4 overflow-y-auto">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
      
      {/* Quick Prompts */}
      <div className="space-y-3 mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Quick Prompts</h3>
        {quickPrompts.map((prompt) => (
          <button
            key={prompt.id}
            onClick={() => handleQuickPrompt(prompt.prompt)}
            disabled={isTyping}
            className={`w-full p-3 rounded-lg border-2 border-dashed transition-all duration-200 text-left hover:shadow-sm ${
              isTyping 
                ? 'opacity-50 cursor-not-allowed' 
                : 'hover:border-solid cursor-pointer'
            } ${prompt.color}`}
          >
            <div className="flex items-start gap-3">
              <span className="text-lg">{prompt.icon}</span>
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-sm mb-1">{prompt.title}</h4>
                <p className="text-xs opacity-75 line-clamp-2">{prompt.prompt}</p>
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Status Cards */}
      <div className="space-y-4">
        {/* WTI Price Card */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-700">WTI Oil Price</h3>
            <span className={`text-xs font-medium ${
              wtiData.loading ? 'text-blue-600' : 
              wtiData.isLive ? 'text-green-600' : 'text-gray-500'
            }`}>
              {wtiData.loading ? 'Loading...' : wtiData.isLive ? 'Live' : 'Cached'}
            </span>
          </div>
          <div className="flex items-end gap-2">
            <span className="text-2xl font-bold text-gray-900">
              {wtiData.loading ? '--' : `$${wtiData.price.toFixed(2)}`}
            </span>
            {!wtiData.loading && (
              <span className={`text-sm font-medium ${
                wtiData.changePercent >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {wtiData.changePercent >= 0 ? '+' : ''}{wtiData.changePercent.toFixed(1)}%
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {wtiData.loading ? 'Fetching live data...' : 'Per barrel'}
          </p>
        </div>

        {/* Recent Deals Card */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Deals</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Midland Basin</span>
              <span className="text-sm font-medium text-gray-900">$2.1M</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Permian Play</span>
              <span className="text-sm font-medium text-gray-900">$850K</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Eagle Ford</span>
              <span className="text-sm font-medium text-gray-900">$1.3M</span>
            </div>
          </div>
          <button className="w-full mt-3 text-xs text-blue-600 hover:text-blue-700 font-medium">
            View all deals →
          </button>
        </div>

        {/* Insights Card */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Key Insights</h3>
          <div className="space-y-3">
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></div>
              <p className="text-xs text-gray-600">Production up 15% this quarter</p>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full mt-1.5 flex-shrink-0"></div>
              <p className="text-xs text-gray-600">Operating costs reduced by 8%</p>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 bg-yellow-500 rounded-full mt-1.5 flex-shrink-0"></div>
              <p className="text-xs text-gray-600">New drilling opportunities identified</p>
            </div>
          </div>
          <button className="w-full mt-3 text-xs text-blue-600 hover:text-blue-700 font-medium">
            Generate report →
          </button>
        </div>

        {/* Performance Card */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Performance</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-600">Revenue</span>
              <span className="text-sm font-medium text-green-600">+12.5%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-600">Efficiency</span>
              <span className="text-sm font-medium text-blue-600">+8.2%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-600">ROI</span>
              <span className="text-sm font-medium text-purple-600">+15.7%</span>
            </div>
          </div>
          <div className="mt-3 bg-gray-100 rounded-full h-2">
            <div className="bg-gradient-to-r from-blue-500 to-green-500 h-2 rounded-full" style={{ width: '78%' }}></div>
          </div>
          <p className="text-xs text-gray-500 mt-1">Overall score: 78/100</p>
        </div>
      </div>
    </div>
  );
}
