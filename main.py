import os
from typing import List, Optional, Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Event as EventSchema, Storyitem as StoryItemSchema, Chatmessage as ChatMessageSchema, AssistantPrompt

app = FastAPI(title="Event Storyboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utility
class IdModel(BaseModel):
    id: str


def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id format")


@app.get("/")
def read_root():
    return {"message": "Event Storyboard Backend Running"}


# Schema endpoint for tooling
@app.get("/schema")
def get_schema():
    return {
        "collections": [
            {
                "name": "event",
                "fields": EventSchema.model_json_schema(),
            },
            {
                "name": "storyitem",
                "fields": StoryItemSchema.model_json_schema(),
            },
            {
                "name": "chatmessage",
                "fields": ChatMessageSchema.model_json_schema(),
            },
        ]
    }


# Events
@app.get("/events")
def list_events() -> List[Dict[str, Any]]:
    items = get_documents("event", {}, limit=None)
    for it in items:
        it["id"] = str(it.pop("_id"))
    return items


@app.post("/events")
def create_event(payload: EventSchema):
    new_id = create_document("event", payload)
    return {"id": new_id}


# Story items
@app.get("/events/{event_id}/storyitems")
def list_storyitems(event_id: str) -> List[Dict[str, Any]]:
    items = db["storyitem"].find({"event_id": event_id}).sort("position", 1)
    result = []
    for it in items:
        it["id"] = str(it.pop("_id"))
        result.append(it)
    return result


@app.post("/storyitems")
def create_storyitem(payload: StoryItemSchema):
    new_id = create_document("storyitem", payload)
    return {"id": new_id}


class ReorderItem(BaseModel):
    id: str
    position: int


@app.patch("/storyitems/reorder")
def reorder_storyitems(items: List[ReorderItem]):
    for it in items:
        db["storyitem"].update_one({"_id": oid(it.id)}, {"$set": {"position": it.position}})
    return {"status": "ok"}


# Chat
@app.get("/events/{event_id}/chat")
def list_chat(event_id: str) -> List[Dict[str, Any]]:
    items = db["chatmessage"].find({"event_id": event_id}).sort("created_at", 1)
    result = []
    for it in items:
        it["id"] = str(it.pop("_id"))
        result.append(it)
    return result


@app.post("/chat")
def post_chat(msg: ChatMessageSchema):
    new_id = create_document("chatmessage", msg)
    return {"id": new_id}


# Simple AI assistant stub
class AssistantResponse(BaseModel):
    suggestions: List[str]


@app.post("/assistant/suggest", response_model=AssistantResponse)
def assistant_suggest(prompt: AssistantPrompt):
    base = prompt.prompt.lower() if prompt.prompt else ""
    suggestions = [
        "Add a welcome card at the top with venue and dress code.",
        "Insert buffer breaks every 45 minutes to keep timing realistic.",
        "Color-code vendor touchpoints and add contact chips to each card.",
    ]
    if "timeline" in base:
        suggestions.insert(0, "Group timeline into phases: setup, ceremony, reception, teardown.")
    if "budget" in base:
        suggestions.append("Attach cost estimates to each card and auto-sum per phase.")
    return {"suggestions": suggestions[:5]}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
