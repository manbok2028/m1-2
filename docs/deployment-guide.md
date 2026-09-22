# Render · Vercel 배포 안내

## 1. Firebase 준비

1. Firebase Console에서 `tax-reset-signal-ai` 프로젝트를 만들고 **Firestore Database**를 생성한다.
2. 프로젝트 설정 → 서비스 계정 → 새 비공개 키 생성으로 JSON을 내려받는다.
3. 배포용으로는 JSON 전체를 한 줄 문자열로 바꿔 Render의 `FIREBASE_SERVICE_ACCOUNT_JSON`에만 넣는다. 파일 자체를 저장소에 넣지 않는다.
4. 로컬 테스트는 내려받은 파일을 `backend/firebase-service-account.json`에 저장하고 `.env`의 `FIREBASE_SERVICE_ACCOUNT_FILE=firebase-service-account.json`을 설정할 수 있다. 이 파일은 `.gitignore`에 포함되어 GitHub에 올라가지 않는다.
4. Firestore 규칙은 서비스 계정이 서버에서 쓰기 가능하도록 설정하되, 브라우저 클라이언트에 서비스 계정 키를 주지 않는다. 개인 체납 자료를 넣지 않고 공개 집계지표만 사용한다.

## 2. Render 백엔드

1. GitHub의 `m1-2` 저장소를 Render **Web Service**로 연결한다.
2. Root Directory는 `backend`, Build Command는 `pip install -r requirements.txt`, Start Command는 `uvicorn app.main:app --host 0.0.0.0 --port $PORT`로 설정한다. `render.yaml`을 사용해도 된다.
3. 환경 변수에 다음을 설정한다.

```text
APP_ENV=production
AI_DEMO_MODE=false
OPENAI_API_KEY=실제_OpenAI_키
FIREBASE_SERVICE_ACCOUNT_JSON={서비스_계정_JSON_전체}
ALLOWED_ORIGINS=https://m1-2-manbok2028s-projects.vercel.app
```

4. 배포 뒤 `https://tax-reset-signal-ai-api.onrender.com/health`와 `https://tax-reset-signal-ai-api.onrender.com/docs`를 확인한다. 두 키를 설정한 뒤 `python -m scripts.import_ecos`로 실제 ECOS 핵심 시계열을 Firestore에 수집한다.

## 3. Vercel 프론트엔드

1. 같은 GitHub 저장소를 Vercel 프로젝트로 Import한다.
2. Root Directory를 `frontend`로 지정한다.
3. Environment Variables에 `API_BASE_URL=https://tax-reset-signal-ai-api.onrender.com`를 넣는다.
4. Deploy한다. 빌드 스크립트가 `js/runtime-config.js`를 생성해 브라우저가 Render API만 호출하게 한다.
5. 공개 주소 `https://m1-2-manbok2028s-projects.vercel.app`를 Render `ALLOWED_ORIGINS`에 추가하고 Render를 재배포한다. 이 프로젝트는 기본 설정에도 해당 도메인을 포함해, 대시보드 변수를 비워 두어도 공개 운영 주소가 연결되도록 했다.

## 4. 배포 후 점검

- Vercel 화면에서 거시경제 지표 요약과 “개인 판단 금지” 한계가 보이는가?
- 관측값을 추가·수정·삭제하면 목록과 요약이 갱신되는가?
- 질문 전송 시 로딩 뒤 GPT 답변이 보이고, 대화 기록에 자동 저장되는가?
- 과금 방지를 위해 작은 질문으로 먼저 검증했는가?
- Render 무료 인스턴스의 첫 요청은 수십 초 걸릴 수 있으므로, 실패로 단정하지 말고 로딩 후 한 번 재시도한다.
