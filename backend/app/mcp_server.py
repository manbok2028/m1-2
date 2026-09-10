"""Read-only MCP channel for the same aggregate macro-signal tools used by chat."""

from mcp.server.fastmcp import FastMCP

from app.core.config import get_settings
from app.services.analysis import build_summary
from app.services.sample_data import make_sample_records

mcp = FastMCP(
    "Tax Reset Signal AI",
    instructions=(
        "공개 거시경제 집계 지표만 조회하는 체납리셋 Signal AI 도구입니다. "
        "개인의 체납·압류·납부 가능성을 판단하지 마세요."
    ),
)


def _summary():
    settings = get_settings()
    if settings.firebase_service_account_json:
        # Delay the Firebase import so a local MCP host can inspect the public sample tools
        # before credentials are configured. Production reads the same Firestore data collection.
        from app.services.repository import get_repository

        records = get_repository(settings).list_data()
    else:
        records = make_sample_records()
    if not records:
        raise ValueError("조회할 거시경제 관측값이 없습니다.")
    return build_summary(records)


@mcp.tool()
def get_macro_summary() -> dict:
    """Return the current aggregate period, statistics, trend, and limitation."""
    return _summary().model_dump()


@mcp.tool()
def get_indicator_snapshot(indicator: str) -> dict:
    """Return one aggregate indicator's latest value, trend, count, and source."""
    for item in _summary().indicators:
        if item.indicator == indicator:
            return item.model_dump()
    return {"error": f"{indicator} 지표는 저장되어 있지 않습니다."}


if __name__ == "__main__":
    mcp.run()
