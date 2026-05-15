import time
from types import SimpleNamespace

from backend.app.core.config import Settings
from backend.app.services.evidence_types import EvidenceDecision
from backend.app.services.llm import LLMService
from backend.app.services.vector_store import RetrievedChunk


def test_answer_without_evidence_refuses() -> None:
    service = LLMService(Settings(openai_api_key=""))
    result = service.answer_with_citations("What is the method?", [])
    assert result["missing_evidence"] is True
    assert "未在已导入文献中找到依据" in result["answer"]


def test_default_citation_selection_mode_is_precision() -> None:
    assert Settings(openai_api_key="").rag_citation_selection_mode == "precision"


def test_summarize_falls_back_when_llm_times_out() -> None:
    class SlowCompletions:
        def create(self, **_: object) -> object:
            time.sleep(2)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))])

    service = LLMService(Settings(openai_api_key="test-key", llm_timeout_seconds=1))
    service.client = SimpleNamespace(chat=SimpleNamespace(completions=SlowCompletions()))
    chunks = [
        RetrievedChunk(
            chunk_id="chunk-1",
            paper_id="paper-1",
            filename="paper.pdf",
            section_title="Abstract",
            text="This paper studies networked sensors and TinyOS.",
        )
    ]

    started = time.monotonic()
    summary = service.summarize_paper("paper.pdf", chunks)

    assert time.monotonic() - started < 1.8
    assert summary["filename"] == "paper.pdf"
    assert "networked sensors" in summary["research_question"]


def test_summarize_fallback_skips_front_matter_authors() -> None:
    service = LLMService(Settings(openai_api_key=""))
    chunks = [
        RetrievedChunk(
            chunk_id="chunk-0",
            paper_id="paper-1",
            filename="2504.07378v3 (1).pdf",
            section_title="BRepFormer: Transformer-Based B-rep Geometric Feature Recognition",
            text=(
                "# BRepFormer: Transformer-Based B-rep Geometric Feature Recognition\n\n"
                "Yongkang Dai\nSchool of Software,\nNorthwestern Polytechnical University\n"
                "daiyongkang@mail.nwpu.edu.cn\nHao Guo\nSchool of Software,\n"
                "Northwestern Polytechnical University\nguoh0215@mail.nwpu.edu.cn"
            ),
        ),
        RetrievedChunk(
            chunk_id="chunk-1",
            paper_id="paper-1",
            filename="2504.07378v3 (1).pdf",
            section_title="Abstract",
            section_type="abstract",
            text=(
                "# Abstract\nRecognizing geometric features on B-rep models is a cornerstone technique for "
                "multimedia content-based retrieval and intelligent manufacturing. However, previous research "
                "often merely focused on Machining Feature Recognition, falling short in effectively capturing "
                "the intricate topological and geometric characteristics of complex geometry features. In this "
                "paper, we propose BRepFormer, a novel transformer-based model to recognize both machining "
                "feature and complex CAD models' features."
            ),
        ),
        RetrievedChunk(
            chunk_id="chunk-2",
            paper_id="paper-1",
            filename="2504.07378v3 (1).pdf",
            section_title="Method",
            section_type="method",
            text=(
                "We propose a novel approach for CAD geometric feature recognition based on a transformer "
                "architecture, consisting of a feature extractor, feature encoder, transformer block, and "
                "recognition head."
            ),
        ),
        RetrievedChunk(
            chunk_id="chunk-3",
            paper_id="paper-1",
            filename="2504.07378v3 (1).pdf",
            section_title="Experimental Datasets",
            section_type="experiment",
            text=(
                "We evaluated our model on the MFInstSeg and MFTRCAD public datasets and on the proposed CBF "
                "dataset. For all datasets, we used a 70% / 15% / 15% split for training, validation, and testing."
            ),
        ),
        RetrievedChunk(
            chunk_id="chunk-4",
            paper_id="paper-1",
            filename="2504.07378v3 (1).pdf",
            section_title="Results",
            section_type="results",
            text=(
                "The experimental results demonstrate that BRepFormer achieves state-of-the-art accuracy on the "
                "MFInstSeg, MFTRCAD, and CBF datasets. Although the network outperforms other comparative "
                "networks in overall accuracy, it performs poorly in the mIoU metric on the CBF dataset."
            ),
        ),
    ]

    summary = service.summarize_paper("2504.07378v3 (1).pdf", chunks)

    assert "Yongkang Dai" not in summary["research_question"]
    assert "daiyongkang" not in summary["key_findings"]
    assert "previous research" in summary["research_question"]
    assert "transformer" in summary["method"].lower()
    assert "MFInstSeg" in summary["dataset_or_materials"]
    assert "70%" in summary["experiment_setup"]
    assert "mIoU" in summary["limitations"]


def test_summarize_repairs_model_author_metadata_with_local_evidence() -> None:
    class BadSummaryCompletions:
        def create(self, **_: object) -> object:
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content=(
                                '{"research_question":"Yongkang Dai School of Software Northwestern '
                                'Polytechnical University daiyongkang@mail.nwpu.edu.cn Hao Guo School of '
                                'Software Northwestern Polytechnical University guoh0215@mail.nwpu.edu.cn",'
                                '"method":"未在原文中找到","key_findings":"未在原文中找到"}'
                            )
                        )
                    )
                ]
            )

    service = LLMService(Settings(openai_api_key="test-key", llm_timeout_seconds=1))
    service.client = SimpleNamespace(chat=SimpleNamespace(completions=BadSummaryCompletions()))
    chunks = [
        RetrievedChunk(
            chunk_id="chunk-0",
            paper_id="paper-1",
            filename="paper.pdf",
            section_title="Title",
            text="Yongkang Dai School of Software Northwestern Polytechnical University daiyongkang@mail.nwpu.edu.cn",
        ),
        RetrievedChunk(
            chunk_id="chunk-1",
            paper_id="paper-1",
            filename="paper.pdf",
            section_title="Abstract",
            section_type="abstract",
            text=(
                "However, previous research falls short in capturing complex geometry features. "
                "In this paper, we propose BRepFormer, a transformer-based model for B-rep feature recognition. "
                "The experimental results demonstrate state-of-the-art accuracy on benchmark datasets."
            ),
        ),
    ]

    summary = service.summarize_paper("paper.pdf", chunks)

    assert "Yongkang Dai" not in summary["research_question"]
    assert "previous research" in summary["research_question"]
    assert "transformer-based" in summary["method"]
    assert "state-of-the-art" in summary["key_findings"]


def test_paper_chat_fallback_forces_citation() -> None:
    service = LLMService(Settings(openai_api_key=""))
    chunks = [
        RetrievedChunk(
            chunk_id="chunk-1",
            paper_id="paper-1",
            filename="paper.pdf",
            section_title="Method",
            section_type="method",
            text="The method has three scheduling stages.",
        )
    ]

    result = service.answer_paper_chat("What is the method?", chunks)

    assert "[C1]" in result["answer"]
    assert result["citations"][0]["citation_id"] == "C1"
    assert result["missing_evidence"] is False


def test_evidence_answer_fallback_returns_top_three_citations() -> None:
    service = LLMService(Settings(openai_api_key="", rag_citation_selection_mode="current"))
    chunks = [
        RetrievedChunk(
            chunk_id=f"chunk-{index}",
            paper_id="paper-1",
            filename="paper.pdf",
            section_title="Method",
            section_type="method",
            text=f"Evidence sentence {index}.",
        )
        for index in range(1, 5)
    ]
    decisions = [EvidenceDecision(chunk.chunk_id, "accept", support_level="partial") for chunk in chunks]

    result = service.answer_with_evidence("What is the method?", chunks, decisions)

    assert "[C1]" in result["answer"]
    assert "[C2]" in result["answer"]
    assert "[C3]" in result["answer"]
    assert [citation["citation_id"] for citation in result["citations"]] == ["C1", "C2", "C3"]
    assert result["answer_source_chunk_ids"] == ["chunk-1", "chunk-2", "chunk-3"]
    assert result["claim_count"] == 3


def test_evidence_answer_strict_mode_uses_only_explicit_citations() -> None:
    class CitedAnswerCompletions:
        def create(self, **_: object) -> object:
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="The answer cites one chunk. [C4]"))])

    service = LLMService(Settings(openai_api_key="test-key", llm_timeout_seconds=1, rag_citation_selection_mode="strict"))
    service.client = SimpleNamespace(chat=SimpleNamespace(completions=CitedAnswerCompletions()))
    chunks = [
        RetrievedChunk(f"chunk-{index}", "paper-1", "paper.pdf", "Method", f"Evidence {index}.")
        for index in range(1, 5)
    ]
    decisions = [
        EvidenceDecision("chunk-1", "accept", support_level="direct"),
        EvidenceDecision("chunk-2", "accept", support_level="partial"),
        EvidenceDecision("chunk-3", "accept", support_level="background"),
        EvidenceDecision("chunk-4", "accept", support_level="background"),
    ]

    result = service.answer_with_evidence("What is the method?", chunks, decisions)

    assert result["answer"] == "The answer cites one chunk. [C4]"
    assert [citation["citation_id"] for citation in result["citations"]] == ["C4"]


def test_evidence_answer_strict_mode_without_used_citation_returns_single_fallback() -> None:
    class UncitedAnswerCompletions:
        def create(self, **_: object) -> object:
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="The answer has no citation."))])

    service = LLMService(Settings(openai_api_key="test-key", llm_timeout_seconds=1, rag_citation_selection_mode="strict"))
    service.client = SimpleNamespace(chat=SimpleNamespace(completions=UncitedAnswerCompletions()))
    chunks = [
        RetrievedChunk("chunk-background", "paper-1", "paper.pdf", "Background", "Background evidence."),
        RetrievedChunk("chunk-direct", "paper-1", "paper.pdf", "Method", "Direct evidence."),
    ]
    decisions = [
        EvidenceDecision("chunk-background", "accept", support_level="background"),
        EvidenceDecision("chunk-direct", "accept", support_level="direct"),
    ]

    result = service.answer_with_evidence("What is the method?", chunks, decisions)

    assert "[C2]" in result["answer"]
    assert [citation["citation_id"] for citation in result["citations"]] == ["C2"]


def test_evidence_answer_answer_linked_mode_uses_extractive_source_only() -> None:
    service = LLMService(Settings(openai_api_key="", rag_citation_selection_mode="answer_linked"))
    chunks = [
        RetrievedChunk(f"chunk-{index}", "paper-1", "paper.pdf", "Method", f"Evidence {index}.")
        for index in range(1, 5)
    ]
    decisions = [EvidenceDecision(chunk.chunk_id, "accept", support_level="partial") for chunk in chunks]

    result = service.answer_with_evidence("What is the method?", chunks, decisions)

    assert "[C1]" in result["answer"]
    assert "[C2]" in result["answer"]
    assert [citation["citation_id"] for citation in result["citations"]] == ["C1", "C2", "C3"]


def test_claim_extraction_uses_two_accepted_direct_chunks() -> None:
    service = LLMService(Settings(openai_api_key="", rag_citation_selection_mode="answer_linked"))
    chunks = [
        RetrievedChunk("chunk-1", "paper-1", "paper.pdf", "Method", "The model uses graph encoding for entities."),
        RetrievedChunk("chunk-2", "paper-1", "paper.pdf", "Method", "The model uses transformer decoding for relations."),
    ]
    decisions = [
        EvidenceDecision("chunk-1", "accept", support_level="direct"),
        EvidenceDecision("chunk-2", "accept", support_level="direct"),
    ]

    result = service.answer_with_evidence("What model do they use?", chunks, decisions)

    assert result["answer_source_chunk_ids"] == ["chunk-1", "chunk-2"]
    assert [claim["citation_id"] for claim in result["answer_claims"]] == ["C1", "C2"]
    assert "[C1]" in result["answer"]
    assert "[C2]" in result["answer"]
    assert [citation["citation_id"] for citation in result["citations"]] == ["C1", "C2"]


def test_claim_extraction_accept_direct_beats_accept_background() -> None:
    service = LLMService(Settings(openai_api_key=""))
    chunks = [
        RetrievedChunk("chunk-background", "paper-1", "paper.pdf", "Background", "The model background uses graph features."),
        RetrievedChunk("chunk-direct", "paper-1", "paper.pdf", "Method", "The model directly uses graph neural networks."),
    ]
    decisions = [
        EvidenceDecision("chunk-background", "accept", support_level="background"),
        EvidenceDecision("chunk-direct", "accept", support_level="direct"),
    ]

    result = service._extractive_answer_with_claim_sources("What model uses graph?", chunks, decisions, max_claims=1)

    assert result["answer_source_chunk_ids"] == ["chunk-direct"]
    assert result["claims"][0]["citation_id"] == "C2"


def test_claim_extraction_ignores_reject_direct() -> None:
    service = LLMService(Settings(openai_api_key=""))
    chunks = [
        RetrievedChunk("chunk-reject", "paper-1", "paper.pdf", "Method", "The model uses rejected graph evidence."),
        RetrievedChunk("chunk-direct", "paper-1", "paper.pdf", "Method", "The model uses accepted graph evidence."),
    ]
    decisions = [
        EvidenceDecision("chunk-reject", "reject", support_level="direct"),
        EvidenceDecision("chunk-direct", "accept", support_level="direct"),
    ]

    result = service._extractive_answer_with_claim_sources("What model uses graph?", chunks, decisions, max_claims=2)

    assert result["answer_source_chunk_ids"] == ["chunk-direct"]
    assert [claim["citation_id"] for claim in result["claims"]] == ["C2"]


def test_claim_extraction_uses_maybe_partial_when_needed() -> None:
    service = LLMService(Settings(openai_api_key=""))
    chunks = [
        RetrievedChunk("chunk-direct", "paper-1", "paper.pdf", "Method", "The model uses direct graph evidence."),
        RetrievedChunk("chunk-maybe", "paper-1", "paper.pdf", "Method", "The model uses partial graph evidence."),
    ]
    decisions = [
        EvidenceDecision("chunk-direct", "accept", support_level="direct"),
        EvidenceDecision("chunk-maybe", "maybe", support_level="partial"),
    ]

    result = service._extractive_answer_with_claim_sources("What model uses graph?", chunks, decisions, max_claims=2)

    assert result["answer_source_chunk_ids"] == ["chunk-direct", "chunk-maybe"]
    assert [claim["citation_id"] for claim in result["claims"]] == ["C1", "C2"]


def test_claim_extraction_dedupes_duplicate_sentences() -> None:
    service = LLMService(Settings(openai_api_key=""))
    chunks = [
        RetrievedChunk("chunk-1", "paper-1", "paper.pdf", "Method", "The model uses graph evidence."),
        RetrievedChunk("chunk-2", "paper-1", "paper.pdf", "Method", "The model uses graph evidence."),
    ]
    decisions = [
        EvidenceDecision("chunk-1", "accept", support_level="direct"),
        EvidenceDecision("chunk-2", "accept", support_level="direct"),
    ]

    result = service._extractive_answer_with_claim_sources("What model uses graph?", chunks, decisions, max_claims=3)

    assert result["answer_source_chunk_ids"] == ["chunk-1"]
    assert len(result["claims"]) == 1


def test_claim_extraction_result_intent_boosts_numeric_metric_sentence() -> None:
    service = LLMService(Settings(openai_api_key=""))
    chunks = [
        RetrievedChunk("chunk-method", "paper-1", "paper.pdf", "Method", "BERT uses a transformer encoder for the task."),
        RetrievedChunk("chunk-result", "paper-1", "paper.pdf", "Results", "BERT obtains an F1 score of 0.97 on the task."),
    ]
    decisions = [EvidenceDecision(chunk.chunk_id, "accept", support_level="partial") for chunk in chunks]

    result = service._extractive_answer_with_claim_sources("What is the performance of BERT on the task?", chunks, decisions, max_claims=1)

    assert result["answer_source_chunk_ids"] == ["chunk-result"]
    assert result["claims"][0]["intent_boosts"]["result"] > 0


def test_claim_extraction_dataset_intent_boosts_corpus_sentence() -> None:
    service = LLMService(Settings(openai_api_key=""))
    chunks = [
        RetrievedChunk("chunk-method", "paper-1", "paper.pdf", "Method", "The model uses multilingual pre-training."),
        RetrievedChunk("chunk-data", "paper-1", "paper.pdf", "Data", "We evaluate on the Europarl corpus and MultiUN benchmark data."),
    ]
    decisions = [EvidenceDecision(chunk.chunk_id, "accept", support_level="partial") for chunk in chunks]

    result = service._extractive_answer_with_claim_sources("Which datasets do they experiment with?", chunks, decisions, max_claims=1)

    assert result["answer_source_chunk_ids"] == ["chunk-data"]
    assert result["claims"][0]["intent_boosts"]["dataset"] > 0


def test_claim_extraction_method_intent_boosts_model_sentence() -> None:
    service = LLMService(Settings(openai_api_key=""))
    chunks = [
        RetrievedChunk("chunk-result", "paper-1", "paper.pdf", "Results", "The results improve by 2 BLEU points."),
        RetrievedChunk("chunk-method", "paper-1", "paper.pdf", "Method", "The method uses a graph neural model architecture."),
    ]
    decisions = [EvidenceDecision(chunk.chunk_id, "accept", support_level="partial") for chunk in chunks]

    result = service._extractive_answer_with_claim_sources("What method do they use?", chunks, decisions, max_claims=1)

    assert result["answer_source_chunk_ids"] == ["chunk-method"]
    assert result["claims"][0]["intent_boosts"]["method"] > 0


def test_claim_extraction_reserve_slot_keeps_distinct_high_confidence_claim() -> None:
    service = LLMService(Settings(openai_api_key=""))
    chunks = [
        RetrievedChunk("chunk-1", "paper-1", "paper.pdf", "Method", "The model uses graph evidence for the method."),
        RetrievedChunk("chunk-2", "paper-1", "paper.pdf", "Method", "The model uses transformer evidence for the method."),
        RetrievedChunk("chunk-3", "paper-1", "paper.pdf", "Method", "The model uses encoder evidence for the method."),
        RetrievedChunk("chunk-4", "paper-1", "paper.pdf", "Method", "The method uses alignment evidence and reports corpus details."),
    ]
    decisions = [EvidenceDecision(chunk.chunk_id, "accept", support_level="direct") for chunk in chunks]

    result = service._extractive_answer_with_claim_sources("What method uses evidence and corpus?", chunks, decisions, max_claims=3)

    assert len(result["claims"]) == 3
    assert "chunk-4" in result["answer_source_chunk_ids"]
    assert [claim for claim in result["claims"] if claim["chunk_id"] == "chunk-4"][0]["selected_by"] in {"reserve_slot", "top_score"}


def test_claim_extraction_near_duplicate_reserve_candidate_is_not_selected() -> None:
    service = LLMService(Settings(openai_api_key=""))
    chunks = [
        RetrievedChunk("chunk-1", "paper-1", "paper.pdf", "Method", "The model uses graph evidence for the method."),
        RetrievedChunk("chunk-2", "paper-1", "paper.pdf", "Method", "The model uses transformer evidence for the method."),
        RetrievedChunk("chunk-3", "paper-1", "paper.pdf", "Method", "The model uses encoder evidence for the method."),
        RetrievedChunk("chunk-dup", "paper-1", "paper.pdf", "Method", "The model uses graph evidence for the method."),
    ]
    decisions = [EvidenceDecision(chunk.chunk_id, "accept", support_level="direct") for chunk in chunks]

    result = service._extractive_answer_with_claim_sources("What model method uses evidence?", chunks, decisions, max_claims=3)

    assert len(result["claims"]) == 3
    assert "chunk-dup" not in result["answer_source_chunk_ids"]


def test_claim_extraction_max_claims_remains_three() -> None:
    service = LLMService(Settings(openai_api_key=""))
    chunks = [
        RetrievedChunk(f"chunk-{index}", "paper-1", "paper.pdf", "Method", f"The method uses evidence item {index}.")
        for index in range(1, 6)
    ]
    decisions = [EvidenceDecision(chunk.chunk_id, "accept", support_level="direct") for chunk in chunks]

    result = service._extractive_answer_with_claim_sources("What method uses evidence?", chunks, decisions, max_claims=3)

    assert len(result["claims"]) == 3
    assert len(result["answer_source_chunk_ids"]) == 3


def test_precision_mode_uses_only_high_confidence_claim_sources() -> None:
    service = LLMService(Settings(openai_api_key="", rag_citation_selection_mode="precision"))
    chunks = [
        RetrievedChunk("chunk-direct", "paper-1", "paper.pdf", "Method", "The model uses direct graph evidence."),
        RetrievedChunk("chunk-maybe", "paper-1", "paper.pdf", "Method", "The model uses partial graph evidence."),
    ]
    decisions = [
        EvidenceDecision("chunk-direct", "accept", support_level="direct"),
        EvidenceDecision("chunk-maybe", "maybe", support_level="partial"),
    ]

    result = service.answer_with_evidence("What model uses graph?", chunks, decisions)

    assert result["answer_source_chunk_ids"] == ["chunk-direct", "chunk-maybe"]
    assert [claim["citation_id"] for claim in result["answer_claims"]] == ["C1", "C2"]
    assert [citation["citation_id"] for citation in result["citations"]] == ["C1"]


def test_evidence_answer_precision_mode_allows_accept_direct_and_partial_only() -> None:
    service = LLMService(Settings(openai_api_key="", rag_citation_selection_mode="precision"))
    chunks = [
        RetrievedChunk("chunk-direct", "paper-1", "paper.pdf", "Method", "Direct evidence."),
        RetrievedChunk("chunk-partial", "paper-1", "paper.pdf", "Method", "Partial evidence."),
        RetrievedChunk("chunk-background", "paper-1", "paper.pdf", "Background", "Background evidence."),
        RetrievedChunk("chunk-maybe", "paper-1", "paper.pdf", "Method", "Maybe evidence."),
        RetrievedChunk("chunk-reject", "paper-1", "paper.pdf", "Method", "Rejected evidence."),
    ]
    citation_map = {f"C{index}": chunk for index, chunk in enumerate(chunks, start=1)}
    decisions = [
        EvidenceDecision("chunk-direct", "accept", support_level="direct"),
        EvidenceDecision("chunk-partial", "accept", support_level="partial"),
        EvidenceDecision("chunk-background", "accept", support_level="background"),
        EvidenceDecision("chunk-maybe", "maybe", support_level="direct"),
        EvidenceDecision("chunk-reject", "reject", support_level="direct"),
    ]

    selected = service._selected_evidence_citation_ids([], citation_map, decisions)

    assert selected == ["C1"]
    assert service._precision_evidence_citation_ids(["C1"], citation_map, decisions) == ["C1"]
    assert service._precision_evidence_citation_ids(["C2"], citation_map, decisions) == ["C2"]
    assert service._precision_evidence_citation_ids(["C3"], citation_map, decisions) == ["C1"]
    assert service._precision_evidence_citation_ids(["C4"], citation_map, decisions) == ["C1"]
    assert service._precision_evidence_citation_ids(["C5"], citation_map, decisions) == ["C1"]


def test_evidence_answer_precision_mode_does_not_use_arbitrary_fallback() -> None:
    service = LLMService(Settings(openai_api_key="", rag_citation_selection_mode="precision"))
    chunks = [
        RetrievedChunk("chunk-background", "paper-1", "paper.pdf", "Background", "Background evidence."),
        RetrievedChunk("chunk-maybe", "paper-1", "paper.pdf", "Method", "Maybe evidence."),
        RetrievedChunk("chunk-reject", "paper-1", "paper.pdf", "Method", "Rejected evidence."),
    ]
    citation_map = {f"C{index}": chunk for index, chunk in enumerate(chunks, start=1)}
    decisions = [
        EvidenceDecision("chunk-background", "accept", support_level="background"),
        EvidenceDecision("chunk-maybe", "maybe", support_level="direct"),
        EvidenceDecision("chunk-reject", "reject", support_level="direct"),
    ]

    selected = service._selected_evidence_citation_ids([], citation_map, decisions)

    assert selected == []


def test_evidence_answer_keeps_used_citations_and_adds_high_confidence_citations() -> None:
    class CitedAnswerCompletions:
        def create(self, **_: object) -> object:
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="The answer cites one chunk. [C4]"))])

    service = LLMService(Settings(openai_api_key="test-key", llm_timeout_seconds=1, rag_citation_selection_mode="current"))
    service.client = SimpleNamespace(chat=SimpleNamespace(completions=CitedAnswerCompletions()))
    chunks = [
        RetrievedChunk(f"chunk-{index}", "paper-1", "paper.pdf", "Method", f"Evidence {index}.")
        for index in range(1, 6)
    ]
    decisions = [
        EvidenceDecision("chunk-1", "accept", support_level="direct"),
        EvidenceDecision("chunk-2", "accept", support_level="partial"),
        EvidenceDecision("chunk-3", "accept", support_level="background"),
        EvidenceDecision("chunk-4", "accept", support_level="background"),
        EvidenceDecision("chunk-5", "reject", support_level="direct"),
    ]

    result = service.answer_with_evidence("What is the method?", chunks, decisions)

    assert result["answer"] == "The answer cites one chunk. [C4]"
    assert [citation["citation_id"] for citation in result["citations"]] == ["C4", "C1", "C2"]


def test_evidence_answer_uses_background_only_when_no_direct_or_partial() -> None:
    class CitedAnswerCompletions:
        def create(self, **_: object) -> object:
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Background-only answer. [C2]"))])

    service = LLMService(Settings(openai_api_key="test-key", llm_timeout_seconds=1, rag_citation_selection_mode="current"))
    service.client = SimpleNamespace(chat=SimpleNamespace(completions=CitedAnswerCompletions()))
    chunks = [
        RetrievedChunk("chunk-1", "paper-1", "paper.pdf", "Background", "Background evidence 1."),
        RetrievedChunk("chunk-2", "paper-1", "paper.pdf", "Background", "Background evidence 2."),
    ]
    decisions = [
        EvidenceDecision("chunk-1", "accept", support_level="background"),
        EvidenceDecision("chunk-2", "accept", support_level="background"),
    ]

    result = service.answer_with_evidence("What background is available?", chunks, decisions)

    assert result["answer"] == "Background-only answer. [C2]"
    assert [citation["citation_id"] for citation in result["citations"]] == ["C2", "C1"]


def test_evidence_answer_default_precision_uses_high_confidence_claim_citations() -> None:
    class UncitedAnswerCompletions:
        def create(self, **_: object) -> object:
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="The answer has no citation."))])

    service = LLMService(Settings(openai_api_key="test-key", llm_timeout_seconds=1))
    service.client = SimpleNamespace(chat=SimpleNamespace(completions=UncitedAnswerCompletions()))
    chunks = [
        RetrievedChunk("chunk-background", "paper-1", "paper.pdf", "Background", "Background evidence."),
        RetrievedChunk("chunk-direct", "paper-1", "paper.pdf", "Method", "Direct evidence."),
    ]
    decisions = [
        EvidenceDecision("chunk-background", "accept", support_level="background"),
        EvidenceDecision("chunk-direct", "accept", support_level="direct"),
    ]

    result = service.answer_with_evidence("What is the method?", chunks, decisions)

    assert "[C2]" in result["answer"]
    assert result["answer_source_chunk_ids"] == ["chunk-background", "chunk-direct"]
    assert [citation["citation_id"] for citation in result["citations"]] == ["C2"]


def test_paper_chat_invalid_model_citation_falls_back_to_valid_citation() -> None:
    class BadCompletions:
        def create(self, **_: object) -> object:
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="The answer is unsupported [C99]."))])

    service = LLMService(Settings(openai_api_key="test-key", llm_timeout_seconds=1))
    service.client = SimpleNamespace(chat=SimpleNamespace(completions=BadCompletions()))
    chunks = [
        RetrievedChunk(
            chunk_id="chunk-1",
            paper_id="paper-1",
            filename="paper.pdf",
            section_title="Results",
            section_type="results",
            text="The accuracy reaches 91 percent.",
        )
    ]

    result = service.answer_paper_chat("What is the result?", chunks)

    assert "[C1]" in result["answer"]
    assert all(citation["citation_id"] != "C99" for citation in result["citations"])


def test_paper_chat_builds_memory_before_recent_messages() -> None:
    service = LLMService(Settings(openai_api_key=""))
    chunk = RetrievedChunk(
        chunk_id="chunk-1",
        paper_id="paper-1",
        filename="paper.pdf",
        section_title="Method",
        text="The method has three scheduling stages.",
    )
    messages = service._build_paper_chat_messages(
        "What about it?",
        {"C1": chunk},
        [
            {"role": "user", "content": "Tell me about the scheduler."},
            {"role": "assistant", "content": "It has staged scheduling. [C1]"},
        ],
        "User cares about the scheduler details.",
    )

    assert messages[0]["role"] == "system"
    assert "not evidence" in messages[1]["content"]
    assert "scheduler details" in messages[1]["content"]
    assert messages[2]["role"] == "user"
    assert messages[3]["role"] == "assistant"
    assert messages[-1]["role"] == "user"
    assert "Evidence:" in messages[-1]["content"]


def test_paper_chat_prompt_requests_substantive_overview_answers() -> None:
    service = LLMService(Settings(openai_api_key=""))
    chunk = RetrievedChunk(
        chunk_id="chunk-1",
        paper_id="paper-1",
        filename="paper.pdf",
        section_title="Introduction",
        text="BRepFormer uses Transformer blocks for B-rep feature recognition.",
    )
    messages = service._build_paper_chat_messages("这篇文章讲了什么", {"C1": chunk}, [], "")

    system_prompt = messages[0]["content"]
    final_prompt = messages[-1]["content"]

    assert "substantive Chinese answer" in system_prompt
    assert "research problem" in system_prompt
    assert "experiments/results" in system_prompt
    assert "Do not answer in only one or two short sentences" in final_prompt


def test_paper_chat_rewrite_fallback_uses_memory_and_recent_terms() -> None:
    service = LLMService(Settings(openai_api_key=""))
    result = service.rewrite_paper_chat_query(
        "What about that metric?",
        memory_summary="The discussion focused on TinyBench accuracy.",
        history=[{"role": "user", "content": "TinyBench accuracy reached 91 percent."}],
        paper_title="TinyOS paper",
    )

    assert result["source"] == "fallback"
    assert "TinyBench" in result["query"]
    assert result["query"].startswith("What about that metric?")


def test_paper_chat_memory_is_not_citable_evidence() -> None:
    class MemoryCitationCompletions:
        def create(self, **_: object) -> object:
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Memory says it is 99 percent [C99]."))])

    service = LLMService(Settings(openai_api_key="test-key", llm_timeout_seconds=1))
    service.client = SimpleNamespace(chat=SimpleNamespace(completions=MemoryCitationCompletions()))
    chunks = [
        RetrievedChunk(
            chunk_id="chunk-1",
            paper_id="paper-1",
            filename="paper.pdf",
            section_title="Results",
            section_type="results",
            text="The reported accuracy is 91 percent.",
        )
    ]

    result = service.answer_paper_chat("What is the metric?", chunks, memory_summary="An old answer mentioned 99 percent.")

    assert "[C1]" in result["answer"]
    assert result["citations"][0]["chunk_id"] == "chunk-1"
    assert all(citation["citation_id"] != "C99" for citation in result["citations"])
