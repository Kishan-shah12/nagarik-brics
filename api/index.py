import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from google import genai
from google.genai.errors import APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NagarikBRICS AI Assistant")

class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=1000, description="User prompt for the AI assistant.")
    language: str = Field(default="English", description="Language for the response.")

@app.post("/api/chat")
async def chat_handler(request: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY is missing.")
        raise HTTPException(status_code=500, detail="Server misconfiguration: AI service unavailable.")
    
    try:
        client = genai.Client(api_key=api_key)
        
        system_prompt = f"You are a helpful assistant for the NagarikBRICS Digital Public Good platform. Answer in {request.language}. Keep responses concise and focused on public infrastructure, feedback aggregation, or project recommendations."
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_prompt}\n\nUser: {request.prompt}",
        )
        
        return {"reply": response.text}
        
    except APIError as e:
        logger.error(f"Gemini API Error: {str(e)}")
        return JSONResponse(status_code=502, content={"error": "Failed to communicate with AI provider.", "details": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": "Internal server error."})
