"""OpenAI chat service with an explicit data-summary context injection step."""

from __future__ import annotations

import json

from openai import OpenAI

from app.core.config import Settings
from app.schemas import DataSummary


def make_system_prompt(summary: DataSummary) -> str:
    metrics = summary.metrics
    indicators = "\n".join(
        f"- {item.indicator}: 최근 {item.latest_value}{item.unit}, {item.count}건, {item.trend}, 출처 {item.source}"
        for item in summary.indicators
    )
    return f"""당신은 체납 리스크의 거시경제적 신호를 설명하는 AI 비서입니다.
아래 집계 시계열 요약만 근거로, 사실·가능한 해석·한계를 구분하여 한국어로 답하세요.
가계대출 연체율은 조세 체납의 대리 지표일 뿐이며, 개인의 체납 여부·압류·납부 가능성·법률 또는 세무 판단을 예측하거나 단정하지 마세요.
수치가 부족하면 추가 확인이 필요하다고 말하세요.

[거시경제 신호 요약]
- 핵심 대리 지표: {summary.primary_indicator} ({summary.primary_unit})
- 기간: {summary.period}
- 전체 관측값: {summary.count}건
- 핵심 지표 평균/최대/최소: {metrics.average}/{metrics.maximum}/{metrics.minimum}{summary.primary_unit}
- 최신값: {metrics.latest_value}{summary.primary_unit}
- 최근 추세: {summary.trend}
- 지표별 상태:
{indicators}
- 한계: {summary.limitation}
"""


def local_answer(question: str, summary: DataSummary) -> str:
    return (
        f"현재 거시경제 신호 데이터는 {summary.period}의 {summary.count}건입니다. "
        f"핵심 대리 지표({summary.primary_indicator})의 평균은 {summary.metrics.average}{summary.primary_unit}이고 최근 추세는 {summary.trend}입니다. "
        f"‘{question}’은(는) 금리와 연체율 같은 집계 추세를 함께 비교해 해석할 수 있습니다. "
        f"다만 {summary.limitation} (로컬 확인용 응답이며, 배포 환경에서는 GPT가 같은 요약을 바탕으로 답변합니다.)"
    )


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_macro_summary",
            "description": "현재 저장된 거시경제 신호의 기간, 건수, 추세와 한계를 다시 조회합니다.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_indicator_snapshot",
            "description": "하나의 지표에 대해 최신값, 관측 건수, 최근 추세, 출처를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {"indicator": {"type": "string", "description": "조회할 indicator 이름"}},
                "required": ["indicator"],
                "additionalProperties": False,
            },
        },
    },
]


def run_tool(name: str, arguments: dict, summary: DataSummary) -> dict:
    """Provide narrowly scoped, aggregate-only tool results to the model."""
    if name == "get_macro_summary":
        return summary.model_dump()
    if name == "get_indicator_snapshot":
        indicator = arguments.get("indicator", "")
        for item in summary.indicators:
            if item.indicator == indicator:
                return item.model_dump()
        return {"error": f"{indicator} 지표는 저장되어 있지 않습니다."}
    return {"error": "허용되지 않은 내부 도구입니다."}


def ask_assistant(question: str, summary: DataSummary, settings: Settings) -> tuple[str, str, list[str]]:
    if settings.ai_demo_mode and not settings.openai_api_key:
        return local_answer(question, summary), "local-summary-preview", ["get_macro_summary"]
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

    client = OpenAI(api_key=settings.openai_api_key)
    messages: list[dict] = [
        {"role": "system", "content": make_system_prompt(summary)},
        {"role": "user", "content": question},
    ]
    tools_used: list[str] = []

    for _ in range(2):
        completion = client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=300,
            temperature=0.3,
            messages=messages,
            tools=TOOLS,
            # Every answer starts from a fresh aggregate lookup. The second turn is free
            # to answer normally after the read-only tool result has been supplied.
            tool_choice="required" if not tools_used else "auto",
        )
        message = completion.choices[0].message
        if not message.tool_calls:
            return message.content or "답변을 생성하지 못했습니다.", settings.openai_model, tools_used

        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {"name": call.function.name, "arguments": call.function.arguments},
                    }
                    for call in message.tool_calls
                ],
            }
        )
        for call in message.tool_calls:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
            tools_used.append(call.function.name)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(run_tool(call.function.name, arguments, summary), ensure_ascii=False),
                }
            )

    return "도구 조회 후 답변 생성을 완료하지 못했습니다. 잠시 후 다시 시도하세요.", settings.openai_model, tools_used
