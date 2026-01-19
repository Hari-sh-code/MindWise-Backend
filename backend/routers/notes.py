"""
Notes Router.
Handles user reference notes for job applications.
IMPORTANT: Notes are stored in DB only and NOT sent to AI.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.note import Note
from models.job import JobApplication
from schemas.note import NoteCreate, NoteResponse, NoteListResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Notes"])


@router.post("/{job_id}/notes", response_model=NoteResponse, status_code=201)
async def create_note(
    job_id: int,
    note_data: NoteCreate,
    db: Session = Depends(get_db)
):
    """
    Create a reference note for a job application.
    
    IMPORTANT: Notes are for tracking purposes only.
    They are stored in the database but NOT sent to AI for analysis.
    """
    # Check if job exists
    job = db.query(JobApplication).filter(JobApplication.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job application not found")
    
    # Create note
    note = Note(
        job_id=job_id,
        content=note_data.content
    )
    
    db.add(note)
    db.commit()
    db.refresh(note)
    
    logger.info(f"Created note {note.id} for job {job_id}")
    
    return note


@router.get("/{job_id}/notes", response_model=NoteListResponse)
async def get_job_notes(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all notes for a specific job application.
    """
    # Check if job exists
    job = db.query(JobApplication).filter(JobApplication.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job application not found")
    
    # Get notes
    notes = db.query(Note).filter(Note.job_id == job_id).order_by(Note.created_at.desc()).all()
    
    return NoteListResponse(
        notes=notes,
        total=len(notes)
    )


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a specific note.
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    db.delete(note)
    db.commit()
    
    logger.info(f"Deleted note {note_id}")
    
    return {"message": "Note deleted successfully"}
