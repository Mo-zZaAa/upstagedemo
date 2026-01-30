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

from utils.prompts import STRUCTURE_PROMPT, ACTION_PROMPT, EXECUTIVE_SUMMARY_PROMPT
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

    def analyze(self, context: str) -> dict[str, Any]:
        """
        Run structure, action extraction, and executive summary on the given context.

        Returns:
            {'mermaid': str, 'actions': list, 'executive_summary': dict}
            - executive_summary: {title, summary, core_value, growth_driver}
            - actions: list of {summary, due_date, priority, assignee}
        """
        if not (context and context.strip()):
            return {"mermaid": "", "actions": [], "executive_summary": {}}

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
            "title": str(data.get("title", "")).strip() or "전략 요약",
            "summary": str(data.get("summary", "")).strip() or "",
            "core_value": str(data.get("core_value", "")).strip() or "",
            "growth_driver": str(data.get("growth_driver", "")).strip() or "",
        }

    def _safe_mermaid_output(self, raw: str) -> str:
        """Clean Mermaid and return valid code, or raw text if too messy."""
        cleaned = clean_mermaid(raw or "")
        if not cleaned.strip():
            return raw.strip() if raw else ""
        # Basic sanity: should contain mindmap and root
        if "mindmap" in cleaned and ("root" in cleaned or "Root" in cleaned or "목표" in cleaned):
            return cleaned
        # Otherwise return raw so UI can show something
        return raw.strip() if raw else cleaned

    def _parse_actions(self, raw: str) -> list[dict[str, Any]]:
        """Parse JSON array from LLM output. Return empty list on failure."""
        if not raw or not raw.strip():
            return []
        # Strip markdown code fence if present
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
            out.append({
                "summary": str(item.get("summary", "")).strip() or "(제목 없음)",
                "due_date": item.get("due_date"),
                "priority": item.get("priority") or "Medium",
                "assignee": str(item.get("assignee", "")).strip() or "-",
            })
        return out
