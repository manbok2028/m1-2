# AI Agent 개발 미션 요구사항 충족표 — 체납리셋 Signal AI

| 미션 요구사항 | 체납리셋 구현 | 확인 위치 |
| --- | --- | --- |
| 관심 시계열 데이터·100개 이상 | ECOS 기준금리·가계대출 연체율 월별 공개지표. 로컬 60개월×2=120건, 실제 수집 기본 240건 | `sample_data.py`, `ecos.py`, `import_ecos.py` |
| 기간·통계·최근 추세 요약 | 핵심 대리 지표의 기간·기본 통계·최근 10건 변화, 모든 지표별 상태 | `backend/app/services/analysis.py` |
| FastAPI·CORS·Swagger | 라우터와 `CORSMiddleware`, 자동 `/docs` | `backend/app/main.py` |
| Pydantic 검증 | date·indicator·value·unit·source·memo와 수정 필드 검증 | `backend/app/schemas.py` |
| Firestore 연동 | `data`, `conversations` 컬렉션 분리 | `backend/app/services/repository.py` |
| 데이터 CRUD 4개 + summary | POST/GET/PUT/DELETE와 `GET /api/data/summary` | `backend/app/routers/data.py` |
| 대화 기록 저장·조회·삭제·불러오기 | POST/GET/DELETE, `GET /api/conversations/{id}` | `backend/app/routers/conversations.py` |
| AI 채팅·컨텍스트 주입 | 데이터 요약 → 안전 고지 포함 시스템 프롬프트 → GPT → 대화 자동 저장 | `chat.py`, `ai.py` |
| 채팅 UX | 질문·답변·로딩·오류 표시 | `frontend/index.html`, `frontend/js/app.js` |
| 데이터 관리 UX | 지표·값·단위·출처·메모 추가, 수정·삭제, 목록 | `frontend/index.html`, `frontend/js/app.js` |
| 대화 불러오기 UX | 목록 클릭 뒤 선택한 messages 재표시 | `frontend/js/app.js` |
| 보너스 통계/시각화 | 월별 평균 통계와 가계대출 연체율 Canvas 차트 | `/api/data/statistics`, `frontend/js/app.js` |
| 보너스 UX | CSV 내보내기·다크 모드 | `frontend/js/app.js` |
| Render 배포 | Web Service start/health/환경변수 설정 | `backend/render.yaml` |
| Vercel 배포 | `API_BASE_URL`을 빌드 시 정적 설정 파일로 주입 | `frontend/vercel.json`, `scripts/generate-config.js` |
| 보안·운영 | 키는 환경 변수, 배포 Firebase 누락 시 실행 차단, 개인 자료 미수집 | `.gitignore`, `config.py`, `repository.py` |
| 체납 분석 한계 | 연체율은 조세 체납 대리 지표이며 개인 판단을 금지 | `README.md`, `service-plan.md`, `ai.py` |
