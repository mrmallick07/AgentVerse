"""
FastAPI Routes — Chat endpoint and dashboard data API.
"""

import uuid
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from backend.agents.orchestrator import orchestrator_agent
from backend.database import create_task, get_tasks, save_session_message, get_session_history
router = APIRouter()

# Session management
session_service = InMemorySessionService()
APP_NAME = "agentverse"

# Create the runner
runner = Runner(
    agent=orchestrator_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


async def stream_agent_response(session_id: str, message: str):
    """Stream agent response events via SSE."""
    try:
        # Ensure session exists
        try:
            session = await session_service.get_session(
                app_name=APP_NAME,
                user_id="user",
                session_id=session_id,
            )
        except Exception:
            session = None

        if session is None:
            session = await session_service.create_session(
                app_name=APP_NAME,
                user_id="user",
                session_id=session_id,
            )

        # Create the user message
        user_content = types.Content(
            role="user",
            parts=[types.Part(text=message)],
        )

        # Stream events from the runner
        async for event in runner.run_async(
            user_id="user",
            session_id=session_id,
            new_message=user_content,
        ):
            # Send agent activity events
            if event.author:
                event_data = {
                    "type": "agent_activity",
                    "agent": event.author,
                }

                # Check for tool calls in actions
                if event.actions and event.actions.tool_code_execution_result:
                    event_data["type"] = "tool_result"
                    event_data["tool"] = "code_execution"

                yield f"data: {json.dumps(event_data)}\n\n"

            # Send text content
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        text_event = {
                            "type": "text",
                            "agent": event.author or "OrchestratorAgent",
                            "content": part.text,
                        }
                        yield f"data: {json.dumps(text_event)}\n\n"

                    # Track function calls
                    if part.function_call:
                        tool_event = {
                            "type": "tool_call",
                            "agent": event.author or "Unknown",
                            "tool": part.function_call.name,
                            "args": str(dict(part.function_call.args or {}))[:200],
                        }
                        yield f"data: {json.dumps(tool_event)}\n\n"

                    # Track function responses
                    if part.function_response:
                        resp_data = part.function_response.response
                        # Safely extract status
                        status = "unknown"
                        if isinstance(resp_data, dict):
                            status = resp_data.get("status", "completed")
                        tool_resp_event = {
                            "type": "tool_response",
                            "agent": event.author or "Unknown",
                            "tool": part.function_response.name,
                            "status": status,
                        }
                        yield f"data: {json.dumps(tool_resp_event)}\n\n"

        # Final done event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        error_event = {"type": "error", "content": str(e)}
        yield f"data: {json.dumps(error_event)}\n\n"


@router.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint — streams agent activity and responses via SSE."""
    session_id = request.session_id or str(uuid.uuid4())

    return StreamingResponse(
        stream_agent_response(session_id, request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-Id": session_id,
        },
    )


@router.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "app": "AgentVerse", "agents": 5}
class TaskRequest(BaseModel):
    session_id: str
    title: str
    description: str = ""


@router.post("/api/tasks")
async def add_task(request: TaskRequest):
    """Create a new task in Firestore."""
    task = create_task(request.session_id, request.title, request.description)
    return task


@router.get("/api/tasks/{session_id}")
async def list_tasks(session_id: str):
    """Get all tasks for a session."""
    tasks = get_tasks(session_id)
    return {"tasks": tasks}


@router.get("/api/history/{session_id}")
async def chat_history(session_id: str):
    """Get chat history for a session."""
    history = get_session_history(session_id)
    return {"history": history}