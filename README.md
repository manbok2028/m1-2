# 체납리셋 Signal AI — 거시경제 체납 리스크 분석 비서

공개 시계열 지표를 Firestore에 저장하고, 요약을 GPT 시스템 프롬프트에 주입하여 **체납 리스크의 거시경제적 신호**를 설명하는 AI 비서입니다. 개인의 체납 여부·압류·납부 가능성·세무 판단을 예측하지 않으며, 집계 통계의 변화와 한계를 이해하도록 돕습니다.

> 기본 핵심 지표는 한국은행 ECOS의 월별 **기준금리(`722Y001`)**와 **가계대출 연체율(1일 이상, `901Y054`)**입니다. 가계대출 연체율은 조세 체납의 직접 지표가 아닌 대리 지표입니다.

## 서비스 목적과 데이터 범위

| 구분 | 역할 | 분석에서의 주의점 |
| --- | --- | --- |
| 기준금리 | 이자 부담 환경을 보여 주는 선행 후보 지표 | 금리 변화가 체납을 일으킨다고 단정하지 않음 |
| 가계대출 연체율 | 상환 부담의 월별 대리 지표 | 국세·지방세 체납과 동일한 지표가 아님 |
| CPI·자영업 상황 | 향후 보조 후보 지표 | 원자료·단위·주기를 검증한 뒤에만 추가 |
| 국세 체납 통계 | 연도별 검증·맥락 지표 후보 | 월별 시차상관의 직접 입력값으로 섞지 않음 |

개인 이름, 주민번호, 주소, 사업자번호, 고지서·계좌번호 등은 수집하지 않습니다. `data`에는 기준일·지표명·값·단위·출처·메모처럼 공개 집계 관측값만 저장합니다.

## 핵심 기능

| 기능 | 사용자 경험 | 구현 위치 |
| --- | --- | --- |
| 데이터 기반 AI 채팅 | 질문 → 로딩 → 거시지표 요약을 반영한 답변 → 대화 자동 저장 | `POST /api/chat`, `backend/app/services/ai.py` |
| 지표 데이터 CRUD | 기준일·지표·값·단위·출처·메모 추가, 수정, 삭제 | `backend/app/routers/data.py` |
| 요약과 시각화 | 기간·건수·기본 통계·최근 추세·가계대출 연체율 그래프 | `/api/data/summary`, `/statistics` |
| 대화 기록 | 대화 목록, 특정 대화의 전체 messages 불러오기, 삭제 | `backend/app/routers/conversations.py` |
| 보너스 AI 도구 호출 | GPT가 필요 시 집계 요약·특정 지표 상태를 읽기 전용 함수로 다시 조회 | `backend/app/services/ai.py` |
| 보너스 UX | Canvas 추세 그래프, CSV 내보내기, 다크 모드 | `frontend/js/app.js` |

## 프로젝트 구조

```text
m1-2/
├── backend/                         # Render FastAPI 서버
│   ├── app/routers/                  # data · chat · conversations
│   ├── app/services/analysis.py      # 지표별 기간·통계·추세 계산
│   ├── app/services/ecos.py          # 검증된 ECOS 핵심 지표 수집
│   ├── app/services/repository.py    # Firestore data·conversations
│   ├── app/mcp_server.py              # 별도 MCP 채널의 읽기 전용 도구
│   ├── scripts/import_ecos.py        # 실제 ECOS → Firestore 수집
│   ├── scripts/seed_firestore.py     # 로컬 모의값 120건 시드
│   └── render.yaml
│   ├── requirements.txt               # FastAPI 서버 의존성
│   └── requirements-mcp.txt           # 별도 MCP 런타임 의존성
├── frontend/                         # Vercel 바닐라 웹
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
└── docs/                             # 기획·평가·배포·검증 문서
```

## 컨텍스트 주입 흐름

```text
사용자 질문
  → Firestore data의 지표별 시계열 조회
  → 기간·건수·평균·최대·최소·최근 추세 생성
  → 시스템 프롬프트에 요약과 “개인 판단 금지” 한계 주입
  → OpenAI GPT 답변
  → questions + answer를 Firestore conversations에 자동 저장
```

GPT는 Firestore에 직접 접근하지 않습니다. 서버가 필요한 집계 요약만 전달하며 API 키·서비스 계정은 브라우저에 노출하지 않습니다.

## 보너스: AI 도구 호출과 UX 고도화

GPT는 답변에 필요한 경우에만 `get_macro_summary`, `get_indicator_snapshot`을 호출합니다. 두 도구는 저장된 **집계 지표만 읽는 함수**이며, 쓰기·삭제·개인 데이터 접근 권한은 없습니다. 화면에는 이번 답변에서 사용한 도구명을 표시해 호출 근거를 확인할 수 있습니다.

```text
질문 → GPT가 도구 필요성 판단 → 읽기 전용 내부 도구 호출
     → 집계 결과를 tool 메시지로 전달 → 안전 고지가 포함된 답변 → 대화 저장
```

추세 Canvas 그래프, CSV 내보내기, 다크 모드도 포함했습니다. 같은 읽기 전용 도구는 MCP 표준 입출력 채널로도 제공됩니다. 동작 근거와 확인 절차는 [보너스 기능 안내](docs/bonus-features.md)에 정리했습니다.

## 로컬 실행

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Firebase·OpenAI 키 전에는 `AI_DEMO_MODE=true`에서 **학습용 모의값 120건**과 명시적 로컬 답변으로 화면을 확인할 수 있습니다.
- 배포 환경은 `APP_ENV=production`, `AI_DEMO_MODE=false`이며 Firebase 키가 없으면 실행을 차단합니다.

## 실제 ECOS 데이터 수집

`ECOS_API_KEY`와 `FIREBASE_SERVICE_ACCOUNT_JSON`을 `.env`에 설정한 뒤 실행합니다.

```powershell
cd backend
python -m scripts.import_ecos
```

이 스크립트는 ECOS 월별 기준금리·가계대출 연체율을 Firestore에 저장합니다. 이미 같은 `날짜 + 지표` 조합이 있으면 건너뛰므로 재실행해도 같은 관측값을 중복 적재하지 않습니다. CPI·폐업률·국세 체납 통계는 출처·단위·주기 검증 전에는 자동 수집·결론에 사용하지 않습니다.

실제 수집 함수는 2020-01~2024-12의 두 지표 120건으로 검증했습니다. [ECOS 검증 기록](docs/ecos-verification.md)에서 범위와 보안 원칙을 확인할 수 있습니다.

## 환경 변수

| 변수 | 사용 위치 | 목적 |
| --- | --- | --- |
| `OPENAI_API_KEY` | Render | GPT 호출 |
| `OPENAI_MODEL` | Render | 기본 `gpt-4o-mini` |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Render | Firestore 서비스 계정 JSON 전체 |
| `ECOS_API_KEY` | 수집 스크립트/서버 | 한국은행 ECOS 공개통계 호출 |
| `ALLOWED_ORIGINS` | Render | Vercel 도메인을 허용하는 CORS 목록 |
| `API_BASE_URL` | Vercel | Render API URL을 프론트 빌드에 주입 |

실제 키, Firebase JSON, 개인 자료는 GitHub·README·스크린샷에 넣지 않습니다.

## 배포

| 대상 | 배포 방법 | 확인 주소 |
| --- | --- | --- |
| Backend | Render Web Service, Root `backend` | [Swagger API 문서](https://tax-reset-signal-ai-api.onrender.com/docs) |
| Frontend | Vercel, Root `frontend` | [체납리셋 Signal AI](https://m1-2-manbok2028s-projects.vercel.app) |

구체적인 설정은 [배포 안내](docs/deployment-guide.md)를, 평가 항목별 구현 위치는 [미션 충족표](docs/mission-compliance.md)를 참고하세요.

## 검증

```powershell
cd backend
pytest -q
```

자동 검증은 지표별 기본 통계·추세·월별 집계와 CRUD·요약·채팅 자동저장·대화 불러오기 흐름을 다룹니다. 제출 화면과 배포 확인은 [검증 체크리스트](docs/verification-checklist.md)에 정리했습니다.
