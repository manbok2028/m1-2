"""Firestore persistence and a deliberately local-only in-memory development store."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

import firebase_admin
from firebase_admin import credentials, firestore

from app.core.config import Settings
from app.schemas import Conversation, DataCreate, DataUpdate, Message
from app.services.sample_data import make_sample_records


def _now() -> datetime:
    return datetime.now(UTC)


def _serialize(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


class MemoryRepository:
    """Local-only fallback that makes UI/testing possible before Firebase setup."""

    def __init__(self) -> None:
        self.data: dict[str, dict] = {}
        self.conversations: dict[str, dict] = {}
        for item in make_sample_records():
            self.create_data(DataCreate(**item))

    def create_data(self, payload: DataCreate) -> dict:
        record_id = str(uuid4())
        record = {"id": record_id, **payload.model_dump(), "created_at": _now(), "updated_at": _now()}
        self.data[record_id] = record
        return record

    def list_data(self) -> list[dict]:
        return sorted(self.data.values(), key=lambda item: item["date"])

    def update_data(self, record_id: str, payload: DataUpdate) -> dict | None:
        record = self.data.get(record_id)
        if record is None:
            return None
        record.update(payload.model_dump(exclude_none=True))
        record["updated_at"] = _now()
        return record

    def delete_data(self, record_id: str) -> bool:
        return self.data.pop(record_id, None) is not None

    def create_conversation(self, title: str, messages: list[Message]) -> dict:
        conversation_id = str(uuid4())
        record = {"id": conversation_id, "title": title, "messages": [message.model_dump() for message in messages], "created_at": _now()}
        self.conversations[conversation_id] = record
        return record

    def list_conversations(self) -> list[dict]:
        return sorted(self.conversations.values(), key=lambda item: item["created_at"], reverse=True)

    def get_conversation(self, conversation_id: str) -> dict | None:
        return self.conversations.get(conversation_id)

    def delete_conversation(self, conversation_id: str) -> bool:
        return self.conversations.pop(conversation_id, None) is not None


class FirestoreRepository:
    data_collection = "data"
    conversations_collection = "conversations"

    def __init__(self, service_account_json: str) -> None:
        if not firebase_admin._apps:
            try:
                account_info = json.loads(service_account_json)
            except json.JSONDecodeError as error:
                raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON은 서비스 계정 JSON 문자열이어야 합니다.") from error
            firebase_admin.initialize_app(credentials.Certificate(account_info))
        self.db = firestore.client()

    @staticmethod
    def _record(document) -> dict:
        value = document.to_dict() or {}
        return {"id": document.id, **value}

    def create_data(self, payload: DataCreate) -> dict:
        document = self.db.collection(self.data_collection).document()
        now = _now()
        document.set({**payload.model_dump(), "created_at": now, "updated_at": now})
        return {"id": document.id, **payload.model_dump(), "created_at": now, "updated_at": now}

    def list_data(self) -> list[dict]:
        documents = self.db.collection(self.data_collection).order_by("date").stream()
        return [self._record(document) for document in documents]

    def update_data(self, record_id: str, payload: DataUpdate) -> dict | None:
        reference = self.db.collection(self.data_collection).document(record_id)
        if not reference.get().exists:
            return None
        reference.update({**payload.model_dump(exclude_none=True), "updated_at": _now()})
        return self._record(reference.get())

    def delete_data(self, record_id: str) -> bool:
        reference = self.db.collection(self.data_collection).document(record_id)
        if not reference.get().exists:
            return False
        reference.delete()
        return True

    def create_conversation(self, title: str, messages: list[Message]) -> dict:
        document = self.db.collection(self.conversations_collection).document()
        now = _now()
        document.set({"title": title, "messages": [message.model_dump() for message in messages], "created_at": now})
        return {"id": document.id, "title": title, "messages": [message.model_dump() for message in messages], "created_at": now}

    def list_conversations(self) -> list[dict]:
        documents = self.db.collection(self.conversations_collection).order_by("created_at", direction=firestore.Query.DESCENDING).stream()
        return [self._record(document) for document in documents]

    def get_conversation(self, conversation_id: str) -> dict | None:
        document = self.db.collection(self.conversations_collection).document(conversation_id).get()
        return self._record(document) if document.exists else None

    def delete_conversation(self, conversation_id: str) -> bool:
        reference = self.db.collection(self.conversations_collection).document(conversation_id)
        if not reference.get().exists:
            return False
        reference.delete()
        return True


def get_repository(settings: Settings):
    if settings.firebase_credentials:
        return FirestoreRepository(settings.firebase_credentials)
    if settings.is_production:
        raise RuntimeError("배포 환경에는 FIREBASE_SERVICE_ACCOUNT_JSON이 필요합니다.")
    return MemoryRepository()
