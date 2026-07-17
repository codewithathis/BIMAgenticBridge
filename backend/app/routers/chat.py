from fastapi import APIRouter, Depends, HTTPException

from app.agent import ChatAgent
from app.config import Settings, get_settings
from app.models import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


def get_agent(settings: Settings = Depends(get_settings)) -> ChatAgent:
    return ChatAgent(settings)


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    agent: ChatAgent = Depends(get_agent),
) -> ChatResponse:
    try:
        return agent.handle_chat(
            message=request.message.strip(),
            data_ready=request.data_ready,
            force_extract=request.force_extract,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - surface unexpected agent failures
        raise HTTPException(status_code=500, detail=f"Chat agent failed: {exc}") from exc
