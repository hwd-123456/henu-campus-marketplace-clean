from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import get_current_user
from app.core.mongodb import get_database
from app.models.errand import ErrandAction, ErrandCreate

router = APIRouter(prefix="/api/v1/errands", tags=["Errands"])


def _serialize(doc: dict) -> dict:
    """Shape stored documents into the unified field contract."""
    return {
        "task_id": doc.get("task_id"),
        "creator_id": doc.get("creator_id"),
        "claimer_id": doc.get("claimer_id"),
        "campus": doc.get("campus"),
        "title": doc.get("title"),
        "origin": doc.get("origin"),
        "destination": doc.get("destination"),
        "reward": doc.get("reward"),
        "status": doc.get("status"),
        "note": doc.get("note"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


@router.get("")
async def list_errands(
    campus: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    db = get_database()
    query = {}
    if campus:
        query["campus"] = campus
    if status:
        query["status"] = status
    cursor = db["errands"].find(query).sort("created_at", -1)
    return [_serialize(doc) async for doc in cursor]


@router.post("", status_code=201)
async def create_errand(payload: ErrandCreate, current=Depends(get_current_user)):
    db = get_database()
    now = datetime.utcnow().isoformat()
    doc = {
        "task_id": f"task-{uuid.uuid4().hex[:12]}",
        "creator_id": current["sub"],
        "claimer_id": None,
        **payload.model_dump(),
        "status": "open",
        "note": None,
        "created_at": now,
        "updated_at": now,
    }
    await db["errands"].insert_one(doc)
    return _serialize(doc)


async def _get_task(db, task_id: str) -> dict:
    doc = await db["errands"].find_one({"task_id": task_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Errand task not found")
    return doc


@router.post("/{task_id}/claim")
async def claim_errand(
    task_id: str,
    payload: ErrandAction | None = None,
    current=Depends(get_current_user),
):
    db = get_database()
    doc = await _get_task(db, task_id)
    if doc["status"] != "open":
        raise HTTPException(status_code=409, detail=f"Task is {doc['status']}, not open")
    if doc["creator_id"] == current["sub"]:
        raise HTTPException(status_code=409, detail="Creator cannot claim own task")

    update = {
        "$set": {
            "claimer_id": current["sub"],
            "status": "claimed",
            "updated_at": datetime.utcnow().isoformat(),
        }
    }
    if payload and payload.note:
        update["$set"]["note"] = payload.note
    await db["errands"].update_one({"task_id": task_id}, update)
    return _serialize(await _get_task(db, task_id))


@router.post("/{task_id}/complete")
async def complete_errand(
    task_id: str,
    payload: ErrandAction | None = None,
    current=Depends(get_current_user),
):
    db = get_database()
    doc = await _get_task(db, task_id)
    if doc["status"] != "claimed":
        raise HTTPException(
            status_code=409, detail=f"Task is {doc['status']}, only claimed tasks can be completed"
        )
    if current["sub"] not in (doc["creator_id"], doc.get("claimer_id")):
        raise HTTPException(status_code=403, detail="Only creator or claimer can complete the task")

    update = {"$set": {"status": "completed", "updated_at": datetime.utcnow().isoformat()}}
    if payload and payload.note:
        update["$set"]["note"] = payload.note
    await db["errands"].update_one({"task_id": task_id}, update)
    return _serialize(await _get_task(db, task_id))
