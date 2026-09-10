# 보너스 기능 실행 안내

## 1. AI 도구 호출(Function Calling)과 MCP 채널

체납리셋 Signal AI의 GPT는 모든 데이터를 임의로 읽지 않는다. 답변을 시작할 때 최신 집계 상태를 한 번 읽고, 특정 지표를 확인해야 할 때 아래 읽기 전용 도구를 추가로 선택할 수 있다.

| 도구 | 입력 | 반환 | 사용 근거 |
| --- | --- | --- | --- |
| `get_macro_summary` | 없음 | 기간, 건수, 기본 통계, 추세, 분석 한계 | “전체 흐름은 어떤가?”처럼 전체 상태를 묻는 질문 |
| `get_indicator_snapshot` | `indicator` | 해당 지표의 최신값, 관측 건수, 추세, 출처 | “기준금리 변화는?”처럼 특정 지표를 묻는 질문 |

호출 흐름은 다음과 같다.

```text
브라우저 질문
  → POST /api/chat
  → 요약을 시스템 프롬프트에 주입
  → GPT가 필요할 때만 함수 호출 요청
  → 서버가 집계 데이터만 함수 결과로 반환
  → GPT 최종 답변 + tools_used
  → conversations에 질문·답변 자동 저장
```

도구는 `backend/app/services/ai.py`의 `TOOLS`, `run_tool()`에 정의했다. Firestore 쓰기·삭제 기능, 개인 정보, 서비스 계정·API 키에는 접근할 수 없다. 화면의 AI 답변 아래 `[이번 답변에서 조회한 내부 도구: ...]` 표시로 호출 사실을 확인할 수 있다.

동일한 두 읽기 도구는 `backend/app/mcp_server.py`에서 MCP 표준 입력/출력 서버로도 노출한다. 외부 MCP 지원 클라이언트는 아래 명령으로 이 프로젝트의 개인용 MCP 서버를 실행해 연결할 수 있다.

```powershell
cd backend
python -m venv .mcp-venv
.mcp-venv\Scripts\python -m pip install -r requirements-mcp.txt
.mcp-venv\Scripts\python -m app.mcp_server
```

MCP 런타임은 FastAPI 서버 가상환경과 분리했다. MCP SDK와 웹 서버가 서로 다른 Starlette 버전을 요구할 수 있어, 분리하면 웹 API 배포 의존성이 영향을 받지 않는다.

MCP 서버는 표준 입출력 프로토콜을 사용하므로 단독 실행 시 화면에 일반 문장을 출력하지 않고 클라이언트 요청을 기다리는 것이 정상이다. MCP Inspector 또는 지원 클라이언트에서 `get_macro_summary`, `get_indicator_snapshot`을 호출해 결과를 확인한다. 이 설계는 웹 채팅의 함수 호출과 외부 채널이 같은 분석 범위·안전 한계를 유지하게 한다.

`OPENAI_API_KEY` 없이 `AI_DEMO_MODE=true`인 로컬 학습 모드에서는 외부 GPT 호출·과금 대신 `get_macro_summary` 사용 사실을 포함한 로컬 요약 응답을 제공한다. 실제 배포에서는 환경 변수의 OpenAI 키로 GPT 함수 호출 흐름이 동작한다.

## 2. 인사이트·UX 고도화

| 기능 | 실행 방법 | 확인 위치 |
| --- | --- | --- |
| 추세 시각화 | 가계대출 연체율 관측값을 추가·수정하면 Canvas 추세선이 다시 그려짐 | 화면의 “추세 시각화” 카드 |
| CSV 내보내기 | 데이터 관리 카드의 `CSV 내보내기` 버튼 클릭 | 다운로드 파일 `tax-reset-macro-signals.csv` |
| 다크 모드 | 상단 `다크 모드` 버튼 클릭 | `localStorage`에 선택 상태 저장, 새로고침 후 유지 |
| 추가 통계 | `GET /api/data/statistics` 호출 | `summary`와 `monthly_average` 응답 |

CSV에는 날짜·지표·값·단위·출처·메모를 포함한다. 그래프와 CSV 모두 공개 집계 시계열만 다루며 개인 체납 자료는 저장하거나 내보내지 않는다.
