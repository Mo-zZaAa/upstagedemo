"""
Helpers: ICS calendar generation, Mermaid diagram cleaning, Live Mermaid renderer.
"""

import json
import re
from datetime import datetime
from typing import Any

from ics import Calendar, Event


MERMAID_HTML_TEMPLATE = """
<div class="mermaid-container" style="background:#fff;border-radius:12px;padding:1.5rem;border:1px solid #eaeaea;">
  <div class="mermaid-diagram" id="mermaid-target"></div>
</div>
<script type="application/json" id="mermaid-src">{code_json}</script>
<script type="module">
  const src = document.getElementById('mermaid-src');
  const target = document.getElementById('mermaid-target');
  if (src && target) {
    try {
      const code = JSON.parse(src.textContent || '""');
      if (!code || !code.trim()) return;
      const mermaid = (await import('https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs')).default;
      mermaid.initialize({
        startOnLoad: false,
        theme: 'base',
        themeVariables: {
          primaryColor: '#8B5CF6',
          primaryTextColor: '#374151',
          primaryBorderColor: '#8B5CF6',
          lineColor: '#6b7280',
          secondaryColor: '#f3f4f6',
          tertiaryColor: '#ffffff',
          edgeLabelBackground: '#ffffff'
        }
      });
      const { svg } = await mermaid.render('mermaid-' + Math.random().toString(36).slice(2), code.trim());
      target.innerHTML = svg;
    } catch (e) {
      target.innerHTML = '<p style="color:#9ca3af;font-size:0.9rem;">다이어그램 렌더링 실패</p>';
    }
  }
</script>
"""


def _normalize_mermaid_for_graph(code: str) -> str:
    """
    Strip invalid characters. Prefer graph TD/LR for clear hierarchy.
    Mindmap is passed through (Mermaid supports it).
    """
    if not code or not code.strip():
        return ""
    s = code.strip()
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)
    # If no diagram type, default to graph TD
    if not re.search(r"^\s*(graph|mindmap|flowchart)\s+", s, re.IGNORECASE):
        s = "graph TD\n" + s
    return s


def render_mermaid(code: str) -> str:
    """
    Produce HTML block with Mermaid.js (CDN) to render the diagram.
    Cleans code to use graph TD/LR, strips invalid chars, applies purple theme.
    """
    cleaned = _normalize_mermaid_for_graph(clean_mermaid(code or ""))
    if not cleaned.strip():
        return ""
    code_json = json.dumps(cleaned)
    return MERMAID_HTML_TEMPLATE.replace("{code_json}", code_json)


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
