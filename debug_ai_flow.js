// Debug AI Response Flow
// Add this to your browser console to trace the issue

console.log('🔍 DEBUGGING AI RESPONSE FLOW');

// Override ChatService.sendPrompt to add debugging
const originalSendPrompt = window.ChatService?.sendPrompt;
if (originalSendPrompt) {
  window.ChatService.sendPrompt = async function(...args) {
    console.log('🚀 ChatService.sendPrompt called with:', args);
    try {
      const result = await originalSendPrompt.apply(this, args);
      console.log('✅ ChatService.sendPrompt result:', result);
      return result;
    } catch (error) {
      console.error('❌ ChatService.sendPrompt error:', error);
      throw error;
    }
  };
} else {
  console.error('❌ ChatService not found on window object');
}

// Override fetch to trace API calls
const originalFetch = window.fetch;
window.fetch = async function(url, options) {
  if (url.includes('/prompt')) {
    console.log('🌐 FETCH /prompt called:', { url, options });
    try {
      const response = await originalFetch(url, options);
      console.log('📡 FETCH /prompt response:', response.status, response.statusText);
      
      // Clone response to read body without consuming it
      const clonedResponse = response.clone();
      try {
        const data = await clonedResponse.json();
        console.log('📄 FETCH /prompt data:', data);
      } catch (e) {
        console.log('📄 FETCH /prompt data: (not JSON)');
      }
      
      return response;
    } catch (error) {
      console.error('❌ FETCH /prompt error:', error);
      throw error;
    }
  }
  return originalFetch(url, options);
};

console.log('✅ Debugging setup complete. Send a message and watch the console.');
