from datetime import date, timedelta

from app.services.analysis import build_summary, monthly_average


def records(values: list[float]) -> list[dict]:
    start = date(2025, 1, 1)
    return [
        {
            "id": str(index),
            "date": start + timedelta(days=index),
            "indicator": "household_delinquency_rate",
            "value": value,
            "unit": "%",
            "source": "test",
            "memo": "test",
        }
        for index, value in enumerate(values)
    ]


def test_summary_contains_core_statistics_and_rising_trend():
    summary = build_summary(records([1.0] * 10 + [2.0] * 10))
    assert summary.count == 20
    assert summary.metrics.total == 30.0
    assert summary.metrics.average == 1.5
    assert summary.metrics.maximum == 2.0
    assert summary.trend.startswith("상승")


def test_monthly_average_groups_daily_points():
    output = monthly_average(records([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]))
    assert len(output) == 1
    assert output[0]["average"] == 4.0
