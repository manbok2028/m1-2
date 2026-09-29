from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.dependencies import repository
from app.routers import chat, conversations, data

settings = get_settings()
app = FastAPI(
    title="Tax Reset Signal AI API",
    version="1.0.0",
    description="Firestore의 공개 거시경제 지표를 요약해 GPT 대화에 주입하는 API입니다.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
app.include_router(data.router)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.get("/health", tags=["health"])
def health():
    """A lightweight liveness check used by the hosting platform."""
    return JSONResponse(
        {"status": "ok", "environment": settings.app_env},
        headers={"Cache-Control": "no-store"},
    )


@app.get("/warmup", tags=["health"])
def warmup():
    """Wake the web process and verify that its read-only data dependency is ready."""
    record_count = len(repository().list_data())
    return JSONResponse(
        {"status": "ready", "data_ready": True, "record_count": record_count},
        headers={"Cache-Control": "no-store"},
    )
