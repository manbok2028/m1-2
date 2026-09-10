"""Clearly labelled local-only macro-signal samples (not official statistics)."""

from __future__ import annotations

from datetime import date


def make_sample_records(months: int = 60) -> list[dict]:
    """Create two monthly series, 60 points each, for local UI verification only."""
    records: list[dict] = []
    for index in range(months):
        year, month = divmod(index, 12)
        period = date(2020 + year, month + 1, 1)
        records.extend(
            [
                {
                    "date": period,
                    "indicator": "base_rate",
                    "value": round(1.0 + min(index, 34) * 0.09 - max(index - 45, 0) * 0.04, 2),
                    "unit": "%",
                    "source": "학습용 모의값",
                    "memo": "로컬 화면 검증용. 실제 ECOS 값이 아닙니다.",
                },
                {
                    "date": period,
                    "indicator": "household_delinquency_rate",
                    "value": round(0.42 + index * 0.006 + ((index % 5) - 2) * 0.008, 3),
                    "unit": "%",
                    "source": "학습용 모의값",
                    "memo": "가계대출 연체율 대리 지표의 로컬 검증용 모의값입니다.",
                },
            ]
        )
    return records
