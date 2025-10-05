from pydantic import BaseModel, Field


class MessageIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class MessageOut(BaseModel):
    reply: str
    blocked: bool = False  # True if the guardrails refused the content