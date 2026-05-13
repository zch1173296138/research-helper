# RAG A/B Evaluation Report

## Run Configuration

- Cases: `evals\rag_ab\starter_cases.jsonl`
- Baseline: `baseline-current`
- Comparison: `current-evidence`
- Mode: `in-process`
- Current API URL: `n/a`
- Old-code API URL: `n/a`
- Deterministic local: `True`
- top_k: `8`
- Output directory: `evals/rag_ab/runs/latest`
- Case file sha256: `0c9375c8bcf3f4578b75ede5adff4d44cb530bcd0a6591dfbd97ae77ee77a51c`
- Timestamp: `2026-05-13T11:33:29.135874+00:00`
- Git revision: `db26bc4eeef2a94a3352edae3a0b79d8cb1891e1`
- Notes: n/a

## Aggregate Metrics

### baseline-current

| Metric | Value |
| --- | --- |
| `case_count` | 6 |
| `error_count` | 0 |
| `avg_latency_ms` | 97.5565 |
| `avg_expected_point_coverage` | 0.1333 |
| `missing_evidence_accuracy` | 0.0000 |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 0.7000 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

### current-evidence

| Metric | Value |
| --- | --- |
| `case_count` | 6 |
| `error_count` | 0 |
| `avg_latency_ms` | 74.5992 |
| `avg_expected_point_coverage` | 0.1333 |
| `missing_evidence_accuracy` | 0.0000 |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 0.9000 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

## Metrics By Category

### comparison

**baseline-current**

| Metric | Value |
| --- | --- |
| `case_count` | 1 |
| `error_count` | 0 |
| `avg_latency_ms` | 114.6280 |
| `avg_expected_point_coverage` | 0.6667 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 0.5000 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

**current-evidence**

| Metric | Value |
| --- | --- |
| `case_count` | 1 |
| `error_count` | 0 |
| `avg_latency_ms` | 195.1780 |
| `avg_expected_point_coverage` | 0.6667 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 0.5000 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

### follow-up-style

**baseline-current**

| Metric | Value |
| --- | --- |
| `case_count` | 1 |
| `error_count` | 0 |
| `avg_latency_ms` | 22.0740 |
| `avg_expected_point_coverage` | 0.0000 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 0.0000 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

**current-evidence**

| Metric | Value |
| --- | --- |
| `case_count` | 1 |
| `error_count` | 0 |
| `avg_latency_ms` | 24.1150 |
| `avg_expected_point_coverage` | 0.0000 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 1.0000 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

### identifier

**baseline-current**

| Metric | Value |
| --- | --- |
| `case_count` | 1 |
| `error_count` | 0 |
| `avg_latency_ms` | 15.5430 |
| `avg_expected_point_coverage` | 0.0000 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 1.0000 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

**current-evidence**

| Metric | Value |
| --- | --- |
| `case_count` | 1 |
| `error_count` | 0 |
| `avg_latency_ms` | 15.7830 |
| `avg_expected_point_coverage` | 0.0000 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 1.0000 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

### method

**baseline-current**

| Metric | Value |
| --- | --- |
| `case_count` | 1 |
| `error_count` | 0 |
| `avg_latency_ms` | 316.0210 |
| `avg_expected_point_coverage` | 0.0000 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 1.0000 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

**current-evidence**

| Metric | Value |
| --- | --- |
| `case_count` | 1 |
| `error_count` | 0 |
| `avg_latency_ms` | 88.8720 |
| `avg_expected_point_coverage` | 0.0000 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 1.0000 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

### no-answer

**baseline-current**

| Metric | Value |
| --- | --- |
| `case_count` | 1 |
| `error_count` | 0 |
| `avg_latency_ms` | 96.6900 |
| `avg_expected_point_coverage` | n/a |
| `missing_evidence_accuracy` | 0.0000 |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | n/a |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

**current-evidence**

| Metric | Value |
| --- | --- |
| `case_count` | 1 |
| `error_count` | 0 |
| `avg_latency_ms` | 103.9110 |
| `avg_expected_point_coverage` | n/a |
| `missing_evidence_accuracy` | 0.0000 |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | n/a |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

### result

**baseline-current**

| Metric | Value |
| --- | --- |
| `case_count` | 1 |
| `error_count` | 0 |
| `avg_latency_ms` | 20.3830 |
| `avg_expected_point_coverage` | 0.0000 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 1.0000 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

**current-evidence**

| Metric | Value |
| --- | --- |
| `case_count` | 1 |
| `error_count` | 0 |
| `avg_latency_ms` | 19.7360 |
| `avg_expected_point_coverage` | 0.0000 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 1.0000 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

## A/B Deltas

| Metric | Baseline | Comparison | Delta |
| --- | ---: | ---: | ---: |
| `avg_expected_point_coverage` | 0.1333 | 0.1333 | +0.0000 |
| `missing_evidence_accuracy` | 0.0000 | 0.0000 | +0.0000 |
| `avg_candidate_recall` | n/a | n/a | n/a |
| `avg_final_context_recall` | n/a | n/a | n/a |
| `avg_citation_recall` | n/a | n/a | n/a |
| `avg_quote_support_recall` | 0.7000 | 0.9000 | +0.2000 |
| `avg_accepted_evidence_precision` | n/a | n/a | n/a |
| `avg_accepted_evidence_recall` | n/a | n/a | n/a |
| `reference_contamination_rate` | 0.0000 | 0.0000 | +0.0000 |
| `avg_latency_ms` | 97.5565 | 74.5992 | -22.9573 |
| `error_count` | 0 | 0 | +0.0000 |

## Failed Or Weak Cases

| Case | Strategy | Reason |
| --- | --- | --- |
| `brepmfr-method-001` | `baseline-current` | expected coverage 0 |
| `brepmfr-method-001` | `current-evidence` | expected coverage 0 |
| `brepmfr-result-001` | `baseline-current` | expected coverage 0 |
| `brepmfr-result-001` | `current-evidence` | expected coverage 0 |
| `brepformer-identifier-001` | `baseline-current` | expected coverage 0 |
| `brepformer-identifier-001` | `current-evidence` | expected coverage 0 |
| `brepmfr-followup-style-001` | `baseline-current` | expected coverage 0 |
| `brepmfr-followup-style-001` | `current-evidence` | expected coverage 0 |
| `no-answer-training-data-001` | `baseline-current` | no-answer behavior failed |
| `no-answer-training-data-001` | `current-evidence` | no-answer behavior failed |

## Case Results

### brepmfr-method-001 (method)

Question: What is the core method of BrepMFR?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | n/a | 1.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 1.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“What is the core method of BrepMFR?”可从以下证据开始分析：# 4.1. Machining feature type and label The CADSynth dataset encompasses 24 machining features that are the same as those in MFCAD and MFAD++. The geometric shapes and indexes for each machining feature are illustrated in Fig. 7. # 4.2. Dataset generation CADSynth employs a random synthesis algorithm to combine various primitive elements (cuboid, prism, cylinder, cone, and sphere) to form the primary shape of a CAD model. This proc

Representative citation: `paper_0a722d8e689b4f0d_chunk_16` 5.1.2. Dataset

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“What is the core method of BrepMFR?”可从以下证据开始分析：# 4.1. Machining feature type and label The CADSynth dataset encompasses 24 machining features that are the same as those in MFCAD and MFAD++. The geometric shapes and indexes for each machining feature are illustrated in Fig. 7. # 4.2. Dataset generation CADSynth employs a random synthesis algorithm to combine various primitive elements (cuboid, prism, cylinder, cone, and sphere) to form the primary shape of a CAD model. This proc

Representative citation: `paper_0a722d8e689b4f0d_chunk_16` 5.1.2. Dataset

### brepmfr-result-001 (result)

Question: What performance does BrepMFR report on machining feature recognition?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | n/a | 1.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 1.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“What performance does BrepMFR report on machining feature recognition?”可从以下证据开始分析：# 4.1. Machining feature type and label The CADSynth dataset encompasses 24 machining features that are the same as those in MFCAD and MFAD++. The geometric shapes and indexes for each machining feature are illustrated in Fig. 7. # 4.2. Dataset generation CADSynth employs a random synthesis algorithm to combine various primitive elements (cuboid, prism, cylinder, cone, and sphere) to form the prim

Representative citation: `paper_0a722d8e689b4f0d_chunk_16` 5.1.2. Dataset

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“What performance does BrepMFR report on machining feature recognition?”可从以下证据开始分析：# 4.1. Machining feature type and label The CADSynth dataset encompasses 24 machining features that are the same as those in MFCAD and MFAD++. The geometric shapes and indexes for each machining feature are illustrated in Fig. 7. # 4.2. Dataset generation CADSynth employs a random synthesis algorithm to combine various primitive elements (cuboid, prism, cylinder, cone, and sphere) to form the prim

Representative citation: `paper_0a722d8e689b4f0d_chunk_16` 5.1.2. Dataset

### brepformer-identifier-001 (identifier)

Question: What DOI or arXiv identifier is available for BRepFormer?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | n/a | 1.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 1.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“What DOI or arXiv identifier is available for BRepFormer?”可从以下证据开始分析：# 1 Introduction Geometric feature recognition serves as a critical link between Computer-Aided Design (CAD) and Computer-Aided Manufacturing (CAM). It is a cornerstone technique for multimedia content-based retrieval and plays a key role in automating manufacturing processes, improving efficiency, and reducing human errors. While traditional rule-based geometric feature recognition methods are widely used in 

Representative citation: `paper_1d77c9ee3c5f413d_chunk_5` Introduction

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“What DOI or arXiv identifier is available for BRepFormer?”可从以下证据开始分析：# 1 Introduction Geometric feature recognition serves as a critical link between Computer-Aided Design (CAD) and Computer-Aided Manufacturing (CAM). It is a cornerstone technique for multimedia content-based retrieval and plays a key role in automating manufacturing processes, improving efficiency, and reducing human errors. While traditional rule-based geometric feature recognition methods are widely used in 

Representative citation: `paper_1d77c9ee3c5f413d_chunk_5` Introduction

### cross-paper-compare-001 (comparison)

Question: Compare BrepMFR and BRepFormer at a high level.

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.6667 | 1.0000 | n/a | 0.5000 | n/a |  |
| current-evidence | 0.6667 | 1.0000 | n/a | 0.5000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“Compare BrepMFR and BRepFormer at a high level.”可从以下证据开始分析：5.2.3 Complex Feature Dataset. In our CBF dataset, unlike previous datasets, this dataset requires the model to identify these three distinct geometric features along with the base plate. The experimental results of our model and other mainstream models on this dataset is presented in Table 5. Although our network outperforms other comparative networks in terms of overall accuracy, it performs poorly in the mIoU metric.

Representative citation: `paper_1d77c9ee3c5f413d_chunk_23` Experimental Datasets

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“Compare BrepMFR and BRepFormer at a high level.”可从以下证据开始分析：5.2.3 Complex Feature Dataset. In our CBF dataset, unlike previous datasets, this dataset requires the model to identify these three distinct geometric features along with the base plate. The experimental results of our model and other mainstream models on this dataset is presented in Table 5. Although our network outperforms other comparative networks in terms of overall accuracy, it performs poorly in the mIoU metric.

Representative citation: `paper_1d77c9ee3c5f413d_chunk_23` Experimental Datasets

### brepmfr-followup-style-001 (follow-up-style)

Question: For the same BrepMFR paper, what network components are used after the B-rep face input features are encoded?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 1.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“For the same BrepMFR paper, what network components are used after the B-rep face input features are encoded?”可从以下证据开始分析：# 4.1. Machining feature type and label The CADSynth dataset encompasses 24 machining features that are the same as those in MFCAD and MFAD++. The geometric shapes and indexes for each machining feature are illustrated in Fig. 7. # 4.2. Dataset generation CADSynth employs a random synthesis algorithm to combine various primitive elements (cuboid, prism, cylin

Representative citation: `paper_0a722d8e689b4f0d_chunk_16` 5.1.2. Dataset

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“For the same BrepMFR paper, what network components are used after the B-rep face input features are encoded?”可从以下证据开始分析：# 4.1. Machining feature type and label The CADSynth dataset encompasses 24 machining features that are the same as those in MFCAD and MFAD++. The geometric shapes and indexes for each machining feature are illustrated in Fig. 7. # 4.2. Dataset generation CADSynth employs a random synthesis algorithm to combine various primitive elements (cuboid, prism, cylin

Representative citation: `paper_0a722d8e689b4f0d_chunk_16` 5.1.2. Dataset

### no-answer-training-data-001 (no-answer)

Question: Does BRepFormer report using the CIFAR-10 image classification dataset?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | n/a | 1.0000 | n/a | n/a | no |  |
| current-evidence | n/a | 1.0000 | n/a | n/a | no |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“Does BRepFormer report using the CIFAR-10 image classification dataset?”可从以下证据开始分析：# 5.1 Experimental Environment We trained our network using a single NVIDIA 4090 GPU and PyTorch-Lightning v1.9.0, highlighting its lightweight nature. During training, we used the AdamW optimizer with an initial learning rate of 0.001, and parameters set to $\beta_{1} = 0.9$ , $\beta_{2} = 0.999$ , and $\epsilon = 1 \times 10^{-8}$ for stability. We also employed the ReduceLROn-Plateau [2] learn

Representative citation: `paper_1d77c9ee3c5f413d_chunk_21` Experimental Environment

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“Does BRepFormer report using the CIFAR-10 image classification dataset?”可从以下证据开始分析：# 5.1 Experimental Environment We trained our network using a single NVIDIA 4090 GPU and PyTorch-Lightning v1.9.0, highlighting its lightweight nature. During training, we used the AdamW optimizer with an initial learning rate of 0.001, and parameters set to $\beta_{1} = 0.9$ , $\beta_{2} = 0.999$ , and $\epsilon = 1 \times 10^{-8}$ for stability. We also employed the ReduceLROn-Plateau [2] learn

Representative citation: `paper_1d77c9ee3c5f413d_chunk_21` Experimental Environment
