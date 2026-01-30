#!/bin/bash
# ThinkFlow 앱 실행 (가상환경 사용)
cd "$(dirname "$0")"
.venv/bin/python -m streamlit run app.py "$@"
