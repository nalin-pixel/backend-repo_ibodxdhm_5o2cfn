"""
Database Schemas for Event Storyboard Platform

Each Pydantic model represents a MongoDB collection.
Collection name is the lowercase of the class name.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Event(BaseModel):
    title: str = Field(..., description="Event title")
    date: Optional[str] = Field(None, description="ISO date string for the event day")
    description: Optional[str] = Field(None, description="Short description")
    theme: Optional[str] = Field(None, description="Color or style theme")

class Storyitem(BaseModel):
    event_id: str = Field(..., description="Related event id as string")
    title: str = Field(..., description="Card title")
    time: Optional[str] = Field(None, description="Time label, e.g., 09:30 AM")
    notes: Optional[str] = Field(None, description="Additional notes")
    position: int = Field(0, description="Order index within timeline")
    color: Optional[str] = Field(None, description="Card accent color")

class Chatmessage(BaseModel):
    event_id: str = Field(..., description="Related event id as string")
    user: str = Field(..., description="Sender display name")
    text: str = Field(..., description="Message content")
    created_at: Optional[datetime] = Field(None, description="Server timestamp")

# Optional: Basic assistant prompt schema
class AssistantPrompt(BaseModel):
    prompt: str = Field(..., description="User prompt or context")
    event_id: Optional[str] = Field(None, description="Optional event scope")
