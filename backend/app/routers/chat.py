import logging

from fastapi import APIRouter, Depends, HTTPException
from openai import APIError, APITimeoutError, AuthenticationError, RateLimitError

from app.agent import ChatAgent
from app.config import Settings, get_settings
from app.exceptions import AgentConfigurationError, ToolExecutionError, UpstreamLlmError
from app.models import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

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
    except AgentConfigurationError as exc:
        logger.warning("Chat configuration error: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (AuthenticationError, RateLimitError) as exc:
        logger.warning("LLM auth/rate limit error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="LLM provider rejected the request. Check API key and rate limits.",
        ) from exc
    except (APITimeoutError, APIError, UpstreamLlmError) as exc:
        logger.exception("Upstream LLM failure")
        raise HTTPException(
            status_code=502,
            detail="The language model service failed. Please try again.",
        ) from exc
    except ToolExecutionError as exc:
        logger.exception("Tool execution failure")
        raise HTTPException(
            status_code=500,
            detail="A BIM data tool failed while processing the request.",
        ) from exc
    except Exception:
        logger.exception("Unhandled chat agent failure")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the chat request.",
        ) from None
