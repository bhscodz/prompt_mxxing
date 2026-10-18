# File: backend/app/ai_agent/handler.py
# Description: WebSocket message handler for the AI Agent chat endpoint.
#              Receives JSON from the client, delegates to agent.run_agent(),
#              and streams the response back over the WebSocket.

import json
import logging
from typing import Optional

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db_context
from backend.app.ai_agent.agent import run_agent

logger = logging.getLogger("swasthya.agent.handler")


async def handle_agent_ws_message(websocket: WebSocket, raw: str) -> None:
    """
    Process a single WebSocket message from the AI Agent chat client.

    Expected input JSON:
        {
            "query": str,
            "language": str | null,      // optional hint
            "facility_id": str | null    // optional facility scope
        }

    Output JSON frames:
        { "type": "thinking" }            // immediately after receiving message
        { "type": "final", "content": str, "intent": str, "language": str, "data": dict }
        { "type": "error", "content": str }
    """
    # Send immediate thinking indicator
    try:
        await websocket.send_text(json.dumps({"type": "thinking"}))
    except Exception:
        return

    # Parse incoming message
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        # Treat as plain text query
        msg = {"query": raw}

    query: str = str(msg.get("query", "")).strip()
    language_hint: Optional[str] = msg.get("language") or None
    facility_id: Optional[str] = msg.get("facility_id") or None

    if not query:
        await websocket.send_text(json.dumps({
            "type": "error",
            "content": "Empty query received."
        }))
        return

    # Run the agent pipeline
    try:
        async with get_db_context() as db:
            result = await run_agent(
                query=query,
                db=db,
                facility_id=facility_id,
                language_hint=language_hint,
            )

        await websocket.send_text(json.dumps({
            "type": "final",
            "content": result["response"],
            "intent": result["intent"],
            "language": result["language"],
            "data": result.get("data", {}),
        }))

    except Exception as exc:
        logger.exception(f"Agent handler error: {exc}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "content": f"Agent encountered an error: {str(exc)}"
        }))
