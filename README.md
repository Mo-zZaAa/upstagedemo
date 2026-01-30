
  # B2B SaaS Dashboard Design

  This is a code bundle for B2B SaaS Dashboard Design. The original project is available at https://www.figma.com/design/6Tpd8pdL1qpsW4W75xfPxz/B2B-SaaS-Dashboard-Design.

  ## Running the code

  Run `npm i` to install the dependencies.

  Run `npm run dev` to start the development server.

  ---

  ## ThinkFlow (Streamlit 대시보드)

  - **API 키:** `.env` 파일의 `UPSTAGE_API_KEY`에만 저장됩니다. `.gitignore`에 `.env`가 포함되어 있어 커밋되지 않습니다. **절대 코드에 API 키를 넣지 마세요.**
  - **실행 방법 (프로젝트 루트에서):**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    streamlit run app.py
    ```
  - 브라우저에서 열리는 주소(예: http://localhost:8501)에서 PDF/이미지를 업로드 후 "분석 실행"을 누르면 구조(마인드맵)와 액션 플랜이 생성됩니다.
  