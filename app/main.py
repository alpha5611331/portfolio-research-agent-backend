from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, UTC
import asyncio
import uuid
import json

from app.models.schemas import ResearchRequest, ResearchResponse, SessionSummary
from app.graph import graph
from app.state import ResearchState
from app.db.qdrant_client import ensure_collection

_sessions: dict[str, dict] = {}
_ws_queues: dict[str, asyncio.Queue] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await ensure_collection()
    except Exception:
        pass
    yield


app = FastAPI(title="Research Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


async def _emit(session_id: str, event: str, agent: str, data: dict, subtopic: str | None = None):
    q = _ws_queues.get(session_id)
    if q:
        await q.put({
            "event": event,
            "session_id": session_id,
            "timestamp": _now(),
            "agent": agent,
            "subtopic": subtopic,
            "data": data,
        })


async def _run_research(session_id: str, request: ResearchRequest):
    state: ResearchState = {
        "query": request.query,
        "session_id": session_id,
        "subtopics": [],
        "results": [],
        "report": "",
        "error": None,
    }

    try:
        async for event in graph.astream_events(state, version="v2"):
            kind = event["event"]
            name = event.get("name", "")

            if kind == "on_chain_end" and name == "planner":
                subtopics = event["data"]["output"].get("subtopics", [])
                await _emit(session_id, "PLAN_CREATED", "planner", {"subtopics": subtopics})

            elif kind == "on_chain_end" and name == "researcher":
                results = event["data"]["output"].get("results", [])
                for r in results:
                    await _emit(session_id, "SOURCES_COLLECTED", "researcher",
                                {"sources": r["sources"], "count": len(r["sources"])},
                                subtopic=r["subtopic"])

            elif kind == "on_chain_end" and name == "summarizer":
                results = event["data"]["output"].get("results", [])
                for r in results:
                    await _emit(session_id, "SUMMARY_DONE", "summarizer",
                                {"summary": r["summary"]}, subtopic=r["subtopic"])

            elif kind == "on_chat_model_stream" and "synthesizer" in str(event.get("tags", [])):
                chunk = event["data"]["chunk"].content
                if chunk:
                    await _emit(session_id, "REPORT_CHUNK", "synthesizer", {"chunk": chunk})

            elif kind == "on_chain_end" and name == "synthesizer":
                report = event["data"]["output"].get("report", "")
                _sessions[session_id]["report"] = report
                _sessions[session_id]["status"] = "done"
                await _emit(session_id, "REPORT_DONE", "synthesizer", {"report": report})

    except Exception as e:
        _sessions[session_id]["status"] = "error"
        await _emit(session_id, "ERROR", "orchestrator", {"message": str(e)})
    finally:
        q = _ws_queues.get(session_id)
        if q:
            await q.put(None)


@app.post("/api/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest):
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "session_id": session_id,
        "query": request.query,
        "created_at": _now(),
        "status": "running",
        "report": "",
    }
    _ws_queues[session_id] = asyncio.Queue()
    asyncio.create_task(_run_research(session_id, request))
    return ResearchResponse(session_id=session_id)


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    if session_id not in _sessions:
        await websocket.close(code=4004)
        return

    await websocket.accept()
    q = _ws_queues.get(session_id)
    if q is None:
        await websocket.close(code=4004)
        return

    try:
        while True:
            msg = await q.get()
            if msg is None:
                break
            await websocket.send_text(json.dumps(msg))
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()


@app.get("/api/research/{session_id}")
async def get_session(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/api/sessions", response_model=list[SessionSummary])
async def list_sessions():
    return [
        SessionSummary(
            session_id=s["session_id"],
            query=s["query"],
            created_at=s["created_at"],
            status=s["status"],
        )
        for s in sorted(_sessions.values(), key=lambda x: x["created_at"], reverse=True)
    ]


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    del _sessions[session_id]
    _ws_queues.pop(session_id, None)
    return {"ok": True}
