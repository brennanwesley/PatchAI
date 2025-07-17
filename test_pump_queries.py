import os
import sys
import json
import asyncio
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import the pump context service
from services.pump_context_service import PumpContextService

def test_pump_context_service():
    """Test the pump context service with various queries"""
    print("\n=== Testing Pump Context Service ===")
    
    # Initialize the service
    try:
        service = PumpContextService()
        print("[OK] PumpContextService initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize PumpContextService: {str(e)}")
        return
    
    # Test queries
    test_queries = [
        "What's the flowrate vs pressure for a 4x6-13 pump?",
        "Show me the performance curve for a 2x3-13 pump at 1750 RPM",
        "What's the efficiency of a 3x4-13 pump at 100 GPM and 100 ft?",
        "Compare the performance of 4x6-13 and 6x8-15 pumps",
        "What's the NPSHr for a 8x10-17 pump at 2000 GPM?"
    ]
    
    for query in test_queries:
        print(f"\n[TEST] Testing query: {query}")
        try:
            context = service.generate_pump_context(query)
            if context:
                print(f"[OK] Context generated ({len(context)} chars)")
                print(f"[PREVIEW] Context preview: {context[:200]}...")
                
                # Check for specific data points in the context
                if any(size in query for size in ["2x3-13", "3x4-13", "4x6-13", "6x8-15", "8x10-17"]):
                    if "head" in context.lower() and "flow" in context.lower():
                        print("   [OK] Found head and flow data in context")
                    else:
                        print("   [WARN] Head and flow data not found in context")
                
                if "efficiency" in query.lower() and "efficiency" in context.lower():
                    print("   [OK] Found efficiency data in context")
                
                if "npsh" in query.lower() and "npsh" in context.lower():
                    print("   [OK] Found NPSH data in context")
                    
            else:
                print("[WARN] No context generated (may not be a pump-related query)")
                
        except Exception as e:
            print(f"[ERROR] Error generating pump context: {str(e)}")
            import traceback
            traceback.print_exc()

async def test_chat_completion(api_key: str, query: str):
    """Test chat completion with a pump query"""
    import httpx
    
    url = "https://patchai-backend.onrender.com/prompt"  # Update with your production URL
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "messages": [
            {"role": "user", "content": query}
        ]
    }
    
    print(f"\n[API] Sending query to API: {query}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            
            print(f"[RESPONSE] Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("[OK] API Response:")
                print(f"   - Role: {result.get('role', 'N/A')}")
                print(f"   - Content: {result.get('content', 'N/A')[:200]}...")
                
                # Check if response contains pump data
                content = result.get('content', '').lower()
                if any(term in content for term in ["head", "flow", "efficiency", "npsh", "rpm"]):
                    print("   [OK] Response contains pump performance data")
                else:
                    print("   [WARN] Response does not appear to contain pump performance data")
                    
            else:
                print(f"[ERROR] Error response: {response.status_code}")
                print(f"Response content: {response.text}")
                
    except Exception as e:
        print(f"[ERROR] Request failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== PatchAI Pump Query Tester ===\n")
    
    # Test the pump context service directly
    test_pump_context_service()
    
    # Test the chat completion endpoint with a sample query
    test_query = "What's the flowrate vs pressure for a 4x6-13 pump?"
    print(f"\n=== Testing API Endpoint with Query: {test_query} ===")
    
    # Try to get the API key from environment variable
    import os
    api_key = os.getenv("PATCHAI_API_KEY", "")
    
    if api_key:
        asyncio.run(test_chat_completion(api_key, test_query))
    else:
        print("\n[INFO] No API key found in PATCHAI_API_KEY environment variable.")
        print("To test the API, set the PATCHAI_API_KEY environment variable and run the script again.")
        print("Example (Windows): set PATCHAI_API_KEY=your_api_key_here")
        print("Example (Unix/Mac): export PATCHAI_API_KEY=your_api_key_here")
