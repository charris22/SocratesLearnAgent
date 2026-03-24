"""Worksheet generation, scoring, and PDF-ready output."""

import json
import logging

from app.azure_client import get_openai_client
from app import database as db
from app.config import get_settings
from app.models import (
    AnswerEntry,
    Difficulty,
    LearningEventKind,
    ScoredItem,
    Worksheet,
    WorksheetItem,
    WorksheetRequest,
    WorksheetResult,
    WorksheetSubmission,
)
from app.prompts import WORKSHEET_GENERATION_PROMPT, WORKSHEET_SCORING_PROMPT
from app.services import progress_service

logger = logging.getLogger(__name__)


async def generate_worksheet(request: WorksheetRequest) -> Worksheet:
    """Generate a worksheet using Azure OpenAI."""
    client = get_openai_client()
    settings = get_settings()

    title = f"{request.subject} – {request.topic} Worksheet"

    prompt = WORKSHEET_GENERATION_PROMPT.format(
        num_items=request.num_items,
        subject=request.subject,
        topic=request.topic,
        difficulty=request.difficulty.value,
        title=title,
    )

    response = await client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=3000,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)

    items: list[WorksheetItem] = []
    for item in data.get("items", []):
        diff_raw = item.get("difficulty", request.difficulty.value).lower()
        try:
            diff = Difficulty(diff_raw)
        except ValueError:
            diff = request.difficulty

        items.append(WorksheetItem(
            number=item["number"],
            question=item["question"],
            answer_key=item.get("answer_key", "") if request.include_answer_key else "",
            concept=item.get("concept", request.topic),
            difficulty=diff,
            points=item.get("points", 1),
        ))

    worksheet = Worksheet(
        title=title,
        subject=request.subject,
        topic=request.topic,
        difficulty=request.difficulty,
        items=items,
        student_id=request.student_id,
    )
    await db.save_worksheet({
        "id": worksheet.id,
        "title": worksheet.title,
        "subject": worksheet.subject,
        "topic": worksheet.topic,
        "difficulty": worksheet.difficulty.value,
        "items": [item.model_dump() for item in worksheet.items],
        "student_id": worksheet.student_id,
    })

    logger.info(
        "Generated worksheet %s: %d items for %s/%s",
        worksheet.id, len(items), request.subject, request.topic,
    )
    return worksheet


async def get_worksheet(worksheet_id: str) -> Worksheet | None:
    """Retrieve a worksheet by ID."""
    row = await db.get_worksheet_row(worksheet_id)
    if row is None:
        return None
    items = [WorksheetItem(**item) for item in row["items"]]
    return Worksheet(
        id=row["id"],
        title=row["title"],
        subject=row["subject"],
        topic=row["topic"],
        difficulty=Difficulty(row["difficulty"]),
        items=items,
        student_id=row.get("student_id", ""),
        created_at=row.get("created_at"),
    )


async def score_worksheet(submission: WorksheetSubmission) -> WorksheetResult:
    """Score a submitted worksheet using AI-assisted grading."""
    worksheet = await get_worksheet(submission.worksheet_id)
    if worksheet is None:
        raise ValueError(f"Unknown worksheet: {submission.worksheet_id}")

    # Build lookup of student answers by question number
    answer_map: dict[int, str] = {a.number: a.student_answer for a in submission.answers}

    # Prepare items for the scoring prompt
    items_for_prompt = []
    for item in worksheet.items:
        items_for_prompt.append({
            "number": item.number,
            "question": item.question,
            "correct_answer": item.answer_key,
            "student_answer": answer_map.get(item.number, "(blank)"),
            "points": item.points,
        })

    client = get_openai_client()
    settings = get_settings()

    prompt = WORKSHEET_SCORING_PROMPT.format(
        subject=worksheet.subject,
        topic=worksheet.topic,
        items_json=json.dumps(items_for_prompt, indent=2),
    )

    response = await client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)

    scored_items: list[ScoredItem] = []
    total_earned = 0

    for scored in data.get("scored_items", []):
        num = scored["number"]
        ws_item = next((i for i in worksheet.items if i.number == num), None)
        is_correct = scored.get("correct", False)
        earned = scored.get("earned_points", 1 if is_correct else 0)
        total_earned += earned

        scored_items.append(ScoredItem(
            number=num,
            correct=is_correct,
            student_answer=answer_map.get(num, "(blank)"),
            correct_answer=ws_item.answer_key if ws_item else "",
            feedback=scored.get("feedback", ""),
            concept=ws_item.concept if ws_item else "",
        ))

        # Update concept mastery
        if ws_item:
            await progress_service.record_concept(
                student_id=submission.student_id,
                concept=ws_item.concept,
                subject=worksheet.subject,
                correct=is_correct,
            )
            await progress_service.record_event(
                student_id=submission.student_id,
                kind=LearningEventKind.WORKSHEET,
                subject=worksheet.subject,
                concept=ws_item.concept,
                correct=is_correct,
            )

    total_points = worksheet.total_points
    pct = round((total_earned / total_points * 100) if total_points > 0 else 0, 1)

    recommendations = data.get("recommendations", [])

    logger.info(
        "Scored worksheet %s: %d/%d (%.0f%%)",
        submission.worksheet_id, total_earned, total_points, pct,
    )

    return WorksheetResult(
        worksheet_id=submission.worksheet_id,
        total=total_points,
        earned=total_earned,
        percentage=pct,
        items=scored_items,
        recommendations=recommendations,
    )


def render_worksheet_html(worksheet: Worksheet, show_answers: bool = False) -> str:
    """Render a print-friendly HTML page for a worksheet."""
    items_html = ""
    for item in worksheet.items:
        items_html += f"""
        <div class="ws-item">
          <div class="ws-q">
            <strong>{item.number}.</strong> {item.question}
            <span class="ws-pts">({item.points} pt{"s" if item.points != 1 else ""})</span>
          </div>
          <div class="ws-answer-space"></div>
          {"<div class='ws-key'>Answer: " + item.answer_key + "</div>" if show_answers else ""}
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>{worksheet.title}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css"/>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{{delimiters:[
    {{left:'$$',right:'$$',display:true}},
    {{left:'$',right:'$',display:false}}
  ]}})"></script>
<style>
  @media print {{ @page {{ margin: 1in; }} }}
  body {{ font-family: 'Segoe UI', sans-serif; max-width: 8in; margin: 0 auto;
         padding: 0.5in; color: #1c1917; }}
  h1 {{ font-size: 1.4rem; border-bottom: 2px solid #ea580c; padding-bottom: .4rem; }}
  .ws-meta {{ color: #57534e; font-size: .85rem; margin-bottom: 1.5rem; }}
  .ws-item {{ margin-bottom: 1.4rem; page-break-inside: avoid; }}
  .ws-q {{ line-height: 1.6; }}
  .ws-pts {{ color: #a8a29e; font-size: .8rem; }}
  .ws-answer-space {{ border-bottom: 1px solid #d1c7bb; height: 3rem; margin-top: .5rem; }}
  .ws-key {{ margin-top: .3rem; padding: .4rem .6rem; background: #fff7ed;
             border-left: 3px solid #ea580c; font-size: .85rem; color: #57534e; }}
  .ws-footer {{ margin-top: 2rem; text-align: center; font-size: .75rem; color: #a8a29e; }}
</style>
</head>
<body>
  <h1>{worksheet.title}</h1>
  <div class="ws-meta">
    Name: ______________________________&nbsp;&nbsp;&nbsp;Date: ______________&nbsp;&nbsp;&nbsp;
    Total: {worksheet.total_points} points
  </div>
  {items_html}
  <div class="ws-footer">
    Worksheet ID: {worksheet.id} &middot; Generated by Socrates Learn Agent
  </div>
</body>
</html>"""
