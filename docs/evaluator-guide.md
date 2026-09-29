# M1-2 평가자 확인 안내서 — 체납리셋 Signal AI

> 이 문서는 평가자가 저장소를 처음 열었을 때, **미션 요구조건을 어떤 화면·API·코드에서 확인하면 되는지** 빠르게 알 수 있도록 작성한 제출용 안내서입니다.  
> 작성일: 2026-09-29 · 대상 저장소: `manbok2028/m1-2`

## 1. 서비스와 평가 범위

체납리셋 Signal AI는 개인의 체납 가능성을 판정하는 서비스가 아닙니다. 한국은행 ECOS의 **공개 월별 거시지표**를 바탕으로, 체납 리스크를 이해할 때 참고할 수 있는 거시경제적 신호와 한계를 설명하는 AI 비서입니다.

| 구분 | 평가자가 확인할 내용 |
| --- | --- |
| 핵심 데이터 | 기준금리와 가계대출 연체율의 월별 시계열, 운영 Firestore 기준 240건 |
| 분석 원칙 | 가계대출 연체율은 조세 체납의 직접 지표가 아닌 **대리 지표**이며, 개인별 판단을 하지 않음 |
| 사용자 기능 | 데이터 CRUD, 통계·그래프, AI 채팅, 대화 기록 조회·삭제 |
| 기술 구성 | FastAPI + Firestore + OpenAI + Vercel + Render |
| 보너스 | GPT 읽기 전용 도구 호출, MCP 서버, Canvas 그래프, CSV, 다크 모드, 콜드스타트 UX |

## 2. 바로 확인할 공개 주소

| 대상 | 주소 | 용도 |
| --- | --- | --- |
| 사용자 웹 화면 | [Vercel 서비스](https://m1-2-manbok2028s-projects.vercel.app) | CRUD·그래프·AI 채팅·대화 기록 시연 |
| API 명세 | [Render Swagger UI](https://tax-reset-signal-ai-api.onrender.com/docs) | 모든 API 경로와 요청·응답 형식 확인 |
| 서버 상태 | [Render Health](https://tax-reset-signal-ai-api.onrender.com/health) | 배포 서버 준비 상태 확인 |
| 사전 깨우기 | [Render Warmup](https://tax-reset-signal-ai-api.onrender.com/warmup) | 무료 서버 콜드스타트 대응 확인 |

> Render 무료 인스턴스는 장시간 미사용 뒤 첫 응답에 시간이 걸릴 수 있습니다. 웹 화면은 `/warmup`을 먼저 호출하고 약 50초간 자동 재시도합니다. 기다려도 열리지 않으면 화면의 **다시 연결** 버튼을 누르면 됩니다. 이는 데이터 변경이나 OpenAI 호출 없이 서버와 Firestore 읽기 연결만 준비합니다.

## 3. 3분 핵심 시연 순서

다음 순서만 실행하면 데이터 → 분석 → AI → 기록으로 이어지는 미션의 핵심 흐름을 확인할 수 있습니다.

1. Vercel 서비스 주소를 열고, 상단 연결 안내가 사라진 뒤 요약·가계대출 연체율 추세 그래프를 확인합니다.
2. **데이터 관리**에서 기준일·지표·값·단위·출처·메모를 한 건 입력해 저장합니다. 목록과 요약이 갱신되는지 확인한 뒤, 필요하면 수정 또는 삭제합니다.
3. **AI 비서**에 `최근 가계대출 연체율을 해석할 때 주의할 점을 알려줘`라고 질문합니다.
4. 답변에 공개 지표의 기간·추세·한계와 개인 판단 금지 고지가 포함되는지 확인합니다. 필요할 경우 화면에 읽기 전용 도구 사용 근거도 표시됩니다.
5. **대화 기록**에서 방금 만든 대화를 열어 질문과 답변이 보존되는지 확인하고, 삭제 기능도 확인합니다.
6. Swagger UI에서 `GET /api/data/summary`를 실행해 `count`와 지표별 기간·통계가 화면의 근거 데이터임을 확인합니다.

테스트를 위해 입력한 임의 관측값은 시연 후 삭제해도 됩니다. 공개 ECOS 데이터 자체를 수정할 필요는 없습니다.

## 4. 미션 요구조건별 평가 근거

| 미션 요구조건 | 구현 결과 | 평가 방법 | 코드 근거 |
| --- | --- | --- | --- |
| 관심 시계열 100건 이상 | 기준금리·가계대출 연체율 월별 데이터 240건 적재 | `GET /api/data/summary`에서 `count: 240` 확인 | `backend/scripts/import_ecos.py`, `services/ecos.py` |
| 기간·기본 통계·최근 추세 | 기간, 건수, 평균·최대·최소·최신값, 최근 변화 계산 | 요약 API와 웹 그래프 확인 | `backend/app/services/analysis.py` |
| FastAPI·Swagger·CORS | FastAPI 라우터·Pydantic 검증·CORS·`/docs` | Render Swagger UI와 Vercel 화면 연동 확인 | `backend/app/main.py`, `schemas.py` |
| 데이터 CRUD | 생성·목록·수정·삭제·요약 API 제공 | 데이터 관리 화면 또는 Swagger에서 실행 | `backend/app/routers/data.py` |
| Firestore 저장 | `data`, `conversations` 컬렉션을 분리 사용 | CRUD 후 새로고침, 대화 기록 재조회 | `backend/app/services/repository.py` |
| AI 컨텍스트 주입 | Firestore 요약을 안전 고지와 함께 GPT 시스템 프롬프트에 주입 | AI 질문 후 근거 있는 집계 설명 확인 | `backend/app/services/ai.py` |
| 대화 기록 | 채팅 뒤 자동 저장, 목록·상세 조회·삭제 | 대화 기록 화면에서 방금 대화 열기 | `backend/app/routers/conversations.py` |
| 사용자 UX | 로딩·오류·수동 재시도, 데이터 입력·수정·삭제, 대화 불러오기 | Vercel 화면에서 직접 시연 | `frontend/index.html`, `frontend/js/app.js` |
| Render/Vercel 배포 | 백엔드 Render, 프런트 Vercel 분리 배포 | 위 공개 주소 접속 | `backend/render.yaml`, `frontend/vercel.json` |
| 콜드스타트 대응 | `/warmup`, 캐시 방지, 자동 재시도, 안내·다시 연결 버튼 | `/warmup` 응답과 첫 화면 안내 확인 | `main.py`, `frontend/js/app.js` |
| 보너스 기능 | GPT 읽기 전용 도구·MCP·Canvas·CSV·다크 모드 | AI 답변의 도구 표시와 화면 기능 확인 | `ai.py`, `mcp_server.py`, `frontend/js/app.js` |

## 5. API 빠른 검증표

Swagger UI에서 아래 순서로 실행하면 UI가 실제 서버 API를 사용한다는 점을 확인할 수 있습니다.

| API | 기대 결과 | 의미 |
| --- | --- | --- |
| `GET /health` | `200 OK` | Render FastAPI 서버가 실행 중 |
| `GET /warmup` | `status: ready`, `data_ready: true`, `record_count` | 서버·Firestore 읽기 연결 준비 완료 |
| `GET /api/data/summary` | `count: 240`, 지표별 요약 | 운영 시계열 데이터와 분석 요약 |
| `GET /api/data/statistics` | 월별 평균 통계 | 그래프·통계용 데이터 |
| `POST /api/data` | `201 Created` | 관측값 생성 |
| `PUT /api/data/{record_id}` | `200 OK` | 관측값 수정 |
| `DELETE /api/data/{record_id}` | `204 No Content` | 관측값 삭제 |
| `POST /api/chat` | 답변·`conversation_id` | 컨텍스트 주입 GPT 답변과 기록 생성 |
| `GET /api/conversations` | 대화 목록 | 대화 자동 저장 확인 |
| `GET /api/conversations/{conversation_id}` | 질문·답변 메시지 | 저장된 대화 불러오기 |

`POST /api/chat`의 예시 질문은 다음처럼 **개인 정보를 넣지 않는 공개 통계 해석 질문**을 사용합니다.

```json
{
  "message": "최근 가계대출 연체율과 기준금리를 함께 볼 때 어떤 한계가 있나요?"
}
```

## 6. 평가 시 확인할 설계 의도

### 데이터의 출처·품질

- 핵심 데이터는 한국은행 ECOS 공개 통계이며, 기준일·지표·값·단위·출처·메모를 함께 저장합니다.
- 같은 날짜와 지표 조합은 수집 스크립트가 중복 저장하지 않습니다.
- 연체율은 세금 체납과 동일하지 않으므로, 답변과 문서에서 대리 지표임을 명시합니다.

### AI 안전성과 컨텍스트 주입

- GPT는 Firestore 또는 서비스 계정에 직접 접근하지 않습니다.
- 서버가 계산한 집계 요약만 시스템 프롬프트에 전달합니다.
- 읽기 전용 도구도 집계 결과만 반환하며, 데이터 쓰기·삭제·개인 정보 접근 권한이 없습니다.
- 개인의 체납 여부, 압류 가능성, 납부 능력, 세무·법률 결론은 제공하지 않습니다.

### 보안과 운영

- OpenAI API 키, ECOS 키, Firebase 서비스 계정 JSON은 GitHub에 저장하지 않고 배포 환경 변수로만 관리합니다.
- 브라우저에는 관리자 Firebase 자격 증명이나 OpenAI 키가 전달되지 않습니다.
- Vercel 공개 도메인만 백엔드 CORS에서 허용하도록 구성했습니다.

## 7. 저장소 문서 안내

| 문서 | 읽을 때 |
| --- | --- |
| [README](../README.md) | 서비스 목적·구조·로컬 실행·환경 변수 개요를 볼 때 |
| [미션 충족표](mission-compliance.md) | 요구조건과 파일 단위 구현 근거를 빠르게 대조할 때 |
| [평가보고서](evaluation-report.md) | 기획·구현·배포·검증 과정을 상세히 검토할 때 |
| [배포 안내](deployment-guide.md) | Render/Vercel 설정과 재배포 절차를 확인할 때 |
| [검증 체크리스트](verification-checklist.md) | 제출 전 테스트와 시연 항목을 점검할 때 |
| [보너스 기능 안내](bonus-features.md) | GPT 도구 호출·MCP·UX 보너스를 확인할 때 |

## 8. 최종 평가 요약

평가자는 공개 Vercel 화면에서 **관측값 관리 → 통계·그래프 → 데이터 근거 AI 답변 → 대화 기록 재조회**를 시연하고, Render Swagger UI에서 같은 API의 응답을 확인할 수 있습니다. 이로써 요구된 데이터 기반 AI Agent의 전체 흐름과 배포 상태를 재현 가능하게 제시합니다.

콜드스타트처럼 무료 배포 환경에서 생길 수 있는 지연도 사용자에게 이유와 재시도 방법을 안내하고, `/warmup`과 자동 재시도로 완화했습니다. 따라서 일시적인 서버 기동 지연을 기능 오류로 오인하지 않고 평가할 수 있습니다.
