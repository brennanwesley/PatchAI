# Chat Backend API

A FastAPI backend that provides chat functionality with OpenAI integration and message history storage via Supabase.

## Features

- **POST /prompt**: Send messages to OpenAI's Chat Completion API
- **POST /history**: Save user and assistant messages to Supabase
- **GET /history**: Retrieve latest 20 messages for authenticated user
- JWT-based authentication
- CORS middleware for cross-origin requests
- Environment variable configuration

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key

### 3. Supabase Database Setup

Create a `messages` table in your Supabase database with the following schema:

```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add index for better query performance
CREATE INDEX idx_messages_user_id_created_at ON messages(user_id, created_at DESC);
```

### 4. Run the Application

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## Deployment

This project is configured for deployment on Render or similar platforms. The application runs on port 8000 by default and is compatible with Python 3.11.

### Render Deployment

1. Connect your repository to Render
2. Set the build command: `pip install -r requirements.txt`
3. Set the start command: `python main.py`
4. Add your environment variables in the Render dashboard

## Authentication

The API expects a JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

For development, the token parsing is lenient and will fall back to an "anonymous" user if token parsing fails.

## API Endpoints

### POST /prompt
Send messages to OpenAI and get a response.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ]
}
```

**Response:**
```json
{
  "response": "I'm doing well, thank you for asking!"
}
```

### POST /history
Save conversation messages to the database.

**Request:**
```json
{
  "user_message": "Hello, how are you?",
  "assistant_message": "I'm doing well, thank you for asking!"
}
```

### GET /history
Retrieve the latest 20 messages for the authenticated user.

**Response:**
```json
[
  {
    "id": 1,
    "user_id": "user123",
    "role": "user",
    "content": "Hello, how are you?",
    "created_at": "2024-01-01T12:00:00Z"
  },
  {
    "id": 2,
    "user_id": "user123", 
    "role": "assistant",
    "content": "I'm doing well, thank you for asking!",
    "created_at": "2024-01-01T12:00:01Z"
  }
]
```
