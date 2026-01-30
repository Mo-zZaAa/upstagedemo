"""
Helpers: ICS calendar generation, Mermaid diagram cleaning.
"""

import re
from datetime import datetime
from typing import Any

from ics import Calendar, Event


def clean_mermaid(text: str) -> str:
    """
    Remove markdown code fences (```mermaid, ```) to prevent rendering errors.
    Returns trimmed Mermaid code only.
    """
    if not text or not text.strip():
        return ""
    s = text.strip()
    # Remove opening ```mermaid or ``` (with optional whitespace/newline)
    s = re.sub(r"^```\s*mer?maid?\s*\n?", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^```\s*\n?", "", s)
    # Remove closing ```
    s = re.sub(r"\n?\s*```\s*$", "", s)
    return s.strip()


def generate_ics(action_list: list[dict[str, Any]]) -> bytes:
    """
    Convert a list of action dicts into a downloadable .ics file as bytes.

    Each dict should have:
      - summary: str (event title)
      - due_date: str "YYYY-MM-DD" or None
      - priority: str (optional, ignored for ICS event)

    Actions without a valid due_date are skipped or use today as fallback (you can change).
    """
    cal = Calendar()
    added = 0
    for i, action in enumerate(action_list or []):
        if not isinstance(action, dict):
            continue
        summary = action.get("summary") or "(제목 없음)"
        due = action.get("due_date")
        if not due:
            continue
        try:
            # Parse YYYY-MM-DD
            if isinstance(due, datetime):
                begin = due
            else:
                begin = datetime.strptime(str(due).strip()[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            continue
        # All-day event: start 09:00, end 10:00 same day
        end = begin.replace(hour=10, minute=0, second=0, microsecond=0)
        begin = begin.replace(hour=9, minute=0, second=0, microsecond=0)
        event = Event()
        event.name = summary[:255]
        event.begin = begin
        event.end = end
        event.uid = f"thinkflow-{i}-{begin.strftime('%Y%m%d')}@thinkflow"
        cal.events.add(event)
        added += 1
    if not added:
        return b""
    return cal.serialize().encode("utf-8")
