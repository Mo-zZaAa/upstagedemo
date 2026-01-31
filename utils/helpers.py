"""
Helpers: ICS calendar generation, Mermaid diagram cleaning, Live Mermaid renderer.
"""

import re
from datetime import date, datetime
from typing import Any

from ics import Calendar, Event


def format_dday(due: str | datetime | None) -> str:
    """Format due date as D-day (D-5, D+3, D-day)."""
    if not due:
        return "-"
    try:
        if isinstance(due, datetime):
            target = due.date()
        else:
            target = datetime.strptime(str(due).strip()[:10], "%Y-%m-%d").date()
        today = date.today()
        delta = (target - today).days
        if delta == 0:
            return "D-day"
        if delta > 0:
            return f"D-{delta}"
        return f"D+{abs(delta)}"
    except (ValueError, TypeError):
        return str(due)[:10] if due else "-"


def _mermaid_html(code: str, height: int = 500) -> str:
    """
    Simple Mermaid HTML: div.mermaid + startOnLoad for reliable rendering.
    Lighter theme for readability; container scrolls when long.
    """
    # Prevent script injection; Mermaid code rarely has </script>
    safe = code.strip().replace("</script>", "</scr\"+\"ipt>")
    return f"""
<div class="mermaid" style="min-height: {height}px; max-height: 800px; overflow: auto; background:#fafafa; border-radius:12px; padding:1.5rem; border:1px solid #eaeaea;">
{safe}
</div>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{
    startOnLoad: true,
    theme: 'base',
    themeVariables: {{
      primaryColor: '#c4b5fd',
      primaryTextColor: '#4b5563',
      primaryBorderColor: '#a78bfa',
      lineColor: '#9ca3af',
      secondaryColor: '#e9d5ff',
      tertiaryColor: '#f5f3ff',
      edgeLabelBackground: '#ffffff'
    }}
  }});
</script>
"""


def _sanitize_mermaid_code(code: str) -> str:
    """
    Fix common Mermaid syntax errors: special chars in labels, reserved words.
    """
    if not code or not code.strip():
        return ""
    s = code.strip()
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)

    def fix_label(match: re.Match) -> str:
        inner = match.group(1)
        inner = inner.replace('"', "'").replace(":", "-").replace(";", ",")
        inner = re.sub(r"[\[\]{}()]", " ", inner)
        inner = re.sub(r"\s+", " ", inner).strip()
        if inner.lower() == "end":
            inner = "End"
        return f"[{inner}]" if inner else "[Node]"

    s = re.sub(r"\[([^\]]*)\]", fix_label, s)
    s = re.sub(r"\(([^)]*)\)", lambda m: f"({m.group(1).replace('"', "'")})", s)
    if not re.search(r"^\s*(graph|flowchart)\s+", s, re.I):
        s = "graph TD\n" + s
    return s


def _normalize_mermaid_for_graph(code: str) -> str:
    """Clean and sanitize Mermaid code for reliable rendering."""
    cleaned = clean_mermaid(code or "")
    return _sanitize_mermaid_code(cleaned)


def render_mermaid(code: str, height: int = 500) -> str:
    """
    Produce HTML block with Mermaid.js (CDN) to render the diagram.
    Uses div.mermaid + startOnLoad for reliable display. Fallback: empty string.
    """
    cleaned = _normalize_mermaid_for_graph(clean_mermaid(code or ""))
    if not cleaned.strip():
        return ""
    return _mermaid_html(cleaned, height=height)


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
