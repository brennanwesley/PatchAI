import React, { useState } from 'react';
import { ChatService } from '../services/chatService';

export default function BackendTest() {
  const [results, setResults] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const runTest = async (testName, testFunction) => {
    setIsLoading(true);
    try {
      console.log(`🧪 Running test: ${testName}`);
      const result = await testFunction();
      setResults(prev => ({
        ...prev,
        [testName]: { success: true, data: result, error: null }
      }));
      console.log(`✅ Test passed: ${testName}`, result);
    } catch (error) {
      setResults(prev => ({
        ...prev,
        [testName]: { success: false, data: null, error: error.message }
      }));
      console.error(`❌ Test failed: ${testName}`, error);
    }
    setIsLoading(false);
  };

  const tests = [
    {
      name: 'Backend Health',
      description: 'Check if backend is responding',
      test: () => ChatService.healthCheck()
    },
    {
      name: 'Authentication',
      description: 'Verify JWT token is working',
      test: () => ChatService.testAuth()
    },
    {
      name: 'Load Chats',
      description: 'Fetch user chat sessions',
      test: () => ChatService.getUserChatSessions()
    },
    {
      name: 'AI Prompt',
      description: 'Send a test message to AI',
      test: () => ChatService.sendPrompt([
        { role: 'user', content: 'Say "Backend integration test successful" if you can read this.' }
      ])
    }
  ];

  const runAllTests = async () => {
    for (const test of tests) {
      await runTest(test.name, test.test);
      // Small delay between tests
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Backend Integration Test</h2>
      
      <div className="mb-6">
        <button
          onClick={runAllTests}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {isLoading ? 'Running Tests...' : 'Run All Tests'}
        </button>
      </div>

      <div className="space-y-4">
        {tests.map(test => {
          const result = results[test.name];
          return (
            <div key={test.name} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h3 className="font-semibold text-lg">{test.name}</h3>
                  <p className="text-gray-600 text-sm">{test.description}</p>
                </div>
                <div className="flex items-center space-x-2">
                  {result && (
                    <span className={`px-2 py-1 rounded text-sm ${
                      result.success 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {result.success ? '✅ PASS' : '❌ FAIL'}
                    </span>
                  )}
                  <button
                    onClick={() => runTest(test.name, test.test)}
                    disabled={isLoading}
                    className="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 text-sm"
                  >
                    Test
                  </button>
                </div>
              </div>
              
              {result && (
                <div className="mt-3 p-3 bg-gray-50 rounded">
                  {result.success ? (
                    <div>
                      <p className="text-green-700 font-medium">Success!</p>
                      <pre className="text-xs text-gray-600 mt-1 overflow-auto">
                        {JSON.stringify(result.data, null, 2)}
                      </pre>
                    </div>
                  ) : (
                    <div>
                      <p className="text-red-700 font-medium">Error:</p>
                      <p className="text-red-600 text-sm mt-1">{result.error}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="font-semibold text-blue-800 mb-2">Expected Results:</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• <strong>Backend Health:</strong> Should return server status</li>
          <li>• <strong>Authentication:</strong> Should pass if logged in, fail if not</li>
          <li>• <strong>Load Chats:</strong> Should return array of chat sessions (may be empty)</li>
          <li>• <strong>AI Prompt:</strong> Should return AI response confirming integration</li>
        </ul>
      </div>
    </div>
  );
}
