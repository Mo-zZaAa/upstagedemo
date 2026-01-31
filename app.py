"""
ThinkFlow - Active Thinking Partner
Context-Aware UX: Guidance Mode, Gap Analysis, Clean Design (no emojis).
"""

import logging
import os
import tempfile
from pathlib import Path
from datetime import datetime

import streamlit as st  # type: ignore[reportMissingImports]

logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)

from dotenv import load_dotenv  # type: ignore[reportMissingImports]
load_dotenv(Path(__file__).resolve().parent / ".env")

def _inject_secrets_to_env():
    if os.environ.get("UPSTAGE_API_KEY"):
        return
    try:
        val = st.secrets["UPSTAGE_API_KEY"]
    except (KeyError, TypeError, AttributeError):
        val = getattr(st.secrets, "UPSTAGE_API_KEY", None)
    if val:
        os.environ["UPSTAGE_API_KEY"] = str(val).strip()


def check_api_key() -> bool:
    return bool(os.environ.get("UPSTAGE_API_KEY", "").strip())


# ---- Clean design: mild colors, no emojis ----
STYLES = """
<style>
  .stApp { background: #fafafb; }
  [data-testid="stSidebar"] { background: #f0f0f3; }
  [data-testid="stSidebar"] .stMarkdown { color: #374151; }
  h1 { font-size: 1.75rem !important; color: #374151 !important; font-weight: 700 !important; font-family: -apple-system, BlinkMacSystemFont, sans-serif !important; }
  h2 { font-size: 1.35rem !important; color: #374151 !important; font-weight: 600 !important; }
  h3 { font-size: 1.15rem !important; color: #374151 !important; font-weight: 600 !important; }
  .thinkflow-logo { font-size: 2rem; font-weight: 700; color: #8b7aa8; letter-spacing: -0.02em; font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin-bottom: 0; }
  .thinkflow-logo-hero { font-size: 2.25rem; font-weight: 700; color: #8b7aa8; letter-spacing: -0.02em; font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin-bottom: 1rem; }
  .char-count { font-size: 0.8rem; color: #6b7280; margin-top: 4px; }
  .card-box {
    background: #ffffff;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    margin-bottom: 1rem;
    border: 1px solid #eaeaea;
  }
  .card-value { font-weight: 600; color: #8b7aa8; }
  .card-label { font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
  .empty-card { background: #f0f0f3; color: #6b7280; border: 1px dashed #d1d5db; }
  .section-title { font-size: 0.75rem; color: #8b7aa8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px; font-weight: 600; }
  .stButton > button {
    background: linear-gradient(90deg, #9f8fbb, #b8a9c9) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    width: 100%;
  }
  .stButton > button:hover { opacity: 0.92; box-shadow: 0 2px 6px rgba(139,122,168,0.25); }
  .success-box { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 0.75rem 1rem; margin: 0.5rem 0; }
  .clarification-box { background: #fffbeb; border: 1px solid #fde68a; border-radius: 12px; padding: 1.25rem; margin: 1rem 0; }
  .footer-text { font-size: 0.7rem; color: #9ca3af; margin-top: 2rem; }
  .empty-hero { text-align: center; padding: 3rem 2rem; color: #374151; }
  .empty-hero h2 { font-size: 1.25rem; font-weight: 600; color: #4b5563; margin-bottom: 0.5rem; }
  .empty-hero p { color: #6b7280; font-size: 0.95rem; line-height: 1.65; max-width: 32rem; margin: 0 auto 2rem; }
  .btn-hint { font-size: 0.8rem; color: #9ca3af; margin-top: 0.25rem; }
  .refine-box { background: #f9fafb; border: 1px solid #eaeaea; border-radius: 12px; padding: 1rem 1.25rem; margin-top: 1rem; }
  .refine-label { font-size: 0.8rem; color: #6b7280; margin-bottom: 0.5rem; }
  div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
</style>
"""


def main():
    st.set_page_config(
        page_title="ThinkFlow - Thinking Partner",
        page_icon="",  # no emoji
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(STYLES, unsafe_allow_html=True)
    _inject_secrets_to_env()

    if not check_api_key():
        st.sidebar.error("UPSTAGE_API_KEY를 설정해 주세요.")
        st.error(
            "**UPSTAGE_API_KEY**가 설정되지 않았습니다.\n\n"
            "- **로컬:** 프로젝트 루트의 `.env` 파일에 `UPSTAGE_API_KEY=키값` 추가\n"
            "- **Streamlit Cloud:** 앱 Settings → Secrets에 `UPSTAGE_API_KEY = \"키\"` 추가 후 Save"
        )
        st.stop()

    if "thinkflow_result" not in st.session_state:
        st.session_state.thinkflow_result = None
    if "thought_dump" not in st.session_state:
        st.session_state.thought_dump = ""
    if "last_context" not in st.session_state:
        st.session_state.last_context = ""

    # ----- Sidebar: Logo, Dumping Zone, File Upload -----
    with st.sidebar:
        st.markdown('<p class="thinkflow-logo">ThinkFlow</p>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown('<p style="font-size:0.9rem;font-weight:600;color:#4b5563;margin-bottom:0.25rem;">생각 덤핑 & 컨텍스트</p>', unsafe_allow_html=True)

        thought_input = st.text_area(
            "자유롭게 생각을 적어 보세요.",
            height=200,
            key="thought_dump",
            label_visibility="collapsed",
            placeholder="여기에 어지러운 생각들을 자유롭게 적어주세요...",
        )
        n_char = len(thought_input or "")
        st.markdown(f'<p class="char-count">{n_char}자 작성됨</p>', unsafe_allow_html=True)

        st.markdown('<p style="font-size:0.9rem;font-weight:600;color:#4b5563;margin:1rem 0 0.25rem;">참고 자료 (PDF, 이미지)</p>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "PDF 또는 이미지 업로드",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="ref_files",
            label_visibility="collapsed",
        )

        has_input = bool((thought_input or "").strip()) or bool(uploaded_files)
        st.markdown("---")
        run_clicked = st.button("생각 정리하기", type="primary", use_container_width=True, disabled=not has_input)
        if not has_input:
            st.markdown('<p class="btn-hint">내용을 입력하거나 참고 자료를 올리면 버튼이 활성화됩니다</p>', unsafe_allow_html=True)

        if st.session_state.thinkflow_result is not None and not st.session_state.thinkflow_result.get("need_clarification"):
            st.markdown("---")
            st.markdown('<div class="success-box"><strong>분석 완료</strong><br/>전략 맵과 액션 플랜이 준비되었어요. 아래에서 보완할 내용을 추가할 수 있습니다.</div>', unsafe_allow_html=True)
            if st.button("새로운 주제로 시작", use_container_width=True):
                st.session_state.thinkflow_result = None
                st.session_state.last_context = ""
                st.rerun()

        st.markdown('<p class="footer-text">Powered by Upstage</p>', unsafe_allow_html=True)

    # ----- Run analysis -----
    if run_clicked:
        context_parts = []
        if (thought_input or "").strip():
            context_parts.append(thought_input.strip())
        if uploaded_files:
            try:
                from core.processor import process_documents
                paths: list[Path] = []
                with tempfile.TemporaryDirectory() as tmp:
                    for f in uploaded_files:
                        path = Path(tmp) / (f.name or "file")
                        path.write_bytes(f.getvalue())
                        paths.append(path)
                    file_text = process_documents(paths)
                if file_text and file_text.strip():
                    context_parts.append(file_text.strip())
            except Exception as e:
                st.sidebar.warning(f"참고 자료 처리 중 오류: {e}")
        combined_context = "\n\n".join(context_parts) if context_parts else ""

        if not combined_context:
            st.sidebar.info("내용을 입력하거나 참고 자료를 올려 주세요.")
        else:
            with st.spinner("생각을 정리하고 있어요..."):
                try:
                    from core.agent import ThinkFlowAgent
                    from utils.helpers import generate_ics
                    agent = ThinkFlowAgent()
                    result = agent.analyze(combined_context)
                    if result.get("need_clarification"):
                        st.session_state.thinkflow_result = result
                        st.rerun()
                    else:
                        result["_ics_bytes"] = generate_ics(result.get("actions", []))
                        st.session_state.thinkflow_result = result
                        st.session_state.last_context = combined_context
                        st.rerun()
                except Exception as e:
                    st.sidebar.error(f"오류: {e}")

    result = st.session_state.thinkflow_result

    # ----- Main: State 1 Empty -----
    if result is None:
        st.markdown(
            '<div class="empty-hero">'
            '<p class="thinkflow-logo-hero">ThinkFlow</p>'
            '<h2>Thinking Partner</h2>'
            '<p>복잡한 생각과 메모를 구체적인 실행 계획(Action Plan)으로 변환해 드립니다.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="card-box empty-card"><strong>STRUCTURE</strong><br/>복잡한 생각을 논리 트리로 시각화</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="card-box empty-card"><strong>EXECUTION</strong><br/>우선순위가 포함된 액션 아이템 생성</div>', unsafe_allow_html=True)
        return

    # ----- Main: State 2 Gap (Clarification Card) -----
    if result.get("need_clarification"):
        missing = result.get("missing", ["마감일", "담당"])
        missing_str = ", ".join(m for m in missing)
        st.markdown(
            f'<div class="clarification-box">'
            f'<p style="font-size:0.95rem;font-weight:600;color:#92400e;margin-bottom:0.5rem;">조금만 더 알려주세요</p>'
            f'<p style="font-size:0.9rem;color:#78350f;line-height:1.5;">더 정확한 계획을 위해 <strong>{missing_str}</strong> 정보가 필요해요. 왼쪽 입력창에 보완한 뒤 다시 시도해 주세요.</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        return

    # ----- Main: State 3 Dashboard -----
    exec_sum = result.get("executive_summary") or {}
    subject = exec_sum.get("subject") or exec_sum.get("title") or "전략 요약"
    overview = exec_sum.get("overview") or exec_sum.get("summary") or ""
    main_kpi = exec_sum.get("main_kpi") or exec_sum.get("core_value") or ""
    sub_metrics = exec_sum.get("sub_metrics") or exec_sum.get("growth_driver") or ""

    st.markdown('<p class="section-title">EXECUTIVE SUMMARY</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:1.1rem;font-weight:600;color:#374151;margin-bottom:0.5rem;">주제</p><p style="font-size:1rem;color:#4b5563;margin-bottom:1rem;">{subject}</p>', unsafe_allow_html=True)
    if overview:
        st.markdown(f'<p style="font-size:0.9rem;font-weight:600;color:#6b7280;margin-bottom:0.25rem;">개요</p><p style="font-size:0.95rem;color:#4b5563;line-height:1.6;margin-bottom:1rem;">{overview}</p>', unsafe_allow_html=True)
    ec1, ec2 = st.columns(2)
    with ec1:
        st.markdown(f'<div class="card-box"><p class="card-label">핵심 목표 (KPI)</p><p class="card-value">{main_kpi or "-"}</p></div>', unsafe_allow_html=True)
    with ec2:
        st.markdown(f'<div class="card-box"><p class="card-label">하위 성과 지표</p><p class="card-value">{sub_metrics or "-"}</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p class="section-title">LOGIC TREE</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.85rem;color:#6b7280;margin-top:-0.25rem;">전략적 사고의 구조적 가시화</p>', unsafe_allow_html=True)
    mermaid = result.get("mermaid", "")
    if mermaid:
        from streamlit.components.v1 import html as st_html
        from utils.helpers import render_mermaid
        html_block = render_mermaid(mermaid)
        if html_block:
            st_html(html_block, height=400)
        else:
            st.code(mermaid, language="mermaid")
    else:
        st.info("생성된 구조가 없습니다.")

    st.markdown("---")
    st.markdown('<p class="section-title">ACTION PLAN</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.85rem;color:#6b7280;margin-top:-0.25rem;">우선순위에 기반한 실행 목록</p>', unsafe_allow_html=True)
    actions = result.get("actions", [])
    if actions:
        display_rows = []
        for a in actions:
            summary = a.get("summary") or "(제목 없음)"
            level = a.get("level", 1)
            task_name = f"  └─ {summary}" if level == 2 else summary
            due = a.get("due_date")
            due_str = str(due)[:10] if due else "-"
            dep = a.get("dependency") or "-"
            sug = a.get("ai_suggestion")
            ai_suggestion = f"💡 {sug}" if sug else "-"
            display_rows.append({
                "Task Name": task_name,
                "Due Date": due_str,
                "Priority": a.get("priority") or "Medium",
                "Dependency": dep,
                "AI Suggestion": ai_suggestion,
            })
        st.dataframe(display_rows, use_container_width=True, hide_index=True)
        ics_bytes = result.get("_ics_bytes") or b""
        if ics_bytes:
            st.download_button(
                label="캘린더 (.ics) 다운로드",
                data=ics_bytes,
                file_name="thinkflow_actions.ics",
                mime="text/calendar",
            )
    else:
        st.info("추출된 액션이 없습니다.")

    st.markdown("---")
    st.markdown('<p class="section-title">TIMELINE</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.85rem;color:#6b7280;margin-top:-0.25rem;">단계별 마일스톤 및 일정 로드맵</p>', unsafe_allow_html=True)
    if actions:
        month_actions: dict[str, list[str]] = {}
        for a in actions:
            d = a.get("due_date")
            if not d:
                continue
            try:
                if isinstance(d, datetime):
                    month_key = d.strftime("%Y년 %m월")
                else:
                    dt = datetime.strptime(str(d).strip()[:10], "%Y-%m-%d")
                    month_key = dt.strftime("%Y년 %m월")
            except (ValueError, TypeError):
                continue
            summary_text = (a.get("summary") or "(제목 없음)")[:40]
            if month_key not in month_actions:
                month_actions[month_key] = []
            month_actions[month_key].append(summary_text)
        if month_actions:
            def _month_key(m: str) -> tuple[int, int]:
                try:
                    a, b = m.split("년 ", 1)
                    return (int(a.strip()), int(b.replace("월", "").strip() or 0))
                except (ValueError, AttributeError):
                    return (0, 0)
            months_sorted = sorted(month_actions.keys(), key=_month_key)
            for month in months_sorted:
                with st.expander(month, expanded=True):
                    for t in month_actions[month]:
                        st.markdown(f"- {t}")
        else:
            st.caption("due_date가 있는 액션이 없어 타임라인을 표시할 수 없습니다.")
    else:
        st.caption("액션이 없습니다.")

    # ----- Context Accumulation: 찰떡이에게 수정 요청 (대시보드 하단) -----
    st.markdown("---")
    with st.expander("찰떡이에게 수정 요청하기 (열기/닫기)", expanded=False):
        st.caption("계획을 다듬고 싶다면 요청을 적어 보내세요. 이전 계획과 함께 반영해 다시 생성합니다.")
        chat_col1, chat_col2 = st.columns([4, 1])
        with chat_col1:
            chat_input = st.text_input(
                "수정 요청",
                key="refine_chat_input",
                label_visibility="collapsed",
                placeholder="예: 마감일을 2월 20일로 변경해 주세요",
            )
        with chat_col2:
            chat_sent = st.button("보내기", type="primary")
        if chat_sent and (chat_input or "").strip():
            prev_plan = ""
            if result and not result.get("need_clarification"):
                exec_s = result.get("executive_summary") or {}
                prev_plan = f"[이전 계획]\n주제: {exec_s.get('subject', '')}\n개요: {exec_s.get('overview', '')}\n"
                for i, a in enumerate(result.get("actions", [])[:10], 1):
                    prev_plan += f"{i}. {a.get('summary', '')} (마감: {a.get('due_date', '-')})\n"
            combined = (st.session_state.last_context or "").strip()
            if prev_plan:
                combined += "\n\n" + prev_plan
            combined += "\n\n[사용자 수정 요청]\n" + chat_input.strip()
            if combined.strip():
                with st.spinner("수정 요청을 반영해 다시 생성 중..."):
                    try:
                        from core.agent import ThinkFlowAgent
                        from utils.helpers import generate_ics
                        agent = ThinkFlowAgent()
                        new_result = agent.analyze(combined)
                        if new_result.get("need_clarification"):
                            st.session_state.thinkflow_result = new_result
                        else:
                            new_result["_ics_bytes"] = generate_ics(new_result.get("actions", []))
                            st.session_state.thinkflow_result = new_result
                            st.session_state.last_context = combined
                        st.rerun()
                    except Exception as e:
                        st.error(f"오류: {e}")


if __name__ == "__main__":
    main()
