from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

class ChatIn(BaseModel):
    message: str
    thread: Optional[str] = None

class ChatOut(BaseModel):
    reply: str
    sentiment: Optional[str] = None
    confidence: Optional[float] = None
    thread: Optional[str] = None

@router.post("/message", response_model=ChatOut)
def post_message(body: ChatIn) -> Dict[str, Any]:
    from agenticcore.chatbot.services import ChatBot
    bot = ChatBot()
    res = bot.reply(body.message)
    return {
        "reply": res.get("reply", ""),
        "sentiment": res.get("sentiment"),
        "confidence": res.get("confidence"),
        "thread": body.thread or res.get("thread"),
    }
