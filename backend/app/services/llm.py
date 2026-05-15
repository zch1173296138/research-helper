import json
import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Any
from typing import TypeVar

from openai import OpenAI
from openai import OpenAIError

from backend.app.core.config import Settings
from backend.app.services.evidence_types import EvidenceDecision
from backend.app.services.vector_store import RetrievedChunk


MISSING = "未在已导入文献中找到依据。"
NOT_FOUND = "未在原文中找到"
SUMMARY_FIELDS = (
    "research_question",
    "method",
    "dataset_or_materials",
    "experiment_setup",
    "key_findings",
    "limitations",
    "future_work",
)
T = TypeVar("T")


class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        if settings.openai_api_key:
            self.client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                max_retries=0,
                timeout=settings.llm_timeout_seconds,
            )

    def answer_with_citations(self, question: str, chunks: list[RetrievedChunk]) -> dict[str, Any]:
        if not chunks:
            return {"answer": MISSING, "citations": [], "missing_evidence": True}

        citations = [self._citation_from_chunk(chunk) for chunk in chunks[:6]]
        if self.client is None:
            answer = self._extractive_answer(question, chunks)
            return {"answer": answer, "citations": citations[:3], "missing_evidence": False}

        context = "\n\n".join(
            f"[{idx}] paper_id={chunk.paper_id}; filename={chunk.filename}; section={chunk.section_title}\n{chunk.text}"
            for idx, chunk in enumerate(chunks[:8], start=1)
        )
        extra_body = self._completion_extra_body()
        prompt = (
            "你是科研文献综述助手。只能基于给定 context 回答。"
            "如果 context 不支持回答，返回“未在已导入文献中找到依据”。"
            "回答要简洁，并在关键结论后使用 [1] [2] 这样的引用编号。\n\n"
            "请用易读的 Markdown 格式输出：使用简短段落、项目符号列表和加粗标签，"
            "在主要部分之间保留空行，不要输出一整段连续文本。\n\n"
            f"Question:\n{question}\n\nContext:\n{context}"
        )
        try:
            response = self._call_with_deadline(
                lambda: self.client.chat.completions.create(
                    model=self.settings.chat_model,
                    messages=[
                        {"role": "system", "content": "你回答科研问题时必须保守、可追溯、不可编造引用。"},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    extra_body=extra_body,
                )
            )
            answer = response.choices[0].message.content or MISSING
        except (OpenAIError, FutureTimeout):
            answer = self._extractive_answer(question, chunks)
        missing = MISSING in answer
        return {"answer": answer, "citations": [] if missing else citations[:6], "missing_evidence": missing}

    def answer_paper_chat(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        history: list[dict[str, str]] | None = None,
        memory_summary: str = "",
    ) -> dict[str, Any]:
        if not chunks:
            return {"answer": MISSING, "citations": [], "missing_evidence": True, "answer_source_chunk_ids": []}

        citation_map = {f"C{index}": chunk for index, chunk in enumerate(chunks[:8], start=1)}
        citations = [self._citation_from_chunk(chunk, citation_id) for citation_id, chunk in citation_map.items()]
        if self.client is None:
            answer = self._extractive_answer(question, chunks)
            return {"answer": f"{answer} [C1]", "citations": citations[:1], "missing_evidence": False}

        messages = self._build_paper_chat_messages(question, citation_map, history or [], memory_summary)
        try:
            response = self._call_with_deadline(
                lambda: self.client.chat.completions.create(
                    model=self.settings.chat_model,
                    messages=messages,
                    temperature=0.2,
                    extra_body=self._completion_extra_body(),
                )
            )
            answer = response.choices[0].message.content or MISSING
        except (OpenAIError, FutureTimeout):
            answer = f"{self._extractive_answer(question, chunks)} [C1]"

        if MISSING in answer or "未在论文中找到足够依据" in answer:
            return {"answer": answer, "citations": [], "missing_evidence": True}

        used_ids = self._valid_citation_ids(answer, set(citation_map))
        if not used_ids:
            answer = f"{self._extractive_answer(question, chunks)} [C1]"
            used_ids = ["C1"]
        selected = [self._citation_from_chunk(citation_map[citation_id], citation_id) for citation_id in used_ids]
        return {"answer": answer, "citations": selected, "missing_evidence": False}

    def judge_evidence(self, question: str, chunks: list[RetrievedChunk]) -> list[EvidenceDecision]:
        if self.client is None or not chunks:
            return []
        candidates = [
            {
                "chunk_id": chunk.chunk_id,
                "paper_id": chunk.paper_id,
                "filename": chunk.filename,
                "section": chunk.section_path or chunk.section_title or chunk.section_type,
                "pages": [chunk.page_start, chunk.page_end],
                "text": self._truncate(chunk.text, 900),
            }
            for chunk in chunks[:30]
        ]
        prompt = (
            "Judge whether each candidate evidence chunk can help answer the question. "
            "Return strict JSON only with a top-level `decisions` array. Each item must contain: "
            "`chunk_id`, `decision` (`accept`, `maybe`, or `reject`), `reason`, "
            "`support_level` (`direct`, `partial`, `background`, or `none`), "
            "`answerable_claims` as an array of short strings, and `concise_summary`. "
            "Accept only chunks that directly or partially support an answer. Reject background-only or irrelevant chunks. "
            "Keep summaries concise and grounded in the candidate text.\n\n"
            f"Question:\n{question}\n\nCandidates:\n{json.dumps(candidates, ensure_ascii=False)}"
        )
        response = self._call_with_deadline(
            lambda: self.client.chat.completions.create(
                model=self.settings.chat_model,
                messages=[
                    {"role": "system", "content": "You are a strict evidence relevance judge. Return valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                extra_body=self._completion_extra_body(),
            )
        )
        content = response.choices[0].message.content or "{}"
        payload = json.loads(self._extract_json(content))
        raw_decisions = payload.get("decisions") if isinstance(payload, dict) else payload
        if not isinstance(raw_decisions, list):
            return []
        valid_decisions = {"accept", "maybe", "reject"}
        valid_support = {"direct", "partial", "background", "none"}
        parsed: list[EvidenceDecision] = []
        for item in raw_decisions:
            if not isinstance(item, dict):
                continue
            chunk_id = str(item.get("chunk_id") or "").strip()
            decision = str(item.get("decision") or "reject").strip().lower()
            support = str(item.get("support_level") or "none").strip().lower()
            if decision not in valid_decisions:
                decision = "reject"
            if support not in valid_support:
                support = "none"
            claims = item.get("answerable_claims") or []
            if not isinstance(claims, list):
                claims = [str(claims)]
            parsed.append(
                EvidenceDecision(
                    chunk_id=chunk_id,
                    decision=decision,  # type: ignore[arg-type]
                    reason=self._truncate(str(item.get("reason") or ""), 500),
                    support_level=support,  # type: ignore[arg-type]
                    answerable_claims=[self._truncate(str(claim), 300) for claim in claims[:5]],
                    concise_summary=self._truncate(str(item.get("concise_summary") or ""), 700),
                    judge_source="llm_json",
                )
            )
        return parsed

    def answer_with_evidence(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        decisions: list[EvidenceDecision],
    ) -> dict[str, Any]:
        return self._answer_from_accepted_evidence(question, chunks, decisions, [], "", paper_chat=False)

    def answer_paper_chat_with_evidence(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        decisions: list[EvidenceDecision],
        history: list[dict[str, str]] | None = None,
        memory_summary: str = "",
    ) -> dict[str, Any]:
        return self._answer_from_accepted_evidence(question, chunks, decisions, history or [], memory_summary, paper_chat=True)

    def _answer_from_accepted_evidence(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        decisions: list[EvidenceDecision],
        history: list[dict[str, str]],
        memory_summary: str,
        paper_chat: bool,
    ) -> dict[str, Any]:
        if not chunks:
            return {"answer": MISSING, "citations": [], "missing_evidence": True, "answer_source_chunk_ids": []}

        citation_map = {f"C{index}": chunk for index, chunk in enumerate(chunks[:8], start=1)}
        citations = [self._citation_from_chunk(chunk, citation_id) for citation_id, chunk in citation_map.items()]
        if self.client is None:
            extractive = self._extractive_answer_with_claim_sources(question, chunks, decisions)
            answer = str(extractive["answer"])
            answer_source_chunk_ids = list(extractive["answer_source_chunk_ids"])
            selected_ids = self._selected_claim_citation_ids(
                list(extractive["claims"]),
                citation_map,
                decisions,
            )
            selected = [self._citation_from_chunk(citation_map[citation_id], citation_id) for citation_id in selected_ids]
            return {
                "answer": answer,
                "citations": selected,
                "missing_evidence": False,
                "answer_source_chunk_ids": answer_source_chunk_ids,
                "answer_claims": list(extractive["claims"]),
                "claim_sources": list(extractive["claims"]),
                "claim_count": len(extractive["claims"]),
                "claim_candidates": list(extractive.get("claim_candidates") or []),
                "citation_selection_mode": self.settings.rag_citation_selection_mode,
            }

        messages = self._build_evidence_answer_messages(
            question,
            citation_map,
            decisions,
            history,
            memory_summary,
            paper_chat,
        )
        try:
            response = self._call_with_deadline(
                lambda: self.client.chat.completions.create(
                    model=self.settings.chat_model,
                    messages=messages,
                    temperature=0.2,
                    extra_body=self._completion_extra_body(),
                )
            )
            answer = response.choices[0].message.content or MISSING
            answer_source_chunk_ids: list[str] = []
            answer_claims: list[dict[str, Any]] = []
            claim_candidates: list[dict[str, Any]] = []
        except (OpenAIError, FutureTimeout):
            extractive = self._extractive_answer_with_claim_sources(question, chunks, decisions)
            answer = str(extractive["answer"])
            answer_source_chunk_ids = list(extractive["answer_source_chunk_ids"])
            answer_claims = list(extractive["claims"])
            claim_candidates = list(extractive.get("claim_candidates") or [])

        if MISSING in answer or "insufficient evidence" in answer.lower():
            return {
                "answer": answer,
                "citations": [],
                "missing_evidence": True,
                "answer_source_chunk_ids": answer_source_chunk_ids,
                "answer_claims": answer_claims,
                "claim_sources": answer_claims,
                "claim_count": len(answer_claims),
                "claim_candidates": [],
                "citation_selection_mode": self.settings.rag_citation_selection_mode,
            }

        used_ids = self._valid_citation_ids(answer, set(citation_map))
        selected_ids = self._selected_evidence_citation_ids(
            used_ids,
            citation_map,
            decisions,
            answer_source_chunk_ids=answer_source_chunk_ids,
        )
        if not used_ids:
            extractive = self._extractive_answer_with_claim_sources(question, chunks, decisions)
            answer = str(extractive["answer"])
            answer_source_chunk_ids = list(extractive["answer_source_chunk_ids"])
            answer_claims = list(extractive["claims"])
            claim_candidates = list(extractive.get("claim_candidates") or [])
            selected_ids = self._selected_claim_citation_ids(
                answer_claims,
                citation_map,
                decisions,
            )
        selected = [self._citation_from_chunk(citation_map[citation_id], citation_id) for citation_id in selected_ids]
        return {
            "answer": answer,
            "citations": selected,
            "missing_evidence": False,
            "answer_source_chunk_ids": answer_source_chunk_ids,
            "answer_claims": answer_claims,
            "claim_sources": answer_claims,
            "claim_count": len(answer_claims),
            "claim_candidates": claim_candidates,
            "citation_selection_mode": self.settings.rag_citation_selection_mode,
        }

    def _selected_claim_citation_ids(
        self,
        claims: list[dict[str, str]],
        citation_map: dict[str, RetrievedChunk],
        decisions: list[EvidenceDecision],
    ) -> list[str]:
        claim_ids = [
            str(claim.get("citation_id") or "").strip()
            for claim in claims
            if str(claim.get("citation_id") or "").strip() in citation_map
        ]
        claim_ids = self._dedupe_preserve_order(claim_ids)
        if not claim_ids:
            return self._selected_evidence_citation_ids([], citation_map, decisions)

        mode = self.settings.rag_citation_selection_mode
        if mode == "strict":
            return self._selected_evidence_citation_ids([], citation_map, decisions)
        if mode == "answer_linked":
            return claim_ids
        if mode == "precision":
            high_confidence = set(self._accepted_direct_partial_citation_ids(citation_map, decisions))
            return [citation_id for citation_id in claim_ids if citation_id in high_confidence]
        return self._selected_evidence_citation_ids(
            claim_ids,
            citation_map,
            decisions,
            answer_source_chunk_ids=[
                str(claim.get("chunk_id") or "").strip()
                for claim in claims
                if str(claim.get("chunk_id") or "").strip()
            ],
        )

    def _selected_evidence_citation_ids(
        self,
        used_ids: list[str],
        citation_map: dict[str, RetrievedChunk],
        decisions: list[EvidenceDecision],
        answer_source_chunk_ids: list[str] | None = None,
        supplemental_limit: int = 3,
    ) -> list[str]:
        selected = [citation_id for citation_id in used_ids if citation_id in citation_map]
        mode = self.settings.rag_citation_selection_mode
        fallback_ids = self._fallback_evidence_citation_ids(citation_map, decisions, supplemental_limit)
        if mode == "strict":
            return selected or fallback_ids[:1]
        if mode == "answer_linked":
            if selected:
                return selected
            linked_ids = self._citation_ids_by_chunk_ids(citation_map, answer_source_chunk_ids or [])
            return linked_ids or fallback_ids[:1]
        if mode == "precision":
            return self._precision_evidence_citation_ids(selected, citation_map, decisions, supplemental_limit=1)

        return self._current_evidence_citation_ids(selected, citation_map, decisions, supplemental_limit)

    def _current_evidence_citation_ids(
        self,
        selected: list[str],
        citation_map: dict[str, RetrievedChunk],
        decisions: list[EvidenceDecision],
        supplemental_limit: int,
    ) -> list[str]:
        decision_by_chunk = {decision.chunk_id: decision for decision in decisions}
        prioritized = self._citation_ids_by_support(citation_map, decision_by_chunk, {"direct", "partial"})
        if not prioritized:
            prioritized = self._citation_ids_by_support(citation_map, decision_by_chunk, {"background"})
        if not prioritized:
            prioritized = list(citation_map)[:supplemental_limit]
        for citation_id in prioritized:
            if citation_id not in selected:
                selected.append(citation_id)
            if len([item for item in selected if item in prioritized]) >= supplemental_limit:
                break
        return selected

    def _precision_evidence_citation_ids(
        self,
        selected: list[str],
        citation_map: dict[str, RetrievedChunk],
        decisions: list[EvidenceDecision],
        supplemental_limit: int = 1,
    ) -> list[str]:
        high_confidence = self._accepted_direct_partial_citation_ids(citation_map, decisions)
        if selected:
            filtered = [citation_id for citation_id in selected if citation_id in high_confidence]
            if filtered:
                return filtered
            return high_confidence[:supplemental_limit]
        return high_confidence[:supplemental_limit]

    def _accepted_direct_partial_citation_ids(
        self,
        citation_map: dict[str, RetrievedChunk],
        decisions: list[EvidenceDecision],
    ) -> list[str]:
        decision_by_chunk = {decision.chunk_id: decision for decision in decisions}
        result: list[str] = []
        for citation_id, chunk in citation_map.items():
            decision = decision_by_chunk.get(chunk.chunk_id)
            if (
                decision
                and decision.decision == "accept"
                and decision.support_level in {"direct", "partial"}
            ):
                result.append(citation_id)
        return result

    def _fallback_evidence_citation_ids(
        self,
        citation_map: dict[str, RetrievedChunk],
        decisions: list[EvidenceDecision],
        limit: int,
    ) -> list[str]:
        decision_by_chunk = {decision.chunk_id: decision for decision in decisions}
        for support_levels in ({"direct", "partial"}, {"background"}):
            ids = self._citation_ids_by_support(citation_map, decision_by_chunk, support_levels)
            if ids:
                return ids[:limit]
        return list(citation_map)[:limit]

    def _citation_ids_by_chunk_ids(
        self,
        citation_map: dict[str, RetrievedChunk],
        chunk_ids: list[str],
    ) -> list[str]:
        source_ids = set(chunk_ids)
        return [citation_id for citation_id, chunk in citation_map.items() if chunk.chunk_id in source_ids]

    def _citation_ids_by_support(
        self,
        citation_map: dict[str, RetrievedChunk],
        decision_by_chunk: dict[str, EvidenceDecision],
        support_levels: set[str],
    ) -> list[str]:
        result: list[str] = []
        for citation_id, chunk in citation_map.items():
            decision = decision_by_chunk.get(chunk.chunk_id)
            if decision and decision.decision in {"accept", "maybe"} and decision.support_level in support_levels:
                result.append(citation_id)
        return result

    def _build_paper_chat_messages(
        self,
        question: str,
        citation_map: dict[str, RetrievedChunk],
        history: list[dict[str, str]],
        memory_summary: str,
    ) -> list[dict[str, str]]:
        context = "\n\n".join(
            (
                f"[{citation_id}] paper_id={chunk.paper_id}; filename={chunk.filename}; "
                f"section={chunk.section_path or chunk.section_title}; pages={chunk.page_start or '?'}-{chunk.page_end or '?'}\n"
                f"{self._truncate(chunk.text, 1400)}"
            )
            for citation_id, chunk in citation_map.items()
        )
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You are a rigorous paper QA assistant. Answer only from the provided Evidence. "
                    "Every key factual claim about the paper must cite one of the Evidence ids like [C1]. "
                    "Conversation memory and recent chat history are for intent only; they are not evidence and must never be cited. "
                    "If the Evidence is insufficient, say that the paper evidence is insufficient. "
                    "Unless the user explicitly asks for a short answer, write a substantive Chinese answer. "
                    "For overview questions, cover research problem, proposed method, key modules, experiments/results, and limitations when evidence is available. "
                    "Prefer 4-6 compact bullet points or short paragraphs, and attach citations to each important point."
                ),
            }
        ]
        if memory_summary.strip():
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Conversation memory, not evidence. Use this only to understand follow-up intent:\n"
                        f"{self._truncate(memory_summary, 1200)}"
                    ),
                }
            )
        for item in history[-10:]:
            role = item.get("role", "")
            if role not in {"user", "assistant"}:
                continue
            content = self._truncate(item.get("content", ""), 700)
            if content:
                messages.append({"role": role, "content": content})
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Question:\n{question}\n\n"
                    "Evidence:\n"
                    f"{context}\n\n"
                    "Answer in Chinese with citations from the Evidence ids only. "
                    "Do not answer in only one or two short sentences when the question asks for an overview or method explanation."
                ),
            }
        )
        return messages

    def _build_evidence_answer_messages(
        self,
        question: str,
        citation_map: dict[str, RetrievedChunk],
        decisions: list[EvidenceDecision],
        history: list[dict[str, str]],
        memory_summary: str,
        paper_chat: bool,
    ) -> list[dict[str, str]]:
        decision_by_chunk = {decision.chunk_id: decision for decision in decisions}
        evidence_blocks = []
        for citation_id, chunk in citation_map.items():
            decision = decision_by_chunk.get(chunk.chunk_id)
            summary = decision.concise_summary if decision and decision.concise_summary else self._truncate(chunk.text, 600)
            claims = "; ".join(decision.answerable_claims[:3]) if decision else ""
            evidence_blocks.append(
                (
                    f"[{citation_id}] chunk_id={chunk.chunk_id}; paper_id={chunk.paper_id}; "
                    f"filename={chunk.filename}; section={chunk.section_path or chunk.section_title}; "
                    f"pages={chunk.page_start or '?'}-{chunk.page_end or '?'}\n"
                    f"Evidence summary: {summary}\n"
                    f"Supported claims: {claims or 'Not separately listed.'}\n"
                    f"Source snippet: {self._truncate(chunk.text, 850)}"
                )
            )
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You are a rigorous research QA assistant. Answer only from Accepted Evidence. "
                    "Every factual claim must cite one of the accepted Evidence ids like [C1]. "
                    "Do not cite conversation memory, rejected evidence, or background knowledge. "
                    "If the accepted evidence is insufficient, say that insufficient evidence was found. "
                    "Use Chinese unless the user asks otherwise."
                ),
            }
        ]
        if paper_chat and memory_summary.strip():
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Conversation memory, not evidence. Use only to resolve follow-up intent:\n"
                        f"{self._truncate(memory_summary, 1200)}"
                    ),
                }
            )
        if paper_chat:
            for item in history[-10:]:
                role = item.get("role", "")
                if role not in {"user", "assistant"}:
                    continue
                content = self._truncate(item.get("content", ""), 700)
                if content:
                    messages.append({"role": role, "content": content})
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Question:\n{question}\n\n"
                    "Accepted Evidence:\n"
                    f"{chr(10).join(evidence_blocks)}\n\n"
                    "Answer with citations from the accepted Evidence ids only. "
                    "Do not use any citation id that is not listed above."
                ),
            }
        )
        return messages

    def rewrite_paper_chat_query(
        self,
        question: str,
        memory_summary: str = "",
        history: list[dict[str, str]] | None = None,
        paper_title: str = "",
    ) -> dict[str, str]:
        fallback_query = self._fallback_paper_chat_query_rewrite(question, memory_summary, history or [], paper_title)
        if self.client is None:
            return {"query": fallback_query, "source": "fallback"}

        history_text = self._format_history(history or [], max_messages=6, max_chars=320)
        prompt = (
            "Rewrite the user's paper-chat question into a concise standalone retrieval query. "
            "Use the conversation memory and recent turns only to resolve references. "
            "Do not answer the question. Return only the search query.\n\n"
            f"Paper title: {paper_title or 'unknown'}\n\n"
            f"Memory:\n{memory_summary or 'None'}\n\n"
            f"Recent turns:\n{history_text or 'None'}\n\n"
            f"Question:\n{question}"
        )
        try:
            response = self._call_with_deadline(
                lambda: self.client.chat.completions.create(
                    model=self.settings.chat_model,
                    messages=[
                        {"role": "system", "content": "Return only a standalone retrieval query."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.0,
                    extra_body=self._completion_extra_body(),
                )
            )
            rewritten = (response.choices[0].message.content or "").strip()
        except (OpenAIError, FutureTimeout):
            return {"query": fallback_query, "source": "fallback"}

        rewritten = re.sub(r"^```(?:text)?|```$", "", rewritten).strip()
        if not rewritten:
            return {"query": fallback_query, "source": "fallback"}
        return {"query": self._truncate(rewritten, 500), "source": "llm"}

    def summarize_chat_memory(self, messages: list[dict[str, str]], previous_summary: str = "") -> str:
        if not messages:
            return previous_summary
        compact_history = self._format_history(messages, max_messages=24, max_chars=500)
        if self.client is None:
            return self._fallback_memory_summary(messages, previous_summary)
        prompt = (
            "Compress these paper-chat turns into a durable memory summary. Merge with the previous summary. "
            "Preserve user preferences, unresolved questions, prior clarifications, cited topics, and stable discussion state. "
            "Do not add facts that were not present in the conversation. Keep it under 220 words.\n\n"
            f"Previous summary:\n{previous_summary or 'None'}\n\n"
            f"Messages:\n{compact_history}"
        )
        try:
            response = self._call_with_deadline(
                lambda: self.client.chat.completions.create(
                    model=self.settings.chat_model,
                    messages=[
                        {"role": "system", "content": "你只做聊天记忆压缩，不补充外部信息。"},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    extra_body=self._completion_extra_body(),
                )
            )
            return (response.choices[0].message.content or previous_summary).strip()
        except (OpenAIError, FutureTimeout):
            return self._fallback_memory_summary(messages, previous_summary)

    def summarize_paper(self, filename: str, chunks: list[RetrievedChunk]) -> dict[str, Any]:
        if not chunks:
            return self._empty_summary(filename)
        selected_chunks = self._select_summary_chunks(chunks)
        fallback_summary = self._fallback_summary(filename, chunks)
        if self.client is None:
            return fallback_summary

        context = "\n\n".join(
            (
                f"[{idx}] chunk_id={chunk.chunk_id}; section={chunk.section_title or 'unknown'}; "
                f"pages={chunk.page_start or '?'}-{chunk.page_end or '?'}\n"
                f"{self._truncate(self._summary_text_for_chunk(chunk), 1400)}"
            )
            for idx, chunk in enumerate(selected_chunks, start=1)
        )
        schema_hint = {
            "research_question": "",
            "method": "",
            "dataset_or_materials": "",
            "experiment_setup": "",
            "key_findings": "",
            "limitations": "",
            "future_work": "",
            "citations": [{"field": "", "quote": "", "chunk_index": 1}],
        }
        extra_body = self._completion_extra_body()
        prompt = (
            "请基于给定论文片段生成中文结构化摘要，只输出严格 JSON，不要 Markdown。"
            "每个字段尽量用 1-3 句综合概括，不要逐字摘抄。"
            "不要把标题、作者、单位、邮箱、会议引用格式或关键词列表当作研究问题或研究结论。"
            "每个非空字段必须能由 Chunks 中的论文正文支持；如果没有正文证据才写“未在原文中找到”。"
            "method、dataset_or_materials、experiment_setup、key_findings、limitations、future_work "
            "都可以从相关片段中归纳；只有完全没有证据时才写“未在原文中找到”。"
            "citations 至少给 3 条，quote 使用支持对应字段的原文短句，chunk_index 对应输入片段编号。"
            f"JSON schema 示例：{json.dumps(schema_hint, ensure_ascii=False)}\n\n"
            f"Filename: {filename}\n\nChunks:\n{context}"
        )
        try:
            response = self._call_with_deadline(
                lambda: self.client.chat.completions.create(
                    model=self.settings.chat_model,
                    messages=[
                        {"role": "system", "content": "你是严谨的论文信息抽取器，只输出 JSON。"},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    extra_body=extra_body,
                )
            )
            content = response.choices[0].message.content or "{}"
        except (OpenAIError, FutureTimeout):
            return fallback_summary
        try:
            summary = self._normalize_summary(json.loads(self._extract_json(content)), filename)
        except json.JSONDecodeError:
            return fallback_summary
        return self._repair_summary_with_fallback(summary, fallback_summary)

    def _call_with_deadline(self, call: Callable[[], T]) -> T:
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(call)
        try:
            return future.result(timeout=max(1, self.settings.llm_timeout_seconds))
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _completion_extra_body(self) -> dict[str, Any]:
        if "dashscope" in str(self.settings.openai_base_url).lower():
            return {"enable_thinking": False}
        return {}

    def build_matrix(self, rows: list[dict[str, Any]], topic: str) -> list[dict[str, Any]]:
        # v1 keeps matrix deterministic from summaries; model enhancement can be added later.
        return rows

    def _select_summary_chunks(self, chunks: list[RetrievedChunk], max_chunks: int = 14) -> list[RetrievedChunk]:
        candidates = self._summary_content_chunks(chunks)
        selected: list[RetrievedChunk] = []
        seen: set[str] = set()

        def add(chunk: RetrievedChunk) -> None:
            if chunk.chunk_id not in seen:
                seen.add(chunk.chunk_id)
                selected.append(chunk)

        for field in SUMMARY_FIELDS:
            chunk = self._best_summary_chunk(candidates, field)
            if chunk:
                add(chunk)

        for chunk in candidates:
            if len(selected) >= max_chunks:
                break
            add(chunk)

        return selected[:max_chunks]

    def _summary_content_chunks(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        candidates = [chunk for chunk in chunks if self._summary_text_for_chunk(chunk)]
        return candidates or chunks

    def _summary_text_for_chunk(self, chunk: RetrievedChunk) -> str:
        text = re.sub(r"\s+", " ", chunk.text).strip()
        if not text:
            return ""
        if self._is_summary_skip_section(chunk):
            return ""
        if self._is_summary_heading_only(text):
            return ""

        lower = text.lower()
        for marker in ("# abstract", " abstract ", "# abstract ", " abstract\n"):
            index = lower.find(marker)
            if index >= 0:
                trimmed = text[index:].strip()
                if len(trimmed) >= 160:
                    return trimmed
        if self._looks_like_author_metadata(text):
            return ""
        return text

    def _is_summary_heading_only(self, text: str) -> bool:
        plain = re.sub(r"^#+\s*", "", text).strip()
        return bool(
            len(plain.split()) <= 8
            and re.fullmatch(r"(?:\d+(?:\.\d+)*\.?\s*)?[A-Z][A-Za-z0-9 &()/:-]{2,80}", plain)
        )

    def _summary_haystack(self, chunk: RetrievedChunk) -> str:
        return f"{chunk.section_title}\n{chunk.section_path}\n{chunk.section_type}\n{self._summary_text_for_chunk(chunk)[:900]}".lower()

    def _is_summary_skip_section(self, chunk: RetrievedChunk) -> bool:
        heading = f"{chunk.section_title} {chunk.section_path} {chunk.section_type}".lower()
        skip_terms = (
            "acm reference format",
            "article info",
            "ccs concepts",
            "keywords",
            "reference",
            "bibliography",
            "acknowledg",
        )
        return any(term in heading for term in skip_terms)

    def _looks_like_author_metadata(self, text: str) -> bool:
        lower = text.lower()
        metadata_hits = sum(
            marker in lower
            for marker in (
                "@",
                "university",
                "school of",
                "department",
                "institute",
                "college",
                "conference",
                "proceedings",
                "doi.org",
                "copyright",
            )
        )
        research_hits = sum(
            marker in lower
            for marker in (
                "we propose",
                "we introduce",
                "we conduct",
                "we evaluate",
                "experiment",
                "results demonstrate",
                "method",
                "dataset",
                "accuracy",
            )
        )
        return metadata_hits >= 2 and research_hits == 0

    def _best_summary_chunk(self, chunks: list[RetrievedChunk], field: str) -> RetrievedChunk | None:
        scored: list[tuple[int, int, RetrievedChunk]] = []
        for index, chunk in enumerate(chunks):
            text = self._summary_text_for_chunk(chunk)
            if not text:
                continue
            haystack = self._summary_haystack(chunk)
            heading = f"{chunk.section_title} {chunk.section_path} {chunk.section_type}".lower()
            score = 0
            for keyword in self._summary_field_keywords(field):
                if keyword in haystack:
                    score += 3 if keyword in heading else 1
            if field == "research_question" and chunk.section_type in {"abstract", "introduction"}:
                score += 4
            if field == "method" and any(term in heading for term in ("method", "overview", "architecture")):
                score += 4
            if field == "dataset_or_materials" and any(term in heading for term in ("dataset", "datasets", "benchmark")):
                score += 4
            if field == "experiment_setup" and any(
                term in heading for term in ("experimental environment", "experimental datasets", "experiment")
            ):
                score += 4
            if field == "key_findings" and any(term in haystack for term in ("results demonstrate", "achieves", "outperform", "accuracy")):
                score += 3
            if field == "key_findings" and any(term in heading for term in ("result", "experiment", "conclusion")):
                score += 5
            if field == "limitations" and any(term in heading for term in ("limitation", "discussion", "result")):
                score += 3
            if field in {"limitations", "future_work"} and score == 0:
                continue
            if score > 0:
                scored.append((score, -index, chunk))
        if not scored and field in {"research_question", "key_findings"}:
            return chunks[0] if chunks else None
        if not scored:
            return None
        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return scored[0][2]

    def _summary_field_keywords(self, field: str) -> tuple[str, ...]:
        keywords = {
            "research_question": (
                "abstract",
                "introduction",
                "however",
                "challenge",
                "limitation",
                "problem",
                "to address",
                "falling short",
                "struggle",
            ),
            "method": (
                "method",
                "overview",
                "approach",
                "architecture",
                "model",
                "algorithm",
                "module",
                "transformer",
                "we propose",
                "we introduce",
            ),
            "dataset_or_materials": (
                "dataset",
                "data",
                "benchmark",
                "materials",
                "mf",
                "cbf",
                "models",
                "training",
            ),
            "experiment_setup": (
                "experiment",
                "evaluation",
                "environment",
                "setup",
                "trained",
                "optimizer",
                "epochs",
                "gpu",
                "split",
            ),
            "key_findings": (
                "result",
                "finding",
                "performance",
                "accuracy",
                "outperform",
                "achieves",
                "state-of-the-art",
                "demonstrate",
                "conclusion",
            ),
            "limitations": (
                "limitation",
                "shortcoming",
                "shortcomings",
                "poorly",
                "threat",
                "future work",
            ),
            "future_work": (
                "future",
                "future work",
                "next",
            ),
        }
        return keywords.get(field, ())

    def _field_excerpt(self, field: str, chunk: RetrievedChunk | None) -> str:
        if chunk is None:
            return NOT_FOUND
        text = self._summary_text_for_chunk(chunk)
        if not text:
            return NOT_FOUND
        sentences = self._summary_sentences(text)
        if not sentences:
            return self._truncate(text, 420)
        selected = self._select_field_sentences(field, sentences)
        if not selected and field in {"research_question", "key_findings"}:
            selected = sentences[:2]
        if not selected:
            return NOT_FOUND
        return self._truncate(" ".join(selected[:3]), 520)

    def _summary_sentences(self, text: str) -> list[str]:
        cleaned = re.sub(r"!\[[^\]]*]\([^)]+\)", " ", text)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        cleaned = re.sub(r"#+\s*", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned = re.sub(
            r"^(?:\d+(?:\.\d+)*\.?\s*)?"
            r"(?:abstract|introduction|overview|method|experiments?|experimental environment|"
            r"experimental datasets|results?|conclusion|complex b-rep feature \(cbf\) dataset)\s+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        parts = re.split(r"(?<=[.!?。！？])\s+", cleaned)
        return [part.strip() for part in parts if len(part.strip()) >= 30]

    def _select_field_sentences(self, field: str, sentences: list[str]) -> list[str]:
        keywords = self._summary_field_keywords(field)
        selected: list[str] = []
        for sentence in sentences:
            lowered = sentence.lower()
            if any(keyword in lowered for keyword in keywords):
                selected.append(sentence)
            if len(selected) >= 3:
                break
        return selected

    def _extract_json(self, content: str) -> str:
        stripped = content.strip()
        if stripped.startswith("```"):
            stripped = stripped.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            return stripped[start : end + 1]
        return stripped

    def _normalize_summary(self, summary: dict[str, Any], filename: str) -> dict[str, Any]:
        defaults = self._empty_summary(filename)
        normalized = {**defaults, **summary, "filename": summary.get("filename") or filename}
        for key in SUMMARY_FIELDS:
            value = normalized.get(key)
            normalized[key] = str(value).strip() if value else NOT_FOUND
        citations = normalized.get("citations")
        normalized["citations"] = citations if isinstance(citations, list) else []
        return normalized

    def _repair_summary_with_fallback(self, summary: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
        repaired = dict(summary)
        for key in SUMMARY_FIELDS:
            value = str(repaired.get(key) or "").strip()
            fallback_value = str(fallback.get(key) or "").strip()
            if not fallback_value or fallback_value == NOT_FOUND:
                continue
            if value == NOT_FOUND or self._looks_like_author_metadata(value):
                repaired[key] = fallback_value
        if not repaired.get("citations") and fallback.get("citations"):
            repaired["citations"] = fallback["citations"]
        return repaired

    def _truncate(self, text: str, max_chars: int) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        if len(compact) <= max_chars:
            return compact
        return compact[:max_chars].rsplit(" ", 1)[0] + "..."

    def _extractive_answer(self, question: str, chunks: list[RetrievedChunk]) -> str:
        answer, _source_chunk_ids = self._extractive_answer_with_sources(question, chunks)
        return answer

    def _extractive_answer_with_sources(self, question: str, chunks: list[RetrievedChunk]) -> tuple[str, list[str]]:
        first = chunks[0]
        excerpt = first.text.strip().replace("\n", " ")
        if len(excerpt) > 700:
            excerpt = excerpt[:700].rsplit(" ", 1)[0] + "..."
        answer = f"根据已导入文献中最相关的片段，问题“{question}”可从以下证据开始分析：{excerpt}"
        return answer, [first.chunk_id]

    def _extractive_answer_with_claim_sources(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        decisions: list[EvidenceDecision] | None = None,
        max_claims: int = 3,
    ) -> dict[str, Any]:
        citation_map = {chunk.chunk_id: f"C{index}" for index, chunk in enumerate(chunks[:8], start=1)}
        decision_by_chunk = {decision.chunk_id: decision for decision in decisions or []}
        question_terms = self._claim_terms(question)
        question_intents = self._claim_question_intents(question)
        candidates: list[dict[str, Any]] = []
        seen_sentences: list[str] = []

        for chunk_index, chunk in enumerate(chunks[:8]):
            if chunk.chunk_id not in citation_map:
                continue
            decision = decision_by_chunk.get(chunk.chunk_id)
            if not self._claim_chunk_is_eligible(decision):
                continue
            best_sentence: str | None = None
            best_score: tuple[float, float, int] | None = None
            best_intent_boosts: dict[str, float] = {}
            best_text_score = 0.0
            for sentence_index, sentence in enumerate(self._claim_sentences(chunk.text)):
                normalized = self._normalize_claim_sentence(sentence)
                if not normalized or self._is_near_duplicate_claim(normalized, seen_sentences):
                    continue
                text_score = self._claim_text_score(sentence, question_terms)
                intent_boosts = self._claim_intent_boosts(sentence, question_intents)
                intent_boost = sum(intent_boosts.values())
                if text_score <= 0 and intent_boost <= 0 and question_terms:
                    continue
                score = (
                    self._claim_decision_boost(decision) + text_score + intent_boost,
                    text_score + intent_boost,
                    -sentence_index,
                )
                if best_score is None or score > best_score:
                    best_score = score
                    best_sentence = sentence
                    best_intent_boosts = intent_boosts
                    best_text_score = text_score
            if best_sentence is None or best_score is None:
                continue
            seen_sentences.append(self._normalize_claim_sentence(best_sentence))
            candidates.append(
                {
                    "text": self._truncate(best_sentence, 320),
                    "chunk_id": chunk.chunk_id,
                    "citation_id": citation_map[chunk.chunk_id],
                    "score": best_score[0],
                    "text_score": best_text_score,
                    "has_question_overlap": bool(question_terms and best_text_score > 0),
                    "intent_boosts": best_intent_boosts,
                    "support_priority": self._claim_decision_rank(decision),
                    "chunk_rank": chunk_index + 1,
                    "chunk_index": chunk_index,
                    "decision_rank": self._claim_decision_rank(decision),
                }
            )

        candidates.sort(key=lambda item: (-item["decision_rank"], -item["score"], item["chunk_index"]))
        selected = self._select_claim_candidates(candidates, max_claims)
        selected = sorted(selected, key=lambda item: item["chunk_index"])
        claims = [
            {
                "text": str(item["text"]),
                "chunk_id": str(item["chunk_id"]),
                "citation_id": str(item["citation_id"]),
                "score": round(float(item["score"]), 4),
                "intent_boosts": dict(item.get("intent_boosts") or {}),
                "support_priority": int(item.get("support_priority") or 0),
                "chunk_rank": int(item.get("chunk_rank") or 0),
                "selected_by": str(item.get("selected_by") or "top_score"),
            }
            for item in selected
        ]
        if not claims:
            fallback_answer, fallback_source_chunk_ids = self._extractive_answer_with_sources(question, chunks)
            fallback_citation_id = citation_map.get(fallback_source_chunk_ids[0]) if fallback_source_chunk_ids else None
            if fallback_citation_id:
                fallback_answer = f"{fallback_answer} [{fallback_citation_id}]"
                claims = [
                    {
                        "text": fallback_answer,
                        "chunk_id": fallback_source_chunk_ids[0],
                        "citation_id": fallback_citation_id,
                        "score": 0.0,
                        "intent_boosts": {},
                        "support_priority": 0,
                        "chunk_rank": 1,
                        "selected_by": "fallback",
                    }
                ]
            return {
                "answer": fallback_answer,
                "claims": claims,
                "answer_source_chunk_ids": fallback_source_chunk_ids,
                "claim_candidates": [],
            }

        answer = "\n".join(f"{claim['text']} [{claim['citation_id']}]" for claim in claims)
        return {
            "answer": answer,
            "claims": claims,
            "answer_source_chunk_ids": self._dedupe_preserve_order([claim["chunk_id"] for claim in claims]),
            "claim_candidates": self._claim_candidate_diagnostics(candidates, selected),
        }

    def _select_claim_candidates(self, candidates: list[dict[str, Any]], max_claims: int) -> list[dict[str, Any]]:
        if max_claims <= 0:
            return []
        selected = [dict(item, selected_by="top_score") for item in candidates[:max_claims]]
        if len(candidates) <= max_claims or max_claims < 2:
            return selected

        high_confidence = [item for item in candidates if self._claim_is_high_confidence(item)]
        enough_accept_direct_partial = len([item for item in high_confidence if item["decision_rank"] >= 4]) >= max_claims
        reserve_pool = [
            item
            for item in high_confidence
            if item["decision_rank"] >= 4 or not enough_accept_direct_partial
        ]
        selected_chunk_ids = {str(item["chunk_id"]) for item in selected}
        selected_sentences = [self._normalize_claim_sentence(str(item["text"])) for item in selected]
        last_selected = selected[-1]
        selected_cutoff = float(last_selected["score"])
        displaced_signal = float(last_selected.get("text_score") or 0.0) + sum(float(value) for value in (last_selected.get("intent_boosts") or {}).values())
        min_score = max(0.5, selected_cutoff - 0.6)

        reserve: dict[str, Any] | None = None
        for item in reserve_pool:
            if str(item["chunk_id"]) in selected_chunk_ids:
                continue
            if float(item["score"]) < min_score:
                continue
            reserve_signal = float(item.get("text_score") or 0.0) + sum(float(value) for value in (item.get("intent_boosts") or {}).values())
            if not item.get("intent_boosts"):
                continue
            if float(item["score"]) <= selected_cutoff and reserve_signal <= displaced_signal + 0.15 and float(item["score"]) < selected_cutoff - 0.15:
                continue
            normalized = self._normalize_claim_sentence(str(item["text"]))
            if self._is_near_duplicate_claim(normalized, selected_sentences):
                continue
            reserve = item
            break
        if reserve is None:
            return selected
        selected[-1] = dict(reserve, selected_by="reserve_slot")
        return selected

    def _claim_is_high_confidence(self, item: dict[str, Any]) -> bool:
        return int(item.get("decision_rank") or 0) >= 3

    def _claim_candidate_diagnostics(
        self,
        candidates: list[dict[str, Any]],
        selected: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        selected_chunks = {str(item["chunk_id"]) for item in selected}
        selected_scores = [float(item["score"]) for item in selected]
        cutoff = min(selected_scores) if selected_scores else 0.0
        diagnostics: list[dict[str, Any]] = []
        selected_sentences: list[str] = []
        for item in selected:
            selected_sentences.append(self._normalize_claim_sentence(str(item["text"])))
        for item in candidates:
            chunk_id = str(item["chunk_id"])
            selected_item = chunk_id in selected_chunks
            reason = ""
            if not selected_item:
                if int(item.get("decision_rank") or 0) < 3:
                    reason = "low_support"
                elif self._is_near_duplicate_claim(self._normalize_claim_sentence(str(item["text"])), selected_sentences):
                    reason = "duplicate"
                elif float(item["score"]) >= cutoff:
                    reason = "cut_by_max_claims"
                else:
                    reason = "score_below_selected"
            diagnostics.append(
                {
                    "text": str(item["text"]),
                    "chunk_id": chunk_id,
                    "citation_id": str(item["citation_id"]),
                    "score": round(float(item["score"]), 4),
                    "text_score": round(float(item.get("text_score") or 0.0), 4),
                    "has_question_overlap": bool(item.get("has_question_overlap")),
                    "intent_boosts": dict(item.get("intent_boosts") or {}),
                    "support_priority": int(item.get("support_priority") or 0),
                    "chunk_rank": int(item.get("chunk_rank") or 0),
                    "selected": selected_item,
                    "selected_by": next(
                        (str(selected_candidate.get("selected_by") or "top_score") for selected_candidate in selected if str(selected_candidate["chunk_id"]) == chunk_id),
                        "",
                    ),
                    "unselected_reason": reason,
                }
            )
        return diagnostics

    def _claim_chunk_is_eligible(self, decision: EvidenceDecision | None) -> bool:
        if decision is None:
            return True
        if decision.decision == "reject" or decision.support_level == "none":
            return False
        return (
            (decision.decision == "accept" and decision.support_level in {"direct", "partial", "background"})
            or (decision.decision == "maybe" and decision.support_level == "partial")
        )

    def _claim_decision_rank(self, decision: EvidenceDecision | None) -> int:
        if decision is None:
            return 1
        if decision.decision == "accept" and decision.support_level == "direct":
            return 5
        if decision.decision == "accept" and decision.support_level == "partial":
            return 4
        if decision.decision == "maybe" and decision.support_level == "partial":
            return 3
        if decision.decision == "accept" and decision.support_level == "background":
            return 2
        return 0

    def _claim_decision_boost(self, decision: EvidenceDecision | None) -> float:
        return float(self._claim_decision_rank(decision) * 10)

    def _claim_sentences(self, text: str) -> list[str]:
        compact = re.sub(r"\s+", " ", text).strip()
        if not compact:
            return []
        sentences = [
            sentence.strip(" -")
            for sentence in re.split(r"(?<=[.!?。！？])\s+|\n+", compact)
            if sentence.strip(" -")
        ]
        if not sentences:
            sentences = [compact]
        passages: list[str] = []
        for sentence in sentences:
            if len(sentence) <= 360:
                passages.append(sentence)
                continue
            parts = [part.strip(" -") for part in re.split(r";\s+|,\s+(?=[A-Z])", sentence) if part.strip(" -")]
            passages.extend(part for part in parts if part)
        return passages or [compact[:360]]

    def _claim_terms(self, question: str) -> set[str]:
        stopwords = {
            "what",
            "which",
            "when",
            "where",
            "were",
            "with",
            "that",
            "this",
            "they",
            "does",
            "did",
            "the",
            "and",
            "are",
            "for",
            "how",
            "why",
            "paper",
            "method",
        }
        return {
            term.lower()
            for term in re.findall(r"[A-Za-z][A-Za-z0-9_.-]{2,}|\d+(?:\.\d+)?%?", question)
            if term.lower() not in stopwords
        }

    def _claim_text_score(self, sentence: str, question_terms: set[str]) -> float:
        normalized = sentence.lower()
        if not question_terms:
            return 1.0
        hits = sum(1 for term in question_terms if term in normalized)
        return round(hits / max(1, len(question_terms)), 4)

    def _claim_question_intents(self, question: str) -> set[str]:
        normalized = question.lower()
        intents: set[str] = set()
        if re.search(r"\b(dataset|datasets|data|corpus|corpora|benchmark|benchmarks|language pairs?)\b", normalized):
            intents.add("dataset")
        if re.search(r"\b(model|models|method|methods|approach|approaches|architecture|module|use|uses|used|propose|build|match|reorder|reordering)\b", normalized):
            intents.add("method")
        if re.search(r"\b(result|results|performance|metric|accuracy|f1|bleu|score|scores|outperform)\b", normalized):
            intents.add("result")
        if re.search(r"\b(how many|number|count|counts|total)\b", normalized):
            intents.add("count")
        if re.search(r"\b(compar|difference|differ|unlike|whereas|better|worse|versus|vs\.?)\b", normalized):
            intents.add("comparison")
        return intents

    def _claim_intent_boosts(self, sentence: str, intents: set[str]) -> dict[str, float]:
        if not intents:
            return {}
        normalized = sentence.lower()
        boosts: dict[str, float] = {}
        if "dataset" in intents:
            dataset_hits = 0
            if re.search(r"\b(dataset|datasets|corpus|corpora|benchmark|benchmarks|data|train|training|test|dev|task)\b", normalized):
                dataset_hits += 1
            if re.search(r"\b[A-Z][A-Za-z]*(?:-[A-Z][A-Za-z]*)+\b|\b[A-Z][A-Za-z]{2,}[A-Z][A-Za-z]*\b|\b[A-Z][a-z]?\s*[-\u2192]\s*[A-Z][a-z]?\b", sentence):
                dataset_hits += 1
            if re.search(r"\b(arabic|english|spanish|russian|french|german|romanian|hindi|bengali|gujarati|marathi|malayalam|tamil)\b", normalized):
                dataset_hits += 1
            if dataset_hits:
                boosts["dataset"] = min(0.45, 0.2 * dataset_hits)
        if "method" in intents:
            method_hits = 0
            if re.search(r"\b(model|method|approach|use|uses|used|propose|architecture|module|system|pre-?order|reorder|reordering|match)\b", normalized):
                method_hits += 1
            if re.search(r"\b(algorithm|classifier|baseline|rule|rules|configuration|framework)\b", normalized):
                method_hits += 1
            if method_hits:
                boosts["method"] = min(0.35, 0.18 * method_hits)
        if "result" in intents:
            result_hits = 0
            if re.search(r"\b(accuracy|f1|bleu|score|scores|metric|performance|outperform|result|results)\b", normalized):
                result_hits += 1
            if re.search(r"\b\d+(?:\.\d+)?%?\b", normalized):
                result_hits += 1
            if result_hits:
                boosts["result"] = min(0.4, 0.2 * result_hits)
        if "count" in intents and re.search(r"\b\d+(?:,\d{3})*(?:\.\d+)?%?\b|\b(one|two|three|four|five|six|seven|eight|nine|ten)\b", normalized):
            boosts["count"] = 0.3
        if "comparison" in intents and re.search(r"\b(compare|compared|differ|unlike|whereas|better|worse|versus|vs\.?|outperform|than)\b", normalized):
            boosts["comparison"] = 0.3
        return boosts

    def _normalize_claim_sentence(self, sentence: str) -> str:
        return re.sub(r"\W+", " ", sentence).strip().lower()

    def _is_near_duplicate_claim(self, normalized: str, seen: list[str]) -> bool:
        if not normalized:
            return True
        terms = set(normalized.split())
        if not terms:
            return True
        for other in seen:
            other_terms = set(other.split())
            if not other_terms:
                continue
            overlap = len(terms.intersection(other_terms)) / max(1, min(len(terms), len(other_terms)))
            if overlap >= 0.88:
                return True
        return False

    def _dedupe_preserve_order(self, values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            if value and value not in seen:
                result.append(value)
                seen.add(value)
        return result

    def _fallback_summary(self, filename: str, chunks: list[RetrievedChunk]) -> dict[str, Any]:
        content_chunks = self._summary_content_chunks(chunks)
        if not content_chunks:
            return self._empty_summary(filename)

        summary: dict[str, Any] = {"filename": filename}
        field_chunks: dict[str, RetrievedChunk | None] = {}
        for field in SUMMARY_FIELDS:
            chunk = self._best_summary_chunk(content_chunks, field)
            field_chunks[field] = chunk
            summary[field] = self._field_excerpt(field, chunk) if chunk else NOT_FOUND

        citations = []
        for field in SUMMARY_FIELDS:
            chunk = field_chunks.get(field)
            value = str(summary.get(field) or "")
            if not chunk or value == NOT_FOUND:
                continue
            citations.append(
                {
                    "field": field,
                    "quote": self._truncate(value, 300),
                    "chunk_index": content_chunks.index(chunk) + 1,
                }
            )
        summary["citations"] = citations[:6]
        return summary

    def _empty_summary(self, filename: str) -> dict[str, Any]:
        return {
            "filename": filename,
            "research_question": "未在原文中找到",
            "method": "未在原文中找到",
            "dataset_or_materials": "未在原文中找到",
            "experiment_setup": "未在原文中找到",
            "key_findings": "未在原文中找到",
            "limitations": "未在原文中找到",
            "future_work": "未在原文中找到",
            "citations": [],
        }

    def _format_history(self, messages: list[dict[str, str]], max_messages: int = 10, max_chars: int = 600) -> str:
        lines = []
        for message in messages[-max_messages:]:
            role = message.get("role", "")
            content = self._truncate(message.get("content", ""), max_chars)
            if role and content:
                lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _valid_citation_ids(self, answer: str, allowed_ids: set[str]) -> list[str]:
        ids = re.findall(r"\[(C\d+)\]", answer)
        result: list[str] = []
        for citation_id in ids:
            if citation_id in allowed_ids and citation_id not in result:
                result.append(citation_id)
        return result

    def _fallback_paper_chat_query_rewrite(
        self,
        question: str,
        memory_summary: str,
        history: list[dict[str, str]],
        paper_title: str,
    ) -> str:
        source = " ".join(
            [paper_title, memory_summary, *[message.get("content", "") for message in history[-6:]]]
        )
        terms = re.findall(r"[A-Z][A-Za-z0-9_.-]{1,}|[A-Za-z][A-Za-z0-9_.-]{3,}|\d+(?:\.\d+)?%?|[\u4e00-\u9fff]{2,}", source)
        stopwords = {
            "this",
            "that",
            "what",
            "which",
            "with",
            "from",
            "paper",
            "method",
            "result",
            "results",
            "question",
            "answer",
            "assistant",
            "user",
        }
        selected: list[str] = []
        seen: set[str] = set()
        for term in terms:
            normalized = term.lower()
            if normalized in stopwords or normalized in seen:
                continue
            selected.append(term)
            seen.add(normalized)
            if len(selected) >= 8:
                break
        if not selected:
            return question
        return self._truncate(f"{question} {' '.join(selected)}", 500)

    def _fallback_memory_summary(self, messages: list[dict[str, str]], previous_summary: str) -> str:
        latest = " ".join(message.get("content", "") for message in messages[-4:])
        latest = re.sub(r"\s+", " ", latest).strip()
        if len(latest) > 220:
            latest = latest[:220].rsplit(" ", 1)[0] + "..."
        if previous_summary and latest:
            return self._truncate(f"{previous_summary}; recent discussion: {latest}", 420)
        return latest or previous_summary

    def _citation_from_chunk(self, chunk: RetrievedChunk, citation_id: str | None = None) -> dict[str, Any]:
        quote = chunk.text.strip().replace("\n", " ")
        if len(quote) > 360:
            quote = quote[:360] + "..."
        return {
            "citation_id": citation_id,
            "paper_id": chunk.paper_id,
            "filename": chunk.filename,
            "chunk_id": chunk.chunk_id,
            "section_title": chunk.section_title,
            "section_path": chunk.section_path,
            "section_type": chunk.section_type,
            "quote": quote,
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
        }
