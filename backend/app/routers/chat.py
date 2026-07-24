"""聊天 API 路由 — 会话列表、消息收发。"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_auth
from app.models.chat import Conversation, Message
from app.models.system import User as UserModel

router = APIRouter()


# ── Response schemas ───────────────────────────────────────────────

class MessageOut(BaseModel):
    id: str
    sender_id: str
    content: str
    is_read: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: str
    other_user_id: str
    other_user_name: str = ""
    last_message: str = ""
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Helpers ────────────────────────────────────────────────────────

def _get_partner_name(db: Session, conv: Conversation, current_user_id: str) -> str:
    """获取对方用户名."""
    partner_id = (
        conv.participant_b_id if conv.participant_a_id == current_user_id
        else conv.participant_a_id
    )
    user = db.query(UserModel).filter(UserModel.id == partner_id).first()
    return user.username if user else partner_id[:8]


def _ensure_conv(db: Session, uid_a: str, uid_b: str):
    """获取或创建两人之间的会话."""
    conv = db.query(Conversation).filter(
        ((Conversation.participant_a_id == uid_a) & (Conversation.participant_b_id == uid_b)) |
        ((Conversation.participant_a_id == uid_b) & (Conversation.participant_b_id == uid_a))
    ).first()
    if not conv:
        conv = Conversation(
            participant_a_id=min(uid_a, uid_b),
            participant_b_id=max(uid_a, uid_b),
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return conv


# ── Endpoints ──────────────────────────────────────────────────────

@router.get("/chat/sessions", response_model=list[ConversationOut])
def list_sessions(
    user_id: str = Depends(require_auth),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取当前用户的所有会话列表（按最后消息时间倒序）."""
    sessions = db.query(Conversation).filter(
        (Conversation.participant_a_id == user_id) |
        (Conversation.participant_b_id == user_id)
    ).order_by(Conversation.updated_at.desc()).limit(limit).all()

    result = []
    for conv in sessions:
        partner_name = _get_partner_name(db, conv, user_id)
        # Count unread messages (messages from others that current user hasn't read)
        partner_id = (
            conv.participant_b_id if conv.participant_a_id == user_id
            else conv.participant_a_id
        )
        unread = db.query(Message).filter(
            Message.conversation_id == conv.id,
            Message.sender_id == partner_id,
            Message.is_read.is_(None),
        ).count()

        result.append(ConversationOut(
            id=conv.id,
            other_user_id=partner_id,
            other_user_name=partner_name,
            last_message=conv.last_message or "",
            last_message_at=conv.last_message_at,
            unread_count=unread,
            created_at=conv.created_at,
        ))
    return result


@router.get("/chat/sessions/{session_id}/messages", response_model=list[MessageOut])
def list_messages(
    session_id: str,
    user_id: str = Depends(require_auth),
    limit: int = Query(50, ge=1, le=200),
    before: Optional[str] = Query(None, description="分页游标：最后一条消息的 ID"),
    db: Session = Depends(get_db),
):
    """获取会话消息列表."""
    conv = db.query(Conversation).filter(
        Conversation.id == session_id,
        ((Conversation.participant_a_id == user_id) | (Conversation.participant_b_id == user_id)),
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")

    q = db.query(Message).filter(Message.conversation_id == session_id)
    if before:
        prior = db.query(Message.created_at).filter(Message.id == before).first()
        if prior and prior[0]:
            q = q.filter(Message.created_at < prior[0])

    msgs = q.order_by(Message.created_at.desc()).limit(limit).all()

    # Mark messages as read
    partner_id = (
        conv.participant_b_id if conv.participant_a_id == user_id
        else conv.participant_a_id
    )
    now = datetime.utcnow()
    for m in msgs:
        if m.sender_id == partner_id and m.is_read is None:
            m.is_read = now

    db.commit()
    return msgs


@router.post("/chat/sessions/{session_id}/messages", response_model=MessageOut)
def send_message(
    session_id: str,
    content: str,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """发送消息."""
    if not content or not content.strip():
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    conv = db.query(Conversation).filter(
        Conversation.id == session_id,
        ((Conversation.participant_a_id == user_id) | (Conversation.participant_b_id == user_id)),
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")

    msg = Message(
        conversation_id=session_id,
        sender_id=user_id,
        content=content.strip()[:5000],  # 限制长度
    )
    db.add(msg)

    # Update conversation last message
    conv.last_message = content.strip()[:200]
    conv.last_message_at = datetime.utcnow()
    conv.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(msg)
    return msg


@router.post("/chat/sessions", response_model=ConversationOut)
def start_session(
    partner_id: str = Query(..., description="对方 user_id"),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """发起新会话（与指定用户）."""
    if partner_id == user_id:
        raise HTTPException(status_code=400, detail="不能和自己聊天")

    conv = _ensure_conv(db, user_id, partner_id)
    partner_name = _get_partner_name(db, conv, user_id)

    return ConversationOut(
        id=conv.id,
        other_user_id=(
            conv.participant_b_id if conv.participant_a_id == user_id
            else conv.participant_a_id
        ),
        other_user_name=partner_name,
        last_message=conv.last_message or "",
        last_message_at=conv.last_message_at,
        created_at=conv.created_at,
    )
