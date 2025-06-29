Supabase URL: Present
supabaseClient.js:8 Supabase Key: Present
stripe.js:11 ⚠️ Stripe publishable key not found. Payment features will be disabled.
(anonymous) @ stripe.js:11Understand this warning
dom.js?token=991857-791378-107919:893 initEternlDomAPI: domId 715363-551161-681373 false
initEternlDomAPI @ dom.js?token=991857-791378-107919:893Understand this warning
dom.js?token=991857-791378-107919:894 initEternlDomAPI: href https://www.patchai.app/chat
initEternlDomAPI @ dom.js?token=991857-791378-107919:894Understand this warning
App.js:79 🏗️ LAYOUT_DEBUG: ChatLayout rendering with isLoading: false error: false chats.length: 0
useChatStore.js:469 🔍 LOAD_DEBUG: Checking message load conditions: Object
useChatStore.js:480 ✅ LOAD_DEBUG: Conditions met - calling loadMessages()
useChatStore.js:299 🚀 LOAD_DEBUG: loadMessages function called
useChatStore.js:317 🔄 LOAD_DEBUG: Starting message load process
useChatStore.js:324 📡 LOAD_DEBUG: About to call ChatService.getSingleChatSession()
chatService.js:9 🔄 ChatService: Fetching single chat session messages
useChatStore.js:145 ⏳ Setting loading: true
2App.js:79 🏗️ LAYOUT_DEBUG: ChatLayout rendering with isLoading: true error: false chats.length: 0
useChatStore.js:469 🔍 LOAD_DEBUG: Checking message load conditions: Object
useChatStore.js:490 🔄 LOAD_DEBUG: Skipping loadMessages - initial load already done
api.js:24 🔐 Supabase session: Present
api.js:25 🔐 Access token: Present
api.js:27 🔐 Token preview: eyJhbGciOiJIUzI1NiIsImtpZCI6IlJzbzRKb1VpVkVyUnhnY0...
App.js:79 🏗️ LAYOUT_DEBUG: ChatLayout rendering with isLoading: true error: false chats.length: 0
useChatStore.js:469 🔍 LOAD_DEBUG: Checking message load conditions: Object
useChatStore.js:490 🔄 LOAD_DEBUG: Skipping loadMessages - initial load already done
2App.js:79 🏗️ LAYOUT_DEBUG: ChatLayout rendering with isLoading: true error: false chats.length: 0
useChatStore.js:469 🔍 LOAD_DEBUG: Checking message load conditions: Object
useChatStore.js:490 🔄 LOAD_DEBUG: Skipping loadMessages - initial load already done
manifest.json:1 
            
            
           Failed to load resource: the server responded with a status of 403 ()Understand this error
chat:1 Manifest fetch from https://www.patchai.app/manifest.json failed, code 403Understand this error
chatService.js:12 🔍 ChatService: Single chat response: Object
useChatStore.js:327 📨 LOAD_DEBUG: ChatService.getSingleChatSession() returned: Object
useChatStore.js:82 📥 Loading 0 messages
useChatStore.js:96 📥 Loaded Messages: Object
useChatStore.js:186 🏷️ Setting chat title: Chat Session
useChatStore.js:145 ⏳ Setting loading: false
6App.js:79 🏗️ LAYOUT_DEBUG: ChatLayout rendering with isLoading: false error: false chats.length: 0
dom.js?token=742498-596803-377171:893 initEternlDomAPI: domId 863325-386240-516729 true
initEternlDomAPI @ dom.js?token=742498-596803-377171:893Understand this warning
dom.js?token=742498-596803-377171:894 initEternlDomAPI: href https://js.stripe.com/v3/m-outer-3437aaddcdf6922d623e172c2d6f9278.html#url=https%3A%2F%2Fwww.patchai.app%2Fchat&title=React%20App&referrer=https%3A%2F%2Fvercel.com%2F&muid=a4495c76-5a09-4b28-a393-c20f243102b8294a54&sid=4ea5cee5-c7dd-4049-801c-6b4308fc463c042209&version=6&preview=false&__shared_params__[version]=basil
initEternlDomAPI @ dom.js?token=742498-596803-377171:894Understand this warning
dom.js?token=137100-99743-84121:893 initEternlDomAPI: domId 108424-6543-851023 true
initEternlDomAPI @ dom.js?token=137100-99743-84121:893Understand this warning
dom.js?token=137100-99743-84121:894 initEternlDomAPI: href https://m.stripe.network/inner.html#url=https%3A%2F%2Fwww.patchai.app%2Fchat&title=React%20App&referrer=https%3A%2F%2Fvercel.com%2F&muid=a4495c76-5a09-4b28-a393-c20f243102b8294a54&sid=4ea5cee5-c7dd-4049-801c-6b4308fc463c042209&version=6&preview=false&__shared_params__[version]=basil
initEternlDomAPI @ dom.js?token=137100-99743-84121:894Understand this warning
chatService.js:32 🔄 ChatService: Starting message send with context preservation
chatService.js:52 🔍 PAYLOAD_DEBUG: Prepared 1 total messages for backend
chatService.js:53    • Historical messages: 0
chatService.js:54    • New user message: 1
chatService.js:55    • Message flow: user
chatService.js:60 📄 PAYLOAD_DEBUG: Message 1 (user): testing patch
chatService.js:65 ❌ PAYLOAD_DEBUG: CRITICAL - Only 1 message in payload! Context loss detected.
sendMessage @ chatService.js:65Understand this error
chatService.js:66 ❌ PAYLOAD_DEBUG: This means conversationHistory was empty when it should contain previous messages.
sendMessage @ chatService.js:66Understand this error
useChatStore.js:37 Unknown action type: undefined
Mo @ useChatStore.js:37Understand this warning
useChatStore.js:113 ➕ Adding user message: Object
useChatStore.js:158 ⌨️ Setting typing: true
App.js:79 🏗️ LAYOUT_DEBUG: ChatLayout rendering with isLoading: false error: false chats.length: 1
api.js:24 🔐 Supabase session: Present
api.js:25 🔐 Access token: Present
api.js:27 🔐 Token preview: eyJhbGciOiJIUzI1NiIsImtpZCI6IlJzbzRKb1VpVkVyUnhnY0...
chatService.js:82 ✅ ChatService: AI response received with full conversational context
useChatStore.js:432 ✅ SEND_MESSAGE: Message sent and response received
useChatStore.js:113 ➕ Adding assistant message: Object
useChatStore.js:158 ⌨️ Setting typing: false
App.js:79 🏗️ LAYOUT_DEBUG: ChatLayout rendering with isLoading: false error: false chats.length: 1
chatService.js:32 🔄 ChatService: Starting message send with context preservation
chatService.js:52 🔍 PAYLOAD_DEBUG: Prepared 1 total messages for backend
chatService.js:53    • Historical messages: 0
chatService.js:54    • New user message: 1
chatService.js:55    • Message flow: user
chatService.js:60 📄 PAYLOAD_DEBUG: Message 1 (user): what was your last message to me?
chatService.js:65 ❌ PAYLOAD_DEBUG: CRITICAL - Only 1 message in payload! Context loss detected.
sendMessage @ chatService.js:65Understand this error
chatService.js:66 ❌ PAYLOAD_DEBUG: This means conversationHistory was empty when it should contain previous messages.
sendMessage @ chatService.js:66Understand this error
useChatStore.js:37 Unknown action type: undefined
Mo @ useChatStore.js:37Understand this warning
useChatStore.js:113 ➕ Adding user message: Object
useChatStore.js:158 ⌨️ Setting typing: true
App.js:79 🏗️ LAYOUT_DEBUG: ChatLayout rendering with isLoading: false error: false chats.length: 1
api.js:24 🔐 Supabase session: Present
api.js:25 🔐 Access token: Present
api.js:27 🔐 Token preview: eyJhbGciOiJIUzI1NiIsImtpZCI6IlJzbzRKb1VpVkVyUnhnY0...
chatService.js:82 ✅ ChatService: AI response received with full conversational context
useChatStore.js:432 ✅ SEND_MESSAGE: Message sent and response received
useChatStore.js:113 ➕ Adding assistant message: Object
useChatStore.js:158 ⌨️ Setting typing: false
App.js:79 🏗️ LAYOUT_DEBUG: ChatLayout rendering with isLoading: false error: false chats.length: 1
manifest.json:1 
            
            
           Failed to load resource: the server responded with a status of 403 ()Understand this error