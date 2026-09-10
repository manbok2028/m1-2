"""Small ECOS importer for the two verified monthly core indicators."""

from __future__ import annotations

from datetime import datetime

import requests


ECOS_BASE_RATE = ("722Y001", ["0101000"], "base_rate", "%", "한국은행 ECOS 722Y001")
ECOS_HOUSEHOLD_DELINQUENCY = (
    "901Y054",
    ["MO3AB", "AB"],
    "household_delinquency_rate",
    "%",
    "한국은행 ECOS 901Y054 (가계대출 연체율·1일 이상)",
)


def fetch_ecos_indicator(api_key: str, definition: tuple, start: str = "201501", end: str = "202412") -> list[dict]:
    stat_code, item_codes, indicator, unit, source = definition
    base = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/500/{stat_code}/M/{start}/{end}"
    response = requests.get("/".join([base, *item_codes]), timeout=15)
    response.raise_for_status()
    payload = response.json()
    if "StatisticSearch" not in payload:
        raise ValueError("ECOS 응답에 StatisticSearch가 없습니다. 키·지표 코드·기간을 확인하세요.")
    rows = payload["StatisticSearch"].get("row", [])
    if not rows:
        raise ValueError(f"ECOS {indicator} 결과가 비어 있습니다.")
    return [
        {
            "date": datetime.strptime(row["TIME"], "%Y%m").date(),
            "indicator": indicator,
            "value": float(row["DATA_VALUE"]),
            "unit": unit,
            "source": source,
            "memo": "ECOS API에서 수집한 월별 공개 집계값입니다. 조세 체납의 직접 지표가 아닙니다.",
        }
        for row in rows
    ]


def fetch_verified_core_series(api_key: str, start: str = "201501", end: str = "202412") -> list[dict]:
    return [
        *fetch_ecos_indicator(api_key, ECOS_BASE_RATE, start, end),
        *fetch_ecos_indicator(api_key, ECOS_HOUSEHOLD_DELINQUENCY, start, end),
    ]
