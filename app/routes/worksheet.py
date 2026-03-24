"""Worksheet API endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app import database as db
from app.models import WorksheetRequest, WorksheetSubmission
from app.services import worksheet_service

router = APIRouter(prefix="/api/worksheet", tags=["worksheet"])


@router.get("/list")
async def list_worksheets(student_id: str = "default"):
    """List all saved worksheets for a student."""
    return await db.list_worksheets(student_id)


@router.post("/generate")
async def generate_worksheet(request: WorksheetRequest):
    """Generate a new worksheet."""
    try:
        ws = await worksheet_service.generate_worksheet(request)
        return ws.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{worksheet_id}")
async def get_worksheet(worksheet_id: str):
    """Retrieve a worksheet by ID."""
    ws = await worksheet_service.get_worksheet(worksheet_id)
    if ws is None:
        raise HTTPException(status_code=404, detail="Worksheet not found")
    return ws.model_dump()


@router.get("/{worksheet_id}/print", response_class=HTMLResponse)
async def print_worksheet(worksheet_id: str, answers: bool = False):
    """Render a print-friendly HTML version of the worksheet."""
    ws = await worksheet_service.get_worksheet(worksheet_id)
    if ws is None:
        raise HTTPException(status_code=404, detail="Worksheet not found")
    return worksheet_service.render_worksheet_html(ws, show_answers=answers)


@router.post("/score")
async def score_worksheet(submission: WorksheetSubmission):
    """Score a submitted worksheet and update student progress."""
    try:
        result = await worksheet_service.score_worksheet(submission)
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
