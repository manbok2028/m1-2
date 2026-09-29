# 공개 배포·Firestore 실동작 증빙

> 평가 항목의 “실제 접속 결과(스크린샷 또는 live 응답 캡처)”를 위해, 공개 배포 주소에 읽기 전용 요청을 보내고 운영 Firestore CRUD를 한 번 재현한 기록입니다.  
> 확인 일시: **2026-09-29T03:12:59Z (UTC)** · 비밀키·서비스 계정 정보는 포함하지 않습니다.

## 1. 공개 프런트엔드·백엔드 접속 결과

아래 명령은 공개 URL에 실제로 요청한 방식입니다.

```powershell
curl.exe -sS -L -o NUL -w "frontend=%{http_code}\n" "https://m1-2-manbok2028s-projects.vercel.app/"
curl.exe -sS -L -o NUL -w "health=%{http_code}\n" "https://tax-reset-signal-ai-api.onrender.com/health"
curl.exe -sS -L -o NUL -w "warmup=%{http_code}\n" "https://tax-reset-signal-ai-api.onrender.com/warmup"
curl.exe -sS -L -o NUL -w "docs=%{http_code}\n" "https://tax-reset-signal-ai-api.onrender.com/docs"
curl.exe -sS -L -o NUL -w "summary=%{http_code}\n" "https://tax-reset-signal-ai-api.onrender.com/api/data/summary"
```

실제 응답 캡처:

```text
frontend=200
health=200
warmup=200
docs=200
summary=200
```

| 확인 대상 | 실제 결과 | 평가자가 직접 재확인할 주소 |
| --- | --- | --- |
| 프런트엔드 | HTTP `200`, 페이지 제목 `체납리셋 Signal AI \| 거시경제 AI 비서` | [Vercel 서비스](https://m1-2-manbok2028s-projects.vercel.app) |
| 백엔드 상태 | HTTP `200` | [GET /health](https://tax-reset-signal-ai-api.onrender.com/health) |
| Swagger API 문서 | HTTP `200`, 페이지 제목 `Tax Reset Signal AI API - Swagger UI` | [GET /docs](https://tax-reset-signal-ai-api.onrender.com/docs) |
| 데이터 요약 API | HTTP `200` | [GET /api/data/summary](https://tax-reset-signal-ai-api.onrender.com/api/data/summary) |
| 사전 깨우기 | HTTP `200` | [GET /warmup](https://tax-reset-signal-ai-api.onrender.com/warmup) |

## 2. 실제 공개 API 응답 캡처

### `/health`

```json
{"status":"ok","environment":"production"}
```

### `/warmup`

```json
{"status":"ready","data_ready":true,"record_count":240}
```

`/warmup`은 Render 무료 인스턴스의 첫 요청 지연을 완화하기 위한 읽기 전용 엔드포인트입니다. 응답은 캐시되지 않도록 `Cache-Control: no-store`를 설정합니다.

### `/api/data/summary` 핵심 결과

```json
{
  "period": "2015-01-01 ~ 2024-12-01",
  "count": 240,
  "primary_indicator": "household_delinquency_rate",
  "primary_unit": "%",
  "indicators": [
    {"indicator": "base_rate", "count": 120, "latest_value": 3.0},
    {"indicator": "household_delinquency_rate", "count": 120, "latest_value": 0.4}
  ]
}
```

응답에는 “가계대출 연체율은 국세·지방세 체납의 직접 측정값이 아니며 개인 판단에 사용할 수 없다”는 한계 고지도 함께 포함됩니다.

## 3. 운영 Firestore CRUD 재현 증빙

평가 항목의 `repository.py` 구현이 코드에만 존재하지 않고, 실제 운영 Firestore와 연결되는지 확인하기 위해 **임시 공개 관측값 한 건**으로 다음 순서를 실행했습니다.

1. `POST /api/data`로 `evaluation_crud_proof` 관측값을 생성했습니다.
2. `GET /api/data` 목록에서 생성된 `record_id`가 정확히 한 건 조회되는지 확인했습니다.
3. `PUT /api/data/{record_id}`로 메모를 수정했습니다.
4. `DELETE /api/data/{record_id}`로 해당 임시 관측값을 삭제했습니다.

실제 실행 결과:

```json
{
  "checked_at": "2026-09-29T03:12:59Z",
  "create_status": 201,
  "read_status": 200,
  "created_record_found": true,
  "update_status": 200,
  "delete_status": 204,
  "temporary_record_removed": true
}
```

따라서 운영 Firestore의 관측값 CRUD가 `생성 → 조회 → 수정 → 삭제`까지 실제로 동작함을 확인했습니다. 이 검증용 레코드는 `204 No Content` 응답 뒤 즉시 제거되어 운영 데이터 240건에는 남아 있지 않습니다.

## 4. 평가자가 재현하는 방법

1. [Swagger UI](https://tax-reset-signal-ai-api.onrender.com/docs)를 엽니다.
2. `GET /health`, `GET /warmup`, `GET /api/data/summary`에서 **Try it out → Execute**를 눌러 위와 같은 `200` 응답을 확인합니다.
3. 필요하면 `POST /api/data`로 테스트 관측값을 하나 생성하고, 반환된 `id`로 `PUT`, `DELETE`를 실행합니다.
4. 테스트 데이터는 평가 종료 전 반드시 `DELETE`로 제거합니다.

전체 평가 흐름은 [평가자 확인 안내서](evaluator-guide.md), 구현 파일 대조는 [미션 충족표](mission-compliance.md)에서 이어서 확인할 수 있습니다.

동일 검증은 독립 Python 파일 [`backend/scripts/verify_deployment.py`](../backend/scripts/verify_deployment.py)로도 재현할 수 있습니다. 기본 실행은 읽기 전용이고, `--verify-crud`를 명시했을 때만 임시 관측값을 생성한 뒤 자동 삭제합니다.
