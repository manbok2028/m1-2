# M1-2 평가보고서 — 체납리셋 Signal AI

> 작성일: 2026-09-22  
> 저장소: `manbok2028/m1-2` · 배포 상태: 공개 운영 확인 완료

## 1. 한 줄 요약

**체납을 개인 단위로 예측하지 않고**, 한국은행 ECOS의 공개 월별 거시지표를 Firestore에 축적한 뒤, 통계 요약을 근거로 GPT가 설명하도록 만든 웹 기반 AI 비서이다. 데이터 관리, AI 대화, 대화 기록, 배포와 보너스 도구 호출까지 미션 흐름을 하나의 서비스로 완성했다.

| 운영 대상 | 주소 | 확인 목적 |
| --- | --- | --- |
| 프런트엔드 | [체납리셋 Signal AI](https://m1-2-manbok2028s-projects.vercel.app) | 사용자 화면·CRUD·그래프·채팅 |
| 백엔드 | [Render Swagger API](https://tax-reset-signal-ai-api.onrender.com/docs) | API 명세·직접 호출 검증 |

## 2. 미션 해석과 문제 정의

처음에는 “체납관리”라는 주제를 개인 체납 예측으로 만들기보다, **공개 통계로 설명 가능한 거시경제 신호 분석**으로 범위를 정했다. 개인의 체납 여부, 압류 가능성, 세금·법률 판단에는 개인 정보와 전문 판단이 필요하므로 이 서비스의 범위에서 제외했다.

분석의 중심은 다음 두 월별 ECOS 지표다.

| 지표 | 분석상 역할 | 사용 시 한계 |
| --- | --- | --- |
| 기준금리 (`722Y001`) | 이자 부담 환경의 선행 후보 | 금리 변화만으로 체납 원인을 단정할 수 없음 |
| 가계대출 연체율 (`901Y054`) | 상환 부담을 보여 주는 대리 신호 | 국세·지방세 체납과 같은 직접 지표가 아님 |

따라서 모든 AI 답변에는 “집계 지표이며 개인 판단에 사용할 수 없다”는 안전 고지를 포함하도록 설계했다.

## 3. 미션 요구조건별 완료 근거

| 요구조건 | 구현 결과 | 평가 시 확인 방법 |
| --- | --- | --- |
| 관심 시계열 100건 이상 | 실제 Firestore에 2015-01~2024-12 월별 2개 지표, **240건** 적재 | `GET /api/data/summary`의 `count: 240` |
| 기간·통계·최근 추세 | 기간, 건수, 평균·최대·최소·최신값, 최근 10건 변화율 계산 | 요약 화면 및 `GET /api/data/summary` |
| FastAPI·Swagger·CORS | FastAPI 라우터, Pydantic, `CORSMiddleware`, `/docs` 제공 | Render Swagger 링크 |
| 데이터 CRUD | 관측값 추가·목록·수정·삭제와 요약 갱신 | `/api/data`의 POST/GET/PUT/DELETE |
| Firestore 연동 | `data`, `conversations` 컬렉션 분리 저장 | `repository.py`, 실제 API 조회 |
| AI 컨텍스트 주입 | Firestore 집계 → 시스템 프롬프트 → GPT 답변 → 자동 저장 | `POST /api/chat`, `services/ai.py` |
| 대화 기록 | 목록·상세 불러오기·삭제 API와 UI | `/api/conversations`, 대화 기록 화면 |
| 사용자 화면 | 요약, 지표 관리, AI 채팅, 대화 기록, 설정 화면 | Vercel 공개 사이트 |
| 배포 | 백엔드 Render, 프런트 Vercel로 분리 배포 | 두 공개 주소 |
| 보너스 | GPT 읽기 전용 도구 호출, MCP stdio 서버, Canvas 차트, CSV, 다크 모드 | `mcp_server.py`, 보너스 기능 안내 |

상세한 파일 단위 근거는 [미션 충족표](mission-compliance.md)에 정리했다.

## 4. 구현 과정: 동료 교육생이 따라갈 순서

### 4-1. 데이터를 먼저 설계했다

1. 개인 체납 자료가 아니라 출처·단위·기준일이 명확한 공개 월별 시계열을 선택했다.
2. 관측값 구조를 `date`, `indicator`, `value`, `unit`, `source`, `memo`로 통일했다.
3. 로컬 학습용 모의값 120건을 준비하고, 운영용으로 ECOS 수집 스크립트를 만들어 실제 240건을 Firestore에 넣었다.
4. 같은 날짜·지표 조합은 중복 저장하지 않도록 수집 로직을 작성했다.

이 순서가 중요한 이유는 AI보다 먼저 **질문에 근거로 쓸 데이터와 한계**를 정해야 하기 때문이다.

### 4-2. API와 저장소를 분리했다

- `routers/data.py`: CRUD와 통계·요약 API
- `services/analysis.py`: 기간·기본 통계·추세 계산
- `services/repository.py`: Firestore 접근을 한곳으로 모음
- `routers/conversations.py`: 대화 기록의 생성·목록·상세·삭제

이렇게 분리하면 화면 코드가 Firestore 키를 알 필요가 없고, 추후 PostgreSQL 등 다른 저장소로 바꾸기도 쉽다.

### 4-3. AI가 원자료 대신 요약을 보도록 만들었다

채팅 요청의 내부 흐름은 아래와 같다.

```text
사용자 질문
  → Firestore에서 공개 관측값 읽기
  → 지표별 기간·건수·통계·최근 변화율 산출
  → 안전 고지와 함께 GPT 시스템 프롬프트에 주입
  → 필요하면 읽기 전용 도구로 요약/지표 상태 재확인
  → 답변과 질문을 Firestore conversations에 자동 저장
```

이 방식은 GPT가 Firebase 서비스 계정이나 전체 데이터베이스에 직접 접근하지 않게 한다. AI가 사용하는 보너스 도구 `get_macro_summary`, `get_indicator_snapshot`도 쓰기·삭제 권한이 없는 읽기 전용 함수다.

### 4-4. 화면에서 학습 결과를 확인 가능하게 했다

- **요약**: 대표 지표, 기간, 최근 변화, Canvas 추세 그래프
- **데이터 관리**: 관측값 CRUD와 CSV 내보내기
- **AI 비서**: 로딩·오류 처리·도구 사용 표시를 포함한 질의응답
- **대화 기록**: 이전 대화를 다시 열고 삭제
- **설정**: 연결 상태와 다크 모드

즉, 평가자가 API만 보는 것이 아니라 “데이터 입력 → 요약 변화 → AI 질문 → 기록 재조회” 전체 흐름을 화면에서 재현할 수 있다.

## 5. 배포 과정과 운영 설정

### Render 백엔드

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check: `/health`
- 운영 환경 변수: `APP_ENV`, `AI_DEMO_MODE`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `FIREBASE_SERVICE_ACCOUNT_JSON`, `ECOS_API_KEY`

### Vercel 프런트엔드

- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `.`
- 환경 변수: `API_BASE_URL=https://tax-reset-signal-ai-api.onrender.com`

프런트엔드의 실제 공개 도메인과 배포 미리보기 도메인은 백엔드 CORS에 제한적으로 허용했다. Vercel의 로그인 보호도 해제해 동료 교육생과 평가자가 로그인 없이 공개 결과물을 확인할 수 있게 했다.

## 6. 최종 검증 결과

배포 완료 후 다음을 실제 공개 주소로 점검했다.

| 점검 | 결과 |
| --- | --- |
| Vercel 공개 페이지 응답 | HTTP 200, 제목 `체납리셋 Signal AI | 거시경제 AI 비서` |
| Render 헬스체크 | HTTP 200 |
| 프런트 → 백엔드 CORS 사전 요청 | HTTP 200, 운영 Vercel Origin 허용 확인 |
| Firestore 데이터 요약 | 240건, 기준금리·가계대출 연체율 두 지표 확인 |
| 실제 AI 채팅 | `gpt-4o-mini` 응답 성공, `get_macro_summary` 사용 확인 |
| 대화 기록 | AI 점검 대화의 `conversation_id` 생성 확인 |
| API 문서 | `/docs` 공개 접속 확인 |

검증 시 개인 정보는 보내지 않았고, AI 테스트에는 거시지표 해석에 관한 한 문장만 사용했다.

## 7. 보안·윤리 점검

1. OpenAI 키와 Firebase 서비스 계정 JSON은 Render 환경 변수에만 두고 GitHub에는 저장하지 않았다.
2. `.env`, 서비스 계정 JSON, 개인 자료는 `.gitignore`로 제외했다.
3. 브라우저에는 API 키나 Firebase 관리자 권한을 보내지 않는다.
4. 공개 집계 지표만 다루며, 개인 체납·압류·납부 능력·세무·법률 결론을 제공하지 않는다.
5. 연체율을 조세 체납과 동일시하지 않고 대리 지표임을 화면과 AI 응답에 명시한다.

## 8. 시연용 체크리스트

동료 교육생이 결과물을 발표하거나 평가할 때는 다음 순서로 시연하면 된다.

1. Vercel 주소를 열어 요약 화면의 기간·지표·한계 고지를 보여 준다.
2. 데이터 관리에서 공개 관측값 한 건을 추가하거나 수정한 뒤 목록과 요약이 갱신되는지 확인한다.
3. AI 비서에 “최근 가계대출 연체율을 해석할 때 주의할 점”을 질문한다.
4. 답변의 거시경제적 설명, 도구 사용 표시, 개인 판단 금지 고지를 확인한다.
5. 대화 기록 화면에서 방금 만든 대화를 다시 연다.
6. Swagger에서 `/api/data/summary`와 `/api/chat`을 보여 주며 UI와 API가 같은 서버를 쓰는지 설명한다.

## 9. 향후 고도화 방향

- CPI, 자영업 폐업률, 개인회생·파산, 국세·지방세 체납 통계를 출처·주기·결측 검증 후 보조 지표로 추가
- 세목·지역별 공개 통계가 확보되면 시차상관과 선행성 탐색 기능 도입
- 공개 데이터의 최신 갱신 시점과 출처 링크를 화면에 더 명확히 표시
- 운영 환경에서 API 사용량·오류율 모니터링과 키 순환 절차 정례화

이 고도화도 개인 단위 예측이 아니라 공개 통계의 **설명 가능성**을 높이는 범위에서 진행한다.
