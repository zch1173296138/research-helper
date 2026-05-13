from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.db.models import ChatMessage, ChatSession, Paper
from backend.app.services.ids import new_id
from backend.app.services.evidence import EvidenceRagService
from backend.app.services.llm import LLMService
from backend.app.services.retrieval import HybridRetriever


class PaperChatService:
    RECENT_MESSAGE_LIMIT = 6
    COMPRESSION_TRIGGER_MESSAGES = 10
    MEMORY_MESSAGE_CHAR_LIMIT = 700

    def __init__(self, settings: Settings):
        self.settings = settings
        self.retriever = HybridRetriever(settings)
        self.llm = LLMService(settings)

    def get_or_create_session(self, db: Session, paper: Paper) -> ChatSession:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.paper_id == paper.id)
            .order_by(ChatSession.created_at.asc())
            .first()
        )
        if session:
            return session

        session = ChatSession(
            id=new_id("chat"),
            library_id=paper.library_id,
            paper_id=paper.id,
            title=paper.original_filename,
            context_mode="hybrid",
            memory_summary="",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def list_messages(self, db: Session, session_id: str, limit: int = 50, before_id: int | None = None) -> list[ChatMessage]:
        query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id)
        if before_id is not None:
            query = query.filter(ChatMessage.id < before_id)
        rows = query.order_by(ChatMessage.id.desc()).limit(limit).all()
        return list(reversed(rows))

    def ask(
        self,
        db: Session,
        session: ChatSession,
        question: str,
        top_k: int = 8,
        context_mode: str = "hybrid",
    ) -> dict[str, Any]:
        if not session.paper_id:
            raise ValueError("Paper chat session is not bound to a paper")
        paper = db.get(Paper, session.paper_id)
        if not paper:
            raise ValueError("Paper not found")

        previous_messages = self._all_messages(db, session.id)
        self._compact_memory(db, session, previous_messages)
        db.refresh(session)

        recent_messages = self._recent_uncompressed_messages(previous_messages, session.compressed_until_message_id)
        recent_history = [self._message_for_context(message) for message in recent_messages]
        recent_message_ids = [message.id for message in recent_messages]

        user_message = ChatMessage(session_id=session.id, role="user", content=question, citations=[], retrieval_metadata={})
        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        rewrite = self.llm.rewrite_paper_chat_query(
            question,
            memory_summary=session.memory_summary or "",
            history=recent_history,
            paper_title=paper.original_filename,
        )
        rewritten_query = rewrite["query"]
        evidence_answer = EvidenceRagService(self.settings, self.retriever, self.llm).answer_paper_chat(
            db,
            paper.library_id,
            rewritten_query,
            question,
            [paper.id],
            top_k,
            recent_history,
            session.memory_summary or "",
        )
        retrieval_metadata = {
            **evidence_answer["retrieval_metadata"],
            "context_mode": context_mode,
            "paper_id": paper.id,
            "original_question": question,
            "rewritten_query": rewritten_query,
            "rewrite_source": rewrite["source"],
            "recent_message_ids": recent_message_ids,
            "compressed_until_message_id": session.compressed_until_message_id,
        }
        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=evidence_answer["answer"],
            citations=evidence_answer["citations"],
            retrieval_metadata=retrieval_metadata,
        )
        session.context_mode = context_mode
        session.updated_at = datetime.utcnow()
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        db.refresh(session)
        return {
            "user_message": user_message,
            "assistant_message": assistant_message,
            "answer": evidence_answer["answer"],
            "citations": evidence_answer["citations"],
            "missing_evidence": evidence_answer["missing_evidence"],
            "memory_summary": session.memory_summary or "",
            "compressed_until_message_id": session.compressed_until_message_id,
            "memory_updated_at": session.memory_updated_at.isoformat() if session.memory_updated_at else None,
            "retrieval_metadata": retrieval_metadata,
        }

    def _all_messages(self, db: Session, session_id: str) -> list[ChatMessage]:
        return (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.asc())
            .all()
        )

    def _compact_memory(self, db: Session, session: ChatSession, previous_messages: list[ChatMessage]) -> None:
        boundary = session.compressed_until_message_id or 0
        uncompressed = [message for message in previous_messages if message.id > boundary]
        if len(uncompressed) <= self.COMPRESSION_TRIGGER_MESSAGES:
            return

        compact_messages = uncompressed[:-self.RECENT_MESSAGE_LIMIT]
        if not compact_messages:
            return

        compact_payload = [self._message_for_context(message) for message in compact_messages]
        session.memory_summary = self.llm.summarize_chat_memory(compact_payload, session.memory_summary or "")
        session.compressed_until_message_id = compact_messages[-1].id
        session.memory_updated_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        db.commit()

    def _recent_uncompressed_messages(
        self,
        previous_messages: list[ChatMessage],
        compressed_until_message_id: int | None,
    ) -> list[ChatMessage]:
        boundary = compressed_until_message_id or 0
        uncompressed = [message for message in previous_messages if message.id > boundary]
        return uncompressed[-self.RECENT_MESSAGE_LIMIT :]

    def _message_for_context(self, message: ChatMessage) -> dict[str, str]:
        return {
            "role": message.role,
            "content": self._truncate(message.content, self.MEMORY_MESSAGE_CHAR_LIMIT),
        }

    def _truncate(self, text: str, max_chars: int) -> str:
        compact = " ".join(text.split())
        if len(compact) <= max_chars:
            return compact
        return compact[:max_chars].rsplit(" ", 1)[0] + "..."
