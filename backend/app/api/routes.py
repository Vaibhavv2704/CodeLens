import asyncio
import json
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.models import Goal


def authenticate(request: Request, authorization: str = Header(default="")):
    token = request.app.state.settings.api_token
    if token and not secrets.compare_digest(authorization, f"Bearer {token}"):
        raise HTTPException(401, "Valid API bearer token required")


router = APIRouter(prefix="/api", dependencies=[Depends(authenticate)])


@router.post("/reviews", status_code=202)
def create_review(goal: Goal, request: Request):
    state = request.app.state
    if not state.capacity.acquire(blocking=False):
        raise HTTPException(429, "Review queue is full; try again later")
    try:
        identifier = state.store.create(goal)
        state.executor.submit(state.run_review, identifier, goal)
    except Exception:
        state.capacity.release()
        raise
    return {"id": identifier, "status": "queued"}


@router.get("/reviews")
def list_reviews(request: Request, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    return request.app.state.store.list(limit, offset)


def get_review(request, identifier):
    review = request.app.state.store.get(identifier)
    if review is None:
        raise HTTPException(404, "Review not found")
    return review


@router.get("/reviews/{identifier}")
def review_detail(identifier: str, request: Request):
    review = get_review(request, identifier)
    review["events"] = request.app.state.store.events(identifier)
    return review


@router.get("/reviews/{identifier}/report")
def review_report(identifier: str, request: Request):
    review = get_review(request, identifier)
    if review["report"] is None:
        raise HTTPException(409, "Review is still running")
    return review["report"]


@router.get("/reviews/{identifier}/events")
async def events(identifier: str, request: Request, after: int = Query(0, ge=0)):
    get_review(request, identifier)

    async def stream():
        cursor = after
        while not await request.is_disconnected():
            batch = await asyncio.to_thread(request.app.state.store.events, identifier, cursor)
            for event in batch:
                cursor = event["id"]
                yield f"id: {cursor}\ndata: {json.dumps(event)}\n\n"
            review = await asyncio.to_thread(request.app.state.store.get, identifier)
            if review["status"] in {"completed", "failed"} and len(batch) < 500:
                yield "event: done\ndata: {}\n\n"
                break
            yield ": heartbeat\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

