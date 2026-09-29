"""Verify the public Vercel, Render, and optional Firestore CRUD deployment flow.

Run from the backend directory:
    python scripts/verify_deployment.py

The default checks only make read-only requests.  Pass ``--verify-crud`` to
create one clearly labelled temporary public record, verify create/read/update,
and delete it in a ``finally`` block.  This script never reads API keys or
Firebase service-account credentials.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

import requests


DEFAULT_FRONTEND_URL = "https://m1-2-manbok2028s-projects.vercel.app"
DEFAULT_API_BASE_URL = "https://tax-reset-signal-ai-api.onrender.com"


@dataclass
class CheckResult:
    """A single check result that can be read in the terminal or JSON output."""

    name: str
    passed: bool
    status_code: int | None
    detail: str


def request(
    method: str,
    url: str,
    timeout: int,
    **kwargs: Any,
) -> requests.Response:
    """Send one request and turn transport errors into a clear exception."""

    try:
        return requests.request(method, url, timeout=timeout, **kwargs)
    except requests.RequestException as error:
        raise RuntimeError(f"요청 실패: {url} ({error})") from error


def get_json(url: str, timeout: int) -> tuple[requests.Response, dict[str, Any]]:
    response = request("GET", url, timeout)
    try:
        payload = response.json()
    except ValueError as error:
        raise RuntimeError(f"JSON 응답이 아닙니다: {url}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"객체 JSON 응답이 아닙니다: {url}")
    return response, payload


def verify_public_endpoints(
    frontend_url: str,
    api_base_url: str,
    timeout: int,
) -> list[CheckResult]:
    """Verify the published web page, API health, warmup, docs, data, and CORS."""

    results: list[CheckResult] = []

    frontend = request("GET", frontend_url, timeout)
    title = re.search(r"<title>(.*?)</title>", frontend.text, flags=re.DOTALL)
    frontend_title = re.sub(r"\s+", " ", title.group(1)).strip() if title else "title 없음"
    results.append(
        CheckResult(
            name="Vercel 프런트엔드",
            passed=frontend.status_code == 200 and "체납리셋 Signal AI" in frontend_title,
            status_code=frontend.status_code,
            detail=f"title={frontend_title}",
        )
    )

    health, health_payload = get_json(f"{api_base_url}/health", timeout)
    results.append(
        CheckResult(
            name="Render /health",
            passed=health.status_code == 200 and health_payload.get("status") == "ok",
            status_code=health.status_code,
            detail=json.dumps(health_payload, ensure_ascii=False),
        )
    )

    warmup, warmup_payload = get_json(f"{api_base_url}/warmup", timeout)
    record_count = warmup_payload.get("record_count", 0)
    results.append(
        CheckResult(
            name="Render /warmup",
            passed=(
                warmup.status_code == 200
                and warmup_payload.get("status") == "ready"
                and warmup_payload.get("data_ready") is True
                and isinstance(record_count, int)
                and record_count >= 100
            ),
            status_code=warmup.status_code,
            detail=json.dumps(warmup_payload, ensure_ascii=False),
        )
    )

    docs = request("GET", f"{api_base_url}/docs", timeout)
    docs_title = re.search(r"<title>(.*?)</title>", docs.text, flags=re.DOTALL)
    docs_text = re.sub(r"\s+", " ", docs_title.group(1)).strip() if docs_title else "title 없음"
    results.append(
        CheckResult(
            name="Swagger /docs",
            passed=docs.status_code == 200 and "Swagger UI" in docs_text,
            status_code=docs.status_code,
            detail=f"title={docs_text}",
        )
    )

    summary, summary_payload = get_json(f"{api_base_url}/api/data/summary", timeout)
    summary_count = summary_payload.get("count", 0)
    results.append(
        CheckResult(
            name="공개 시계열 요약",
            passed=(
                summary.status_code == 200
                and isinstance(summary_count, int)
                and summary_count >= 100
                and bool(summary_payload.get("indicators"))
            ),
            status_code=summary.status_code,
            detail=(
                f"count={summary_count}, period={summary_payload.get('period')}, "
                f"indicators={len(summary_payload.get('indicators', []))}"
            ),
        )
    )

    origin = frontend_url.rstrip("/")
    cors = request(
        "OPTIONS",
        f"{api_base_url}/api/data/summary",
        timeout,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    allowed_origin = cors.headers.get("access-control-allow-origin", "")
    results.append(
        CheckResult(
            name="Vercel → Render CORS",
            passed=cors.status_code == 200 and allowed_origin == origin,
            status_code=cors.status_code,
            detail=f"access-control-allow-origin={allowed_origin or '없음'}",
        )
    )
    return results


def verify_firestore_crud(api_base_url: str, timeout: int) -> CheckResult:
    """Create, read, update, then always delete a temporary public record."""

    suffix = uuid.uuid4().hex[:12]
    payload = {
        "date": "2099-12-31",
        "indicator": f"evaluation_crud_{suffix}",
        "value": 1.0,
        "unit": "index",
        "source": "deployment verification",
        "memo": "Temporary deployment verification record. It is deleted immediately.",
    }
    record_id: str | None = None
    stages: list[str] = []

    try:
        created = request("POST", f"{api_base_url}/api/data", timeout, json=payload)
        stages.append(f"생성={created.status_code}")
        if created.status_code != 201:
            return CheckResult("운영 Firestore CRUD", False, created.status_code, ", ".join(stages))
        record_id = created.json().get("id")
        if not record_id:
            return CheckResult("운영 Firestore CRUD", False, created.status_code, "생성 응답에 id 없음")

        listed = request("GET", f"{api_base_url}/api/data", timeout)
        stages.append(f"조회={listed.status_code}")
        found = listed.status_code == 200 and any(
            item.get("id") == record_id for item in listed.json()
        )
        if not found:
            return CheckResult("운영 Firestore CRUD", False, listed.status_code, ", ".join(stages))

        updated = request(
            "PUT",
            f"{api_base_url}/api/data/{record_id}",
            timeout,
            json={"memo": "Temporary record updated, then deleted by verification."},
        )
        stages.append(f"수정={updated.status_code}")
        if updated.status_code != 200:
            return CheckResult("운영 Firestore CRUD", False, updated.status_code, ", ".join(stages))

        deleted = request("DELETE", f"{api_base_url}/api/data/{record_id}", timeout)
        stages.append(f"삭제={deleted.status_code}")
        record_id = None
        return CheckResult(
            "운영 Firestore CRUD",
            deleted.status_code == 204,
            deleted.status_code,
            ", ".join(stages) + ", 임시 레코드 삭제 완료",
        )
    finally:
        if record_id:
            # A failure after creation must not leave a verification record behind.
            try:
                request("DELETE", f"{api_base_url}/api/data/{record_id}", timeout)
            except RuntimeError:
                pass


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="체납리셋 Signal AI 공개 배포 검증")
    parser.add_argument("--frontend-url", default=DEFAULT_FRONTEND_URL)
    parser.add_argument("--api-base-url", default=DEFAULT_API_BASE_URL)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument(
        "--verify-crud",
        action="store_true",
        help="운영 Firestore에 임시 공개 레코드를 생성·조회·수정·삭제합니다.",
    )
    parser.add_argument(
        "--json-output",
        help="검증 결과를 저장할 JSON 파일 경로입니다.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    frontend_url = args.frontend_url.rstrip("/")
    api_base_url = args.api_base_url.rstrip("/")
    checked_at = datetime.now(UTC).isoformat()

    try:
        results = verify_public_endpoints(frontend_url, api_base_url, args.timeout)
        if args.verify_crud:
            results.append(verify_firestore_crud(api_base_url, args.timeout))
    except RuntimeError as error:
        results = [CheckResult("배포 연결", False, None, str(error))]

    for result in results:
        mark = "PASS" if result.passed else "FAIL"
        print(f"[{mark}] {result.name} | status={result.status_code} | {result.detail}")

    output = {
        "checked_at": checked_at,
        "frontend_url": frontend_url,
        "api_base_url": api_base_url,
        "verify_crud": args.verify_crud,
        "passed": all(result.passed for result in results),
        "results": [asdict(result) for result in results],
    }
    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as file:
            json.dump(output, file, ensure_ascii=False, indent=2)
        print(f"결과 JSON 저장: {args.json_output}")

    return 0 if output["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
