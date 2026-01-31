"""
Solar Pro Reasoning Logic (Chain).
LangChain-based reasoning for mindmap & action extraction.
"""

import json
import re
from typing import Any

from langchain_upstage import ChatUpstage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from utils.prompts import (
    STRUCTURE_PROMPT,
    ACTION_PROMPT,
    EXECUTIVE_SUMMARY_PROMPT,
    GAP_ANALYSIS_PROMPT,
)
from utils.helpers import clean_mermaid


class ThinkFlowAgent:
    """
    Agent that runs structure (mindmap), action extraction, and executive summary chains.
    Returns {'mermaid': str, 'actions': list, 'executive_summary': dict}.
    """

    def __init__(self, model: str = "solar-pro"):
        self.llm = ChatUpstage(model=model)
        self._structure_chain = (
            {"context": RunnablePassthrough()}
            | STRUCTURE_PROMPT
            | self.llm
            | StrOutputParser()
        )
        self._action_chain = (
            {"context": RunnablePassthrough()}
            | ACTION_PROMPT
            | self.llm
            | StrOutputParser()
        )
        self._executive_chain = (
            {"context": RunnablePassthrough()}
            | EXECUTIVE_SUMMARY_PROMPT
            | self.llm
            | StrOutputParser()
        )
        self._gap_chain = (
            {"context": RunnablePassthrough()}
            | GAP_ANALYSIS_PROMPT
            | self.llm
            | StrOutputParser()
        )

    def check_gaps(self, context: str) -> dict[str, Any]:
        """
        Check if input has enough critical info (goal, deadline, assignee).
        Returns: {"ready": bool, "missing": list[str]}.
        """
        if not (context and context.strip()):
            return {"ready": False, "missing": ["목표", "마감일", "담당자"]}
        try:
            raw = self._gap_chain.invoke({"context": context.strip()})
            return self._parse_gap(raw)
        except Exception:
            return {"ready": True, "missing": []}

    def _parse_gap(self, raw: str) -> dict[str, Any]:
        if not raw or not raw.strip():
            return {"ready": True, "missing": []}
        text = raw.strip()
        code_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if code_match:
            text = code_match.group(1).strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return {"ready": True, "missing": []}
        if not isinstance(data, dict):
            return {"ready": True, "missing": []}
        ready = data.get("ready", True)
        missing = data.get("missing", [])
        if not isinstance(missing, list):
            missing = []
        return {"ready": ready, "missing": missing}

    def analyze(self, context: str) -> dict[str, Any]:
        """
        Run gap check first. If info missing, return need_clarification.
        Else run structure, action extraction, and executive summary.

        Returns:
            Either { "need_clarification": True, "missing": [...] }
            Or { "mermaid", "actions", "executive_summary" }
        """
        if not (context and context.strip()):
            return {"mermaid": "", "actions": [], "executive_summary": {}}

        gap = self.check_gaps(context)
        if not gap.get("ready", True):
            return {
                "need_clarification": True,
                "missing": gap.get("missing", ["마감일", "담당자"]),
            }

        # Executive summary
        try:
            exec_raw = self._executive_chain.invoke({"context": context.strip()})
            executive_summary = self._parse_executive_summary(exec_raw)
        except Exception:
            executive_summary = {}

        # Run structure chain
        try:
            mermaid_raw = self._structure_chain.invoke({"context": context.strip()})
        except Exception as e:
            mermaid_raw = f"[Structure generation failed: {e}]"
        mermaid_out = self._safe_mermaid_output(mermaid_raw)

        # Run action chain
        try:
            action_raw = self._action_chain.invoke({"context": context.strip()})
        except Exception:
            action_raw = "[]"
        actions = self._parse_actions(action_raw)

        return {
            "mermaid": mermaid_out,
            "actions": actions,
            "executive_summary": executive_summary,
        }

    def _parse_executive_summary(self, raw: str) -> dict[str, Any]:
        """Parse JSON object from LLM output. Return empty dict on failure."""
        if not raw or not raw.strip():
            return {}
        text = raw.strip()
        code_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if code_match:
            text = code_match.group(1).strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        return {
            "subject": str(data.get("subject", "")).strip() or str(data.get("title", "")).strip() or "전략 요약",
            "overview": str(data.get("overview", "")).strip() or str(data.get("summary", "")).strip() or "",
            "main_kpi": str(data.get("main_kpi", "")).strip() or str(data.get("core_value", "")).strip() or "",
            "sub_metrics": str(data.get("sub_metrics", "")).strip() or str(data.get("growth_driver", "")).strip() or "",
        }

    def _safe_mermaid_output(self, raw: str) -> str:
        """Clean Mermaid and return valid code, or raw text if too messy."""
        cleaned = clean_mermaid(raw or "")
        if not cleaned.strip():
            return raw.strip() if raw else ""
        if re.search(r"graph\s+(TD|LR|TB|RL)", cleaned, re.IGNORECASE) or "mindmap" in cleaned:
            return cleaned
        return raw.strip() if raw else cleaned

    def _parse_actions(self, raw: str) -> list[dict[str, Any]]:
        """Parse JSON array from LLM output. Return empty list on failure."""
        if not raw or not raw.strip():
            return []
        text = raw.strip()
        code_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if code_match:
            text = code_match.group(1).strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        out: list[dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            level = item.get("level")
            if level is None:
                level = 1
            try:
                level = int(level) if level is not None else 1
            except (ValueError, TypeError):
                level = 1
            level = 1 if level not in (1, 2) else level
            dep = str(item.get("dependency", "")).strip() or ""
            suggestion = str(item.get("ai_suggestion", "")).strip() or ""
            out.append({
                "summary": str(item.get("summary", "")).strip() or "(제목 없음)",
                "due_date": item.get("due_date"),
                "priority": item.get("priority") or "Medium",
                "level": level,
                "dependency": dep,
                "ai_suggestion": suggestion,
            })
        return out
