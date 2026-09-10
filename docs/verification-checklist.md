# 제출 전 검증·스크린샷 체크리스트

## 자동 검증

```powershell
cd backend
pytest -q
uvicorn app.main:app --reload
```

`http://localhost:8000/docs`에서 아래를 각각 실행한다.

- `POST /api/data` → `GET /api/data` → `PUT /api/data/{id}` → `DELETE /api/data/{id}` (기준금리 또는 가계대출 연체율 관측값)
- `GET /api/data/summary`, `GET /api/data/statistics`
- `POST /api/chat` 후 `GET /api/conversations`
- `GET /api/conversations/{id}`로 messages 재표시 확인

## 필수 제출 스크린샷 3종

| 파일명 권장 | 화면에 반드시 포함할 내용 |
| --- | --- |
| `01-chat-summary.png` | 거시지표 요약, 질문, AI 답변, 개인 판단 한계가 보이는 채팅 화면 |
| `02-data-crud.png` | 지표·값·출처를 포함한 새 관측값 추가 또는 수정·삭제 직후 목록 |
| `03-conversation-load.png` | 이전 대화 목록과 선택된 전체 messages |

## 공개 배포 검증

1. Vercel URL을 모바일 폭(375px)과 데스크톱 폭(1440px)에서 연다.
2. Render Swagger URL `/docs`에서 API 문서와 `/health` 성공 응답을 확인한다.
3. 실제 키·서비스 계정·개인 메모가 스크린샷이나 Git 이력에 보이지 않는지 확인한다.
