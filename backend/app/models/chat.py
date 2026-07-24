"""聊天会话数据模型."""

from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class Conversation(Base):
    """聊天会话（一对一）."""
    __tablename__ = "conversations"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    participant_a_id = Column(String(32), nullable=False)  # 发起方 user_id
    participant_b_id = Column(String(32), nullable=False)  # 接收方 user_id
    last_message = Column(Text, nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    is_active = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    __table_args__ = (
        Index("idx_conv_a", "participant_a_id"),
        Index("idx_conv_b", "participant_b_id"),
        Index("idx_conv_partners", "participant_a_id", "participant_b_id"),
    )


class Message(Base):
    """聊天消息."""
    __tablename__ = "messages"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    conversation_id = Column(
        String(32),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(DateTime, nullable=True)  # NULL = unread
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("idx_msg_conv", "conversation_id"),
        Index("idx_msg_sender", "sender_id"),
    )
