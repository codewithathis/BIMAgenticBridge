from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    force_extract: bool = False
    data_ready: bool = False


class ChatResponse(BaseModel):
    status: Literal["ok", "extraction_required", "error"]
    reply: Optional[str] = None
    reason: Optional[str] = None
