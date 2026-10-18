# File: backend/app/api/ai_agent.py
# Description: REST and WebSocket endpoints for the Multilingual AI Health Assistant.
#   POST /agent/chat    — single-turn REST query
#   WS   /agent/ws      — streaming WebSocket chat (HTTP-level — full WS in main.py)

import json
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.ai_agent.agent import run_agent, detect_language, classify_intent, INTENTS
from app.core.security import get_current_user
from app.models.auth import User

logger = logging.getLogger("swasthya.api.agent")

# Two routers — main.py mounts both under /api/v1
router    = APIRouter(prefix="/agent", tags=["AI Assistant"])
agent_ws_router = APIRouter(prefix="/agent", tags=["AI Assistant WebSocket"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class AgentChatRequest(BaseModel):
    query: str
    language: Optional[str] = None      # Optional language hint (en/hi/mr/ta/te/bn)
    facility_id: Optional[str] = None   # Scope responses to a specific facility


class AgentChatResponse(BaseModel):
    response: str
    language: str
    intent: str
    data: Dict[str, Any] = {}
    facility_id: Optional[str] = None


# ---------------------------------------------------------------------------
# POST /agent/chat — single-turn REST query
# ---------------------------------------------------------------------------
@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    body: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Single-turn REST query for the multilingual AI health assistant.

    Use this endpoint from non-WebSocket clients (mobile apps, JSON-RPC, scripts).
    For interactive chat, use the WebSocket at /ws/agent-chat.
    """
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    result = await run_agent(
        query=body.query,
        db=db,
        facility_id=body.facility_id,
        language_hint=body.language,
    )
    return AgentChatResponse(
        response=result["response"],
        language=result["language"],
        intent=result["intent"],
        data=result.get("data", {}),
        facility_id=result.get("facility_id"),
    )


# ---------------------------------------------------------------------------
# GET /agent/intents — list available intents
# ---------------------------------------------------------------------------
@router.get("/intents")
async def list_intents(_: User = Depends(get_current_user)):
    """Return all supported agent intent categories."""
    return {"intents": INTENTS}


# ---------------------------------------------------------------------------
# GET /agent/detect-language — utility: detect language of a text sample
# ---------------------------------------------------------------------------
@router.get("/detect-language")
async def detect_lang(
    text: str,
    _: User = Depends(get_current_user),
):
    """Detect the language code of a given text string."""
    lang = detect_language(text)
    intent = classify_intent(text)
    return {"language": lang, "intent": intent, "text_preview": text[:100]}
