"""Pure time-series summary logic, kept separate so it is easy to test."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from app.schemas import DataSummary, IndicatorSummary, SummaryMetrics


def _series_values(records: list[dict]) -> tuple[list[dict], float, str, str]:
    ordered = sorted(records, key=lambda item: item["date"])
    values = [float(item["value"]) for item in ordered]
    recent_size = min(10, len(values))
    recent_average = sum(values[-recent_size:]) / recent_size
    previous = values[-recent_size * 2 : -recent_size]
    previous_average = sum(previous) / len(previous) if previous else recent_average
    change = 0.0 if previous_average == 0 else (recent_average - previous_average) / previous_average * 100
    direction = "상승" if change > 3 else "감소" if change < -3 else "유지"
    return ordered, change, direction, f"{direction} (최근 {recent_size}건 평균 {change:+.1f}%)"


def build_summary(records: list[dict]) -> DataSummary:
    if not records:
        raise ValueError("요약할 거시경제 지표 데이터가 없습니다.")

    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        grouped[record["indicator"]].append(record)

    preferred = "household_delinquency_rate"
    primary_indicator = preferred if preferred in grouped else max(grouped, key=lambda key: len(grouped[key]))
    primary_records, change, direction, trend = _series_values(grouped[primary_indicator])
    values = [float(item["value"]) for item in primary_records]
    indicators = []
    for name, series in sorted(grouped.items()):
        ordered, series_change, _, series_trend = _series_values(series)
        latest = ordered[-1]
        indicators.append(
            IndicatorSummary(
                indicator=name,
                unit=latest["unit"],
                source=latest["source"],
                count=len(ordered),
                latest_value=round(float(latest["value"]), 3),
                trend=series_trend,
                recent_change_percent=round(series_change, 1),
            )
        )

    return DataSummary(
        period=f"{primary_records[0]['date']} ~ {primary_records[-1]['date']}",
        count=len(records),
        metrics=SummaryMetrics(
            total=round(sum(values), 3),
            average=round(sum(values) / len(values), 3),
            maximum=round(max(values), 3),
            minimum=round(min(values), 3),
            latest_value=round(values[-1], 3),
        ),
        trend=trend,
        recent_change_percent=round(change, 1),
        primary_indicator=primary_indicator,
        primary_unit=primary_records[-1]["unit"],
        indicators=indicators,
        limitation="가계대출 연체율 등은 국세·지방세 체납의 직접 측정값이 아니며, 개인의 체납·처분 가능성을 판단할 수 없습니다.",
    )


def monthly_average(records: list[dict], indicator: str = "household_delinquency_rate") -> list[dict[str, float | str]]:
    buckets: dict[str, list[float]] = defaultdict(list)
    for item in records:
        if item["indicator"] != indicator:
            continue
        record_date = item["date"]
        if isinstance(record_date, str):
            record_date = date.fromisoformat(record_date)
        buckets[record_date.strftime("%Y-%m")].append(float(item["value"]))
    return [
        {"month": month, "average": round(sum(values) / len(values), 3)}
        for month, values in sorted(buckets.items())
    ]
