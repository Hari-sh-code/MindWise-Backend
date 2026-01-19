"""
Pydantic schemas for Note endpoints.
"""
from pydantic import BaseModel
from typing import List
from datetime import datetime


class NoteBase(BaseModel):
    """Base schema for note."""
    content: str


class NoteCreate(NoteBase):
    """Schema for creating a note."""
    pass


class NoteResponse(NoteBase):
    """Schema for note response."""
    id: int
    job_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    """Schema for note list response."""
    notes: List[NoteResponse]
    total: int
