from fastapi import APIRouter, HTTPException, status

from app.dependencies import repository
from app.schemas import Conversation, ConversationCreate

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=Conversation, status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreate):
    return repository().create_conversation(payload.title, payload.messages)


@router.get("", response_model=list[Conversation])
def list_conversations():
    """List items intentionally include messages, so the client can render a selected history."""
    return repository().list_conversations()


@router.get("/{conversation_id}", response_model=Conversation)
def get_conversation(conversation_id: str):
    conversation = repository().get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="대화를 찾지 못했습니다.")
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: str):
    if not repository().delete_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="삭제할 대화를 찾지 못했습니다.")
