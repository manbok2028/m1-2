from __future__ import annotations

from datetime import date as Date, datetime

from pydantic import BaseModel, Field, model_validator


class DataCreate(BaseModel):
    date: Date
    indicator: str = Field(min_length=2, max_length=80, description="예: base_rate, household_delinquency_rate")
    value: float = Field(ge=0, description="해당 기준일의 지표 값")
    unit: str = Field(min_length=1, max_length=30, description="예: %, 지수")
    source: str = Field(min_length=2, max_length=100, description="예: 한국은행 ECOS")
    memo: str = Field(min_length=1, max_length=300)


class DataUpdate(BaseModel):
    date: Date | None = None
    indicator: str | None = Field(default=None, min_length=2, max_length=80)
    value: float | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, min_length=1, max_length=30)
    source: str | None = Field(default=None, min_length=2, max_length=100)
    memo: str | None = Field(default=None, min_length=1, max_length=300)

    @model_validator(mode="after")
    def require_one_field(self) -> "DataUpdate":
        if all(value is None for value in self.model_dump().values()):
            raise ValueError("수정할 필드를 하나 이상 입력하세요.")
        return self


class DataRecord(DataCreate):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SummaryMetrics(BaseModel):
    total: float
    average: float
    maximum: float
    minimum: float
    latest_value: float


class DataSummary(BaseModel):
    period: str
    count: int
    metrics: SummaryMetrics
    trend: str
    recent_change_percent: float
    primary_indicator: str
    primary_unit: str
    indicators: list["IndicatorSummary"]
    limitation: str


class IndicatorSummary(BaseModel):
    indicator: str
    unit: str
    source: str
    count: int
    latest_value: float
    trend: str
    recent_change_percent: float


class StatisticsResponse(BaseModel):
    summary: DataSummary
    monthly_average: list[dict[str, float | str]]


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    summary: DataSummary
    model: str
    tools_used: list[str] = Field(default_factory=list, description="AI가 이번 답변에서 호출한 내부 읽기 도구")


class Message(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=4000)
    created_at: datetime | None = None


class ConversationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    messages: list[Message] = Field(min_length=1, max_length=50)


class Conversation(BaseModel):
    id: str
    title: str
    messages: list[Message]
    created_at: datetime | None = None
