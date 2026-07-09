from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from groq import Groq
from dotenv import load_dotenv
import os
from schemas import ChatRequest

# Load environment variables from .env file
load_dotenv()

app = FastAPI()
client = Groq()

# CORS allow karna zaroori hai taake tumhara HTML frontend API ko call kar sake
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Yeh hai wo jaadu jo usay Medical Consultant banayega
SYSTEM_PROMPT = """
You are a highly professional, empathetic, and knowledgeable Medical Consultant. 
Your job is to provide general health advice, explain medical terms simply, and suggest basic home remedies or over-the-counter options for minor issues.
CRITICAL RULE: You are an AI, not a real doctor. If a user describes severe symptoms (e.g., chest pain, heavy bleeding), you MUST urge them to visit an emergency room or consult a real doctor immediately. Keep your answers concise and professional.
"""

@app.post("/api/chat")
async def chat_with_doctor(request: ChatRequest):
    # Dynamic temperature adjustment:
    # If the user asks about severe symptoms or asks for precise/technical info (e.g. dosages),
    # we lower the temperature to 0.2 (Emergency / Precise Mode) for safer and more factual answers.
    # Otherwise, we use a higher temperature (default 0.8) for a friendly and conversational response.
    precise_keywords = [
        "emergency", "chest pain", "bleeding", "severe", "heart", "breathing",
        "stroke", "dosage", "dose", "medicine", "side effect", "coughing blood",
        "accident", "paralysis"
    ]
    
    # Check if any precise keyword is in the last message (case-insensitive)
    last_message = request.history[-1].content if request.history else ""
    message_lower = last_message.lower()
    if any(keyword in message_lower for keyword in precise_keywords):
        temperature = 0.2
    else:
        temperature = request.temperature  # fallback to client default (0.8)

    # Groq API ko call bhejna with full conversation history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in request.history:
        # Groq API accepts 'user' and 'assistant' roles
        role = "assistant" if msg.role == "bot" else msg.role
        messages.append({"role": role, "content": msg.content})

    chat_completion = client.chat.completions.create(
        messages=messages,
        model="llama-3.3-70b-versatile",
        temperature=temperature,
    )
    
    return {
        "reply": chat_completion.choices[0].message.content,
        "temperature_used": temperature
    }

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("Index.html", "r", encoding="utf-8") as f:
        return f.read()