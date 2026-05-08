import json
import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Any
from typing import TypeVar

from openai import OpenAI
from openai import OpenAIError

from backend.app.core.config import Settings
from backend.app.services.vector_store import RetrievedChunk


MISSING = "未在已导入文献中找到依据。"
NOT_FOUND = "未在原文中找到"
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

    def summarize_paper(self, filename: str, chunks: list[RetrievedChunk]) -> dict[str, Any]:
        if not chunks:
            return self._empty_summary(filename)
        if self.client is None:
            return self._fallback_summary(filename, chunks)

        selected_chunks = self._select_summary_chunks(chunks)
        context = "\n\n".join(
            (
                f"[{idx}] chunk_id={chunk.chunk_id}; section={chunk.section_title or 'unknown'}; "
                f"pages={chunk.page_start or '?'}-{chunk.page_end or '?'}\n{self._truncate(chunk.text, 1400)}"
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
            return self._fallback_summary(filename, selected_chunks)
        try:
            return self._normalize_summary(json.loads(self._extract_json(content)), filename)
        except json.JSONDecodeError:
            return self._fallback_summary(filename, selected_chunks)

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
        keyword_groups = [
            ("abstract", "摘要"),
            ("introduction", "background", "problem", "motivation"),
            ("method", "approach", "architecture", "model", "algorithm"),
            ("dataset", "data", "material", "benchmark"),
            ("experiment", "evaluation", "setup", "implementation"),
            ("result", "finding", "analysis", "performance"),
            ("discussion", "limitation", "future", "conclusion"),
        ]
        selected: list[RetrievedChunk] = []

        def add(chunk: RetrievedChunk) -> None:
            if chunk.chunk_id not in {item.chunk_id for item in selected}:
                selected.append(chunk)

        for chunk in chunks[:3]:
            add(chunk)

        for group in keyword_groups:
            for chunk in chunks:
                haystack = f"{chunk.section_title}\n{chunk.text[:500]}".lower()
                if any(keyword in haystack for keyword in group):
                    add(chunk)
                    break

        for chunk in chunks:
            if len(selected) >= max_chunks:
                break
            add(chunk)

        return selected[:max_chunks]

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
        for key in (
            "research_question",
            "method",
            "dataset_or_materials",
            "experiment_setup",
            "key_findings",
            "limitations",
            "future_work",
        ):
            value = normalized.get(key)
            normalized[key] = str(value).strip() if value else NOT_FOUND
        citations = normalized.get("citations")
        normalized["citations"] = citations if isinstance(citations, list) else []
        return normalized

    def _truncate(self, text: str, max_chars: int) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        if len(compact) <= max_chars:
            return compact
        return compact[:max_chars].rsplit(" ", 1)[0] + "..."

    def _extractive_answer(self, question: str, chunks: list[RetrievedChunk]) -> str:
        first = chunks[0]
        excerpt = first.text.strip().replace("\n", " ")
        if len(excerpt) > 700:
            excerpt = excerpt[:700].rsplit(" ", 1)[0] + "..."
        return f"根据已导入文献中最相关的片段，问题“{question}”可从以下证据开始分析：{excerpt}"

    def _fallback_summary(self, filename: str, chunks: list[RetrievedChunk]) -> dict[str, Any]:
        joined = "\n".join(chunk.text for chunk in chunks[:3])
        excerpt = joined.strip().replace("\n", " ")
        if len(excerpt) > 900:
            excerpt = excerpt[:900] + "..."
        quote = chunks[0].text[:300] if chunks else ""
        return {
            "research_question": excerpt or "未在原文中找到",
            "method": "未在原文中找到",
            "dataset_or_materials": "未在原文中找到",
            "experiment_setup": "未在原文中找到",
            "key_findings": excerpt or "未在原文中找到",
            "limitations": "未在原文中找到",
            "future_work": "未在原文中找到",
            "citations": [{"field": "key_findings", "quote": quote, "chunk_index": 0}],
            "filename": filename,
        }

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

    def _citation_from_chunk(self, chunk: RetrievedChunk) -> dict[str, Any]:
        quote = chunk.text.strip().replace("\n", " ")
        if len(quote) > 360:
            quote = quote[:360] + "..."
        return {
            "paper_id": chunk.paper_id,
            "filename": chunk.filename,
            "chunk_id": chunk.chunk_id,
            "section_title": chunk.section_title,
            "quote": quote,
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
        }
