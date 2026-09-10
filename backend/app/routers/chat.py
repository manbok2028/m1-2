from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.dependencies import repository
from app.schemas import ChatRequest, ChatResponse, Message
from app.services.ai import ask_assistant
from app.services.analysis import build_summary

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest):
    records = repository().list_data()
    if not records:
        raise HTTPException(status_code=400, detail="먼저 거시경제 지표 데이터를 한 건 이상 추가하세요.")
    summary = build_summary(records)
    try:
        answer, model, tools_used = ask_assistant(payload.question, summary, get_settings())
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="AI 응답 생성에 실패했습니다. 잠시 후 다시 시도하세요.") from error

    now = datetime.now(UTC)
    conversation = repository().create_conversation(
        title=payload.question[:40],
        messages=[
            Message(role="user", content=payload.question, created_at=now),
            Message(role="assistant", content=answer, created_at=now),
        ],
    )
    return {
        "conversation_id": conversation["id"],
        "answer": answer,
        "summary": summary,
        "model": model,
        "tools_used": tools_used,
    }
