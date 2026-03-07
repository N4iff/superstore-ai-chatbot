"""
Simple WebSocket server that exposes the ADK parent agent as a
chat-style API for a custom frontend.

Run locally with:

    cd adk-chatbot
    uvicorn server:app --reload --host 0.0.0.0 --port 8000

Then point the frontend WebSocket at:

    ws://localhost:8000/ws/chat
"""
import asyncio
import os
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part

from agents.parent_agent import create_parent_agent
from integrations.report_handler import process_report


def _extract_text_from_event(event) -> str:
    """
    Extract *text only* from an ADK Runner event.
    Returns "" when the event has no textual content.
    """
    from google.genai.types import Content as GenContent  # type: ignore

    direct_text = getattr(event, "text", None)
    if isinstance(direct_text, str) and direct_text:
        return direct_text

    if hasattr(event, "content"):
        content = event.content
        if isinstance(content, GenContent):
            text_parts = []
            for part in content.parts:
                if hasattr(part, "text"):
                    text_parts.append(part.text or "")
            return "".join(text_parts)
        return ""
    return ""


app = FastAPI(title="BI Chatbot WebSocket API")

# Allow localhost frontends during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- ADK runner setup --------------------------------------------------------

parent_agent = create_parent_agent()
session_service = InMemorySessionService()
runner = Runner(agent=parent_agent, app_name="bi_chatbot", session_service=session_service)

# Note: affects how ADK streams internally; we still deliver to client via WebSocket.
run_config = RunConfig(streaming_mode=StreamingMode.SSE)

# Keep track of sessions per WebSocket connection
ws_sessions: Dict[int, str] = {}


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for streaming chat.

    Protocol (very simple):
      - Client connects to /ws/chat
      - Client sends plain text messages (the user query)
      - Server sends JSON messages:
            {"type": "status", "text": "thinking"}
            {"type": "chunk", "text": "<partial text>"}
            {"type": "done"}

    Important streaming behavior:
    - ADK commonly emits SNAPSHOTS (full text-so-far) for partial updates.
    - It may also emit repeated snapshots and then a final full message.
    - Sometimes it emits a non-prefix snapshot (reformat/restart).
    To prevent duplicated output in the UI, we ONLY stream snapshot deltas when
    the new snapshot strictly extends what we already emitted.
    """

    await websocket.accept()

    # Create a fresh session for this WebSocket connection
    session = await session_service.create_session(app_name="bi_chatbot", user_id="web_user")
    ws_sessions[id(websocket)] = session.id

    try:
        while True:
            user_input = await websocket.receive_text()
            user_input = user_input.strip()
            if not user_input:
                continue

            # Notify client that work has started
            await websocket.send_json({"type": "status", "text": "thinking"})

            user_content = Content(role="user", parts=[Part(text=user_input)])

            emitted_text = ""     # exactly what we've sent to the client so far
            saw_any_text = False
            report_payload = None

            async for event in runner.run_async(
                user_id=session.user_id,
                session_id=session.id,
                new_message=user_content,
                run_config=run_config,
            ):
                # Only stream assistant output. Ignore user echoes / other authors.
                author = getattr(event, "author", None)
                if author == "user":
                    continue

                text = _extract_text_from_event(event)
                if not text:
                    continue

                is_partial = bool(getattr(event, "partial", False))

                if os.getenv("ADK_STREAM_DEBUG") == "1" and is_partial:
                    print(
                        "[adk-stream] partial event",
                        "author=",
                        getattr(event, "author", None),
                        "type=",
                        type(event),
                        "len=",
                        len(text),
                        "prefix_ext=",
                        text.startswith(emitted_text),
                        flush=True,
                    )

                # If this is a REPORT payload, don't stream raw content;
                # we will hand it to the report handler once at the end.
                if "REPORT CONTENT:" in text:
                    report_payload = text
                    continue

                new_part = ""

                # Primary path: snapshot that strictly extends what we already emitted.
                if text.startswith(emitted_text):
                    new_part = text[len(emitted_text) :]

                else:
                    # Rare fallback: true delta-style partials (small chunks),
                    # NOT full snapshots. We allow these cautiously.
                    # This helps if ADK sometimes emits tiny token chunks that are not snapshots.
                    if is_partial and len(text) <= 80 and not emitted_text.endswith(text):
                        new_part = text
                    else:
                        # Non-prefix snapshot or duplicate -> ignore to avoid duplication.
                        new_part = ""

                if new_part:
                    saw_any_text = True
                    emitted_text += new_part
                    await websocket.send_json({"type": "chunk", "text": new_part})

            # No events at all – send a friendly error
            if not saw_any_text and report_payload is None:
                await websocket.send_json(
                    {
                        "type": "chunk",
                        "text": "Sorry, I could not generate a response. Please try again.",
                    }
                )
                await websocket.send_json({"type": "done"})
                continue

            # If this was a report, process and stream the final formatted report once.
            if report_payload is not None:
                processed = await process_report(report_payload)
                await websocket.send_json({"type": "chunk", "text": processed})

            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        ws_sessions.pop(id(websocket), None)