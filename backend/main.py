#!/usr/bin/env python3
"""
Simplified main.py for guaranteed Render deployment success
Uses minimal dependencies and robust error handling
Last updated: 2025-06-20 06:48 UTC - FINAL DEPLOYMENT FIX
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import logging
import jwt
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="PatchAI Backend API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://patchai-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Initialize clients with error handling
openai_client = None
supabase_client = None
initialization_error = None

# Security
security = HTTPBearer()

# Debug logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"OPENAI_API_KEY exists: {OPENAI_API_KEY is not None}")
logger.info(f"SUPABASE_URL exists: {SUPABASE_URL is not None}")
logger.info(f"SUPABASE_SERVICE_ROLE_KEY exists: {SUPABASE_SERVICE_ROLE_KEY is not None}")

# Initialize Supabase client
try:
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Supabase client initialized successfully")
    else:
        logger.error("Supabase configuration missing")
except Exception as e:
    logger.error(f"Supabase client initialization error: {e}")

# Import OpenAI and set up client
import openai
from openai import OpenAI

# Use a custom HTTP client to avoid proxy issues
import httpx

class CustomHTTPClient(httpx.Client):
    def __init__(self, *args, **kwargs):
        # Remove any proxy settings
        kwargs.pop('proxies', None)
        kwargs['timeout'] = httpx.Timeout(60.0, connect=60.0)
        super().__init__(*args, **kwargs)

# Initialize the client
try:
    if OPENAI_API_KEY:
        # Create a custom HTTP client
        http_client = CustomHTTPClient()
        
        # Initialize OpenAI with our custom client
        openai_client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            http_client=http_client
        )
        
        # Test the connection
        openai_client.models.list()
        logger.info("OpenAI client initialized and tested successfully")
    else:
        logger.error("OPENAI_API_KEY is None or empty")
        initialization_error = "OPENAI_API_KEY is None or empty"
except Exception as e:
    logger.error(f"OpenAI client initialization error: {e}")
    logger.error(f"Error type: {type(e).__name__}")
    logger.error(f"OpenAI key starts with: {OPENAI_API_KEY[:10] if OPENAI_API_KEY else 'None'}...")
    initialization_error = f"{type(e).__name__}: {str(e)}"
    # Continue without crashing - will handle in endpoints

# Pydantic models
class Message(BaseModel):
    role: str
    content: str

class PromptRequest(BaseModel):
    messages: List[Message]

class PromptResponse(BaseModel):
    response: str

def get_system_prompt():
    """
    Defines the system prompt that sets the behavior and personality of PatchAI
    """
    # SWD Permitting Guidelines (to be completed with user-provided data)
    swd_guidelines = """
    [SWD PERMITTING GUIDELINES - TO BE PROVIDED]
    Please provide the specific SWD permitting guidelines you'd like to include here. If user starts asking questions about the Saltwater Disposals (SWD) in Texas then please share with a breakdown of the information below and provide them a link (provided here:https://www.rrc.texas.gov/oil-and-gas/applications-and-permits/injection-storage-permits/oil-and-gas-waste-disposal/injection-disposal-permit-procedures/) to the public website to the RRC.
    Information From the RRC:
    Utilizing scientific and engineering analysis, the Railroad Commission of Texas has issued new guidelines that further strengthen permitting of disposal wells in the Permian Basin.

    In order to further enhance the integrity of the underground disposal of produced water, new requirements will be implemented for saltwater disposal well (SWD) permit applications in the region. Produced water is a byproduct of oil and gas production and is injected into SWDs.  

    New and amended permit applications in the Permian Basin will now be evaluated based on three primary factors:

    An expanded area of review (AOR) at the injection site;
    Limits on the maximum injection pressure at the surface based on geologic properties; and
    Limits on the maximum daily injection volume based on reservoir pressure.

    In an AOR, operators are required to assess old or unplugged wells to ensure produced water would not escape through those wellbores. The new guidelines increase the AOR to half a mile – an increase from the current quarter-mile radius.

    The new permitting criteria also require operators to demonstrate that their injection pressure will not fracture the confining strata of the reservoirs that produced water is injected into.

    Additionally, the RRC will place limits on the maximum volumes that SWDs can inject based on the pressure in the disposal reservoirs.

    These changes strengthen the Commission’s disposal well permitting requirements by focusing permitting efforts to ensure injected fluids remain confined to the disposal formations to safeguard ground and surface fresh water.

    The new SWD permitting guidelines in the Permian Basin go into effect on June 1, 2025. They apply to new and amended permit applications for deep and shallow disposal wells. Applications for disposal wells that are located within 25 kilometers of a seismic event will continue to be reviewed under the agency’s seismicity review guidelines.
    """
    
    return f"""You are PatchAI, an AI Oilfield consultant specialized in oilfield drilling, completing, and production operations. Your role is to provide expert-level 
    guidance on drilling, completions, production, and other oilfield-related topics, such as reservoir analysis production optimization, and unit economics of oil and gas production and SWD wells. Follow these guidelines:
    
    1. Be helpful, concise, and technical in your responses
    2. Use United States oil and gas industry-standard terminology and units of measurement
    3. When discussing complex topics, break down information into clear, numbered points
    4. Always prioritize safety and regulatory compliance in your advice
    5. If you're unsure about something, say so rather than guessing, it is okay to display uncertainty 
    6. Format your responses with proper markdown for better readability
    7. Use bullet points for lists and **bold** for important terms
    8. Be friendly and folksy, we are in the American south so feel free to use southern dialect, just make sure to not do it on every response, especially not on the technical responses.
    9. Avoid all discussions of sex, gender, race, politics, religion, and personal topics. Stear the conversation back to being productive at work in the oil and gas industry
    
    IMPORTANT REFERENCE INFORMATION:
    {swd_guidelines}
    
    Your responses should be helpful, accurate, and tailored to the user's level of expertise.
    """

# Routes
@app.get("/")
async def root():
    # Trigger deployment
    """Root endpoint for health check"""
    return {"message": "PatchAI Backend API is running"}

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check environment variables and client status"""
    return {
        "openai_key_exists": OPENAI_API_KEY is not None,
        "openai_key_length": len(OPENAI_API_KEY) if OPENAI_API_KEY else 0,
        "openai_client_initialized": openai_client is not None,
        "supabase_client_initialized": supabase_client is not None,
        "initialization_error": initialization_error,
        "environment_vars": {
            "PORT": os.getenv("PORT"),
            "OPENAI_API_KEY": "***" if OPENAI_API_KEY else None,
            "SUPABASE_URL": os.getenv("SUPABASE_URL"),
            "SUPABASE_SERVICE_ROLE_KEY": "***" if os.getenv("SUPABASE_SERVICE_ROLE_KEY") else None
        }
    }

@app.post("/prompt", response_model=PromptResponse)
async def chat_completion(request: PromptRequest):
    if not openai_client:
        raise HTTPException(
            status_code=500,
            detail="OpenAI client not initialized"
        )
    try:
        # Convert messages to the format expected by the API
        messages = [{"role": "system", "content": get_system_prompt()}]
        
        # Add conversation history
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})
        
        logger.info(f"Sending request to OpenAI with messages: {messages}")
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            top_p=0.9,
            frequency_penalty=0.2,
            presence_penalty=0.1
        )
        
        assistant_response = response.choices[0].message.content
        logger.info(f"Received response from OpenAI: {assistant_response[:200]}...")  # Log first 200 chars
        
        return PromptResponse(response=assistant_response)
        
    except Exception as e:
        error_msg = f"OpenAI API error: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@app.get("/history")
async def get_history():
    if not supabase_client:
        raise HTTPException(
            status_code=500,
            detail="Supabase client not initialized"
        )
    try:
        data = supabase_client.from_("history").select("*")
        return data.execute()
    except Exception as e:
        error_msg = f"Supabase API error: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@app.post("/history")
async def save_history(request: PromptRequest):
    if not supabase_client:
        raise HTTPException(
            status_code=500,
            detail="Supabase client not initialized"
        )
    try:
        data = {
            "messages": request.messages,
            "response": ""
        }
        supabase_client.from_("history").insert([data]).execute()
        return {"message": "History saved successfully"}
    except Exception as e:
        error_msg = f"Supabase API error: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
