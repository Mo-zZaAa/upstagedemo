"""
ThinkFlow - Main Dashboard UI
생각 덤핑 & 컨텍스트 → 구조화된 전략 맵 & 액션 플랜.
Theme: 좌측 입력 / 우측 결과 (Executive Summary, Logic Tree, Action Plan, Gantt).
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


def check_api_key() -> bool:
    key = os.environ.get("UPSTAGE_API_KEY", "").strip()
    return bool(key)


# ---- 스타일: 디자인 시안에 맞춘 라이트 그레이 + 퍼플 악센트 ----
STYLES = """
<style>
  .stApp { background: #f5f5f7; }
  [data-testid="stSidebar"] { background: #e8e8ed; }
  [data-testid="stSidebar"] .stMarkdown { color: #1d1d1f; }
  h1, h2, h3 { color: #1d1d1f !important; font-weight: 600 !important; }
  .thinkflow-title { font-size: 1.25rem; font-weight: 700; color: #7c3aed; margin-bottom: 0; }
  .char-count { font-size: 0.8rem; color: #6e6e73; margin-top: 4px; }
  .card-box {
    background: white;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    margin-bottom: 1rem;
    border: 1px solid #e5e5ea;
  }
  .card-value { font-weight: 600; color: #7c3aed; }
  .card-label { font-size: 0.75rem; color: #6e6e73; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
  .empty-card { background: #e8e8ed; color: #6e6e73; border: 1px dashed #c7c7cc; }
  .section-title { font-size: 0.75rem; color: #7c3aed; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px; }
  .stButton > button {
    background: linear-gradient(90deg, #7c3aed, #a78bfa) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    width: 100%;
  }
  .stButton > button:hover { opacity: 0.95; box-shadow: 0 2px 8px rgba(124,58,237,0.4); }
  .success-box { background: #e8f5e9; border: 1px solid #a5d6a7; border-radius: 8px; padding: 0.75rem 1rem; margin: 0.5rem 0; }
  .footer-text { font-size: 0.7rem; color: #8e8e93; margin-top: 2rem; }
  div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
</style>
"""


def main():
    st.set_page_config(
        page_title="ThinkFlow",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(STYLES, unsafe_allow_html=True)

    if not check_api_key():
        st.sidebar.error("`.env`에 `UPSTAGE_API_KEY`를 설정해 주세요.")
        st.error("`.env`에 `UPSTAGE_API_KEY`가 설정되지 않았습니다. 프로젝트 루트의 `.env` 파일을 확인하세요.")
        st.stop()

    # 세션에 결과 저장 (새로운 주제로 시작 시 초기화)
    if "thinkflow_result" not in st.session_state:
        st.session_state.thinkflow_result = None

    # ----- 좌측 사이드바: 생각 덤핑 & 참고 자료 -----
    with st.sidebar:
        st.markdown('<p class="thinkflow-title">ThinkFlow</p>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("**생각 덤핑 & 컨텍스트**")

        thought_input = st.text_area(
            "자유롭게 생각을 적어 보세요.",
            placeholder="예: 2월 4일까지 기획안 내야 하는데 아직 타겟도 못 정함... 타겟 같은 거 필요하려나? 우리 팀원들은 다들 운동을 안 해서...",
            height=200,
            key="thought_dump",
            label_visibility="collapsed",
        )
        n_char = len(thought_input or "")
        st.markdown(f'<p class="char-count">{n_char}자 작성됨</p>', unsafe_allow_html=True)

        st.markdown("**참고 자료 (PDF, 이미지)**")
        uploaded_files = st.file_uploader(
            "PDF 또는 이미지 업로드",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="ref_files",
            label_visibility="collapsed",
        )

        st.markdown("---")
        run_clicked = st.button("✨ 생각 정리하기", type="primary", use_container_width=True)

        if st.session_state.thinkflow_result is not None:
            st.markdown("---")
            st.markdown('<div class="success-box">✅ **분석 완료**<br/>입력된 내용을 바탕으로 전략 로드맵과 액션 아이템 생성이 완료되었습니다.</div>', unsafe_allow_html=True)
            if st.button("🔄 새로운 주제로 시작", use_container_width=True):
                st.session_state.thinkflow_result = None
                st.rerun()

        st.markdown('<p class="footer-text">Powered by ThinkFlow Intelligence Engine</p>', unsafe_allow_html=True)

    # ----- 분석 실행 -----
    if run_clicked:
        # 입력: 텍스트 + 파일에서 추출한 텍스트
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
            st.sidebar.warning("생각을 적거나 참고 자료(PDF/이미지)를 업로드한 뒤 다시 시도해 주세요.")
        else:
            with st.spinner("생각을 정리하고 있어요..."):
                try:
                    from core.agent import ThinkFlowAgent
                    from utils.helpers import generate_ics
                    agent = ThinkFlowAgent()
                    result = agent.analyze(combined_context)
                    result["_ics_bytes"] = generate_ics(result.get("actions", []))
                    st.session_state.thinkflow_result = result
                    st.rerun()
                except FileNotFoundError as e:
                    st.sidebar.error(f"파일을 찾을 수 없습니다: {e}")
                except ValueError as e:
                    st.sidebar.error(f"처리 오류: {e}")
                except Exception as e:
                    st.sidebar.error(f"오류가 발생했습니다: {e}")

    # ----- 우측 메인: 빈 상태 vs 결과 -----
    result = st.session_state.thinkflow_result

    if result is None:
        # 빈 상태: 시작 안내 + STRUCTURE / EXECUTION 카드
        st.markdown("## 생각 정리를 시작해보세요")
        st.markdown("왼쪽 입력창에 아이디어를 덤핑하고 **생각 정리하기** 버튼을 누르면, 이곳에 구조화된 전략 맵과 상세 실행 계획이 생성됩니다.")
        st.markdown("")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="card-box empty-card">**STRUCTURE**<br/>복잡한 생각을 논리 트리로 시각화</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="card-box empty-card">**EXECUTION**<br/>우선순위가 포함된 액션 아이템 생성</div>', unsafe_allow_html=True)
        return

    # ----- 결과: Executive Summary -----
    exec_sum = result.get("executive_summary") or {}
    title = exec_sum.get("title") or "전략 요약"
    summary = exec_sum.get("summary") or ""
    core_value = exec_sum.get("core_value") or ""
    growth_driver = exec_sum.get("growth_driver") or ""

    st.markdown('<p class="section-title">Executive Summary</p>', unsafe_allow_html=True)
    st.markdown(f"### {title}")
    if summary:
        st.markdown(summary)
    ec1, ec2 = st.columns(2)
    with ec1:
        st.markdown(f'<div class="card-box"><p class="card-label">핵심 가치</p><p class="card-value">{core_value or "-"}</p></div>', unsafe_allow_html=True)
    with ec2:
        st.markdown(f'<div class="card-box"><p class="card-label">성장 동력</p><p class="card-value">{growth_driver or "-"}</p></div>', unsafe_allow_html=True)

    # ----- Logic Tree (Mermaid) -----
    st.markdown("---")
    st.markdown('<p class="section-title">Logic Tree</p>', unsafe_allow_html=True)
    st.markdown("전략적 사고의 구조적 가시화")
    mermaid = result.get("mermaid", "")
    if mermaid:
        st.code(mermaid, language="mermaid")
    else:
        st.info("생성된 구조가 없습니다.")

    # ----- Action Plan -----
    st.markdown("---")
    st.markdown('<p class="section-title">Action Plan</p>', unsafe_allow_html=True)
    st.markdown("우선순위에 기반한 실행 목록")
    actions = result.get("actions", [])
    if actions:
        # 컬럼 순서: summary, due_date, priority, assignee (리스트 그대로 표시)
        st.dataframe(actions, use_container_width=True, hide_index=True)
        ics_bytes = result.get("_ics_bytes") or b""
        if ics_bytes:
            st.download_button(
                label="📅 캘린더(.ics) 다운로드",
                data=ics_bytes,
                file_name="thinkflow_actions.ics",
                mime="text/calendar",
            )
    else:
        st.info("추출된 액션이 없습니다.")

    # ----- Gantt Timeline (간단 버전: 액션별 due_date 기준) -----
    st.markdown("---")
    st.markdown('<p class="section-title">Gantt Timeline</p>', unsafe_allow_html=True)
    st.markdown("단계별 마일스톤 및 일정 로드맵")
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
                with st.expander(f"📅 {month}", expanded=True):
                    for t in month_actions[month]:
                        st.markdown(f"- {t}")
        else:
            st.caption("due_date가 있는 액션이 없어 타임라인을 표시할 수 없습니다.")
    else:
        st.caption("액션이 없습니다.")


if __name__ == "__main__":
    main()
