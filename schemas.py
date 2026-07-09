from pydantic import BaseModel
from typing import List

class MessageModel(BaseModel):
    role: str
    content: str

# Frontend se jo data aayega uska schema
class ChatRequest(BaseModel):
    history: List[MessageModel]
    temperature: float = 0.8
