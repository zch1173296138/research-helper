from __future__ import annotations

import json
from typing import Any, Protocol

from openai import OpenAIError

from backend.app.evaluation.types import EvaluationCase, StrategyOutput
from backend.app.services.llm import LLMService


class AnswerJudge(Protocol):
    source: str

    def judge(self, case: EvaluationCase, output: StrategyOutput) -> dict[str, Any]:
        ...


class LlmAnswerJudge:
    source = "llm-as-judge"

    def __init__(self, llm: LLMService):
        self.llm = llm

    def judge(self, case: EvaluationCase, output: StrategyOutput) -> dict[str, Any]:
        if output.error:
            return {"source": self.source, "skipped": True, "reason": "strategy_error"}
        if self.llm.client is None:
            return {"source": self.source, "skipped": True, "reason": "llm_client_unavailable"}

        prompt = {
            "question": case.question,
            "should_answer": case.should_answer,
            "expected_points": case.expected_points,
            "supporting_quotes": case.supporting_quotes,
            "answer": output.answer,
            "citations": output.citations,
            "instruction": (
                "Grade the answer for correctness and grounding. Return JSON only with keys "
                "correctness, groundedness, should_answer_behavior, and notes. Scores must be 0 to 1."
            ),
        }
        try:
            response = self.llm._call_with_deadline(
                lambda: self.llm.client.chat.completions.create(
                    model=self.llm.settings.chat_model,
                    messages=[
                        {"role": "system", "content": "You are a strict RAG evaluation judge. Return valid JSON only."},
                        {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                    ],
                    temperature=0.0,
                    extra_body=self.llm._completion_extra_body(),
                )
            )
            content = response.choices[0].message.content or "{}"
            payload = json.loads(self.llm._extract_json(content))
            return {"source": self.source, "skipped": False, "result": payload}
        except (OpenAIError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            return {"source": self.source, "skipped": True, "reason": str(exc)}


def make_answer_judge(enabled: bool, llm: LLMService) -> AnswerJudge | None:
    if not enabled:
        return None
    return LlmAnswerJudge(llm)
