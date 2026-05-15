# RAG A/B Evaluation Report

## Run Configuration

- Cases: `evals\rag_ab\qasper_validation_local_subset_chunked.jsonl`
- Baseline: `baseline-current`
- Comparison: `current-evidence`
- Mode: `in-process`
- Current API URL: `n/a`
- Old-code API URL: `n/a`
- Deterministic local: `True`
- LLM judge: `False`
- top_k: `8`
- Output directory: `evals/rag_ab/runs/qasper_intent_claims_final_current`
- Case file sha256: `61cf3b1bcc5dcab8b69db7462b360b939a984e766cefa4870729045748d7f4a8`
- Timestamp: `2026-05-15T08:20:46.459846+00:00`
- Git revision: `502640726e1404a14fe33793040ad50a559d06bc`
- Notes: citation_selection_mode=current; intent_claim_selector_final

## Aggregate Metrics

### baseline-current

| Metric | Value |
| --- | --- |
| `case_count` | 12 |
| `error_count` | 0 |
| `avg_latency_ms` | 97.4715 |
| `avg_expected_point_coverage` | 0.2917 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | 0.7917 |
| `avg_citation_count` | 3.0000 |
| `avg_citation_recall` | 0.2917 |
| `avg_citation_precision` | 0.1389 |
| `avg_answer_source_count` | 0.0000 |
| `avg_answer_source_recall` | 0.0000 |
| `avg_answer_source_precision` | n/a |
| `avg_quote_support_recall` | 0.1667 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

### current-evidence

| Metric | Value |
| --- | --- |
| `case_count` | 12 |
| `error_count` | 0 |
| `avg_latency_ms` | 98.4942 |
| `avg_expected_point_coverage` | 0.3194 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | 1.0000 |
| `avg_final_context_recall` | 0.7917 |
| `avg_citation_count` | 3.2500 |
| `avg_citation_recall` | 0.7083 |
| `avg_citation_precision` | 0.2778 |
| `avg_answer_source_count` | 3.0000 |
| `avg_answer_source_recall` | 0.7083 |
| `avg_answer_source_precision` | 0.3055 |
| `avg_quote_support_recall` | 0.2222 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | 0.1250 |
| `avg_accepted_evidence_recall` | 0.7917 |

## Metrics By Category

### dataset

**baseline-current**

| Metric | Value |
| --- | --- |
| `case_count` | 4 |
| `error_count` | 0 |
| `avg_latency_ms` | 195.8145 |
| `avg_expected_point_coverage` | 0.7917 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | 0.7500 |
| `avg_citation_count` | 3.0000 |
| `avg_citation_recall` | 0.7500 |
| `avg_citation_precision` | 0.3333 |
| `avg_answer_source_count` | 0.0000 |
| `avg_answer_source_recall` | 0.0000 |
| `avg_answer_source_precision` | n/a |
| `avg_quote_support_recall` | 0.0000 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

**current-evidence**

| Metric | Value |
| --- | --- |
| `case_count` | 4 |
| `error_count` | 0 |
| `avg_latency_ms` | 153.8040 |
| `avg_expected_point_coverage` | 0.3333 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | 1.0000 |
| `avg_final_context_recall` | 0.7500 |
| `avg_citation_count` | 3.0000 |
| `avg_citation_recall` | 0.7500 |
| `avg_citation_precision` | 0.3333 |
| `avg_answer_source_count` | 3.0000 |
| `avg_answer_source_recall` | 0.7500 |
| `avg_answer_source_precision` | 0.3333 |
| `avg_quote_support_recall` | 0.0000 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | 0.1250 |
| `avg_accepted_evidence_recall` | 0.7500 |

### method

**baseline-current**

| Metric | Value |
| --- | --- |
| `case_count` | 3 |
| `error_count` | 0 |
| `avg_latency_ms` | 74.1567 |
| `avg_expected_point_coverage` | 0.1111 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | 0.6667 |
| `avg_citation_count` | 3.0000 |
| `avg_citation_recall` | 0.0000 |
| `avg_citation_precision` | 0.0000 |
| `avg_answer_source_count` | 0.0000 |
| `avg_answer_source_recall` | 0.0000 |
| `avg_answer_source_precision` | n/a |
| `avg_quote_support_recall` | 0.1111 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

**current-evidence**

| Metric | Value |
| --- | --- |
| `case_count` | 3 |
| `error_count` | 0 |
| `avg_latency_ms` | 105.5693 |
| `avg_expected_point_coverage` | 0.2222 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | 1.0000 |
| `avg_final_context_recall` | 0.6667 |
| `avg_citation_count` | 3.3333 |
| `avg_citation_recall` | 0.3333 |
| `avg_citation_precision` | 0.1667 |
| `avg_answer_source_count` | 3.0000 |
| `avg_answer_source_recall` | 0.3333 |
| `avg_answer_source_precision` | 0.2222 |
| `avg_quote_support_recall` | 0.1111 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | 0.1250 |
| `avg_accepted_evidence_recall` | 0.6667 |

### paper-qa

**baseline-current**

| Metric | Value |
| --- | --- |
| `case_count` | 5 |
| `error_count` | 0 |
| `avg_latency_ms` | 32.7860 |
| `avg_expected_point_coverage` | 0.0000 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | 0.9000 |
| `avg_citation_count` | 3.0000 |
| `avg_citation_recall` | 0.1000 |
| `avg_citation_precision` | 0.0667 |
| `avg_answer_source_count` | 0.0000 |
| `avg_answer_source_recall` | 0.0000 |
| `avg_answer_source_precision` | n/a |
| `avg_quote_support_recall` | 0.3333 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

**current-evidence**

| Metric | Value |
| --- | --- |
| `case_count` | 5 |
| `error_count` | 0 |
| `avg_latency_ms` | 50.0012 |
| `avg_expected_point_coverage` | 0.3667 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | 1.0000 |
| `avg_final_context_recall` | 0.9000 |
| `avg_citation_count` | 3.4000 |
| `avg_citation_recall` | 0.9000 |
| `avg_citation_precision` | 0.3000 |
| `avg_answer_source_count` | 3.0000 |
| `avg_answer_source_recall` | 0.9000 |
| `avg_answer_source_precision` | 0.3333 |
| `avg_quote_support_recall` | 0.4667 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | 0.1250 |
| `avg_accepted_evidence_recall` | 0.9000 |

## A/B Deltas

| Metric | Baseline | Comparison | Delta |
| --- | ---: | ---: | ---: |
| `avg_expected_point_coverage` | 0.2917 | 0.3194 | +0.0277 |
| `missing_evidence_accuracy` | n/a | n/a | n/a |
| `avg_candidate_recall` | n/a | 1.0000 | n/a |
| `avg_final_context_recall` | 0.7917 | 0.7917 | +0.0000 |
| `avg_citation_count` | 3.0000 | 3.2500 | +0.2500 |
| `avg_citation_recall` | 0.2917 | 0.7083 | +0.4166 |
| `avg_citation_precision` | 0.1389 | 0.2778 | +0.1389 |
| `avg_answer_source_count` | 0.0000 | 3.0000 | +3.0000 |
| `avg_answer_source_recall` | 0.0000 | 0.7083 | +0.7083 |
| `avg_answer_source_precision` | n/a | 0.3055 | n/a |
| `avg_quote_support_recall` | 0.1667 | 0.2222 | +0.0555 |
| `avg_accepted_evidence_precision` | n/a | 0.1250 | n/a |
| `avg_accepted_evidence_recall` | n/a | 0.7917 | n/a |
| `reference_contamination_rate` | 0.0000 | 0.0000 | +0.0000 |
| `avg_latency_ms` | 97.4715 | 98.4942 | +1.0227 |
| `error_count` | 0 | 0 | +0.0000 |

## Failed Or Weak Cases

| Case | Strategy | Reason |
| --- | --- | --- |
| `qasper-val-0004` | `baseline-current` | expected coverage 0 |
| `qasper-val-0008` | `baseline-current` | expected coverage 0 |
| `qasper-val-0008` | `current-evidence` | expected coverage 0 |
| `qasper-val-0009` | `baseline-current` | expected coverage 0 |
| `qasper-val-0009` | `current-evidence` | expected coverage 0 |
| `qasper-val-0011` | `baseline-current` | expected coverage 0 |
| `qasper-val-0011` | `current-evidence` | expected coverage 0 |
| `qasper-val-0013` | `current-evidence` | expected coverage 0 |
| `qasper-val-0016` | `current-evidence` | expected coverage 0 |
| `qasper-val-0017` | `baseline-current` | expected coverage 0 |
| `qasper-val-0020` | `baseline-current` | expected coverage 0 |
| `qasper-val-0022` | `baseline-current` | expected coverage 0 |
| `qasper-val-0022` | `current-evidence` | expected coverage 0 |

## Case Results

### qasper-val-0003 (dataset)

Question: which datasets did they experiment with?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 1.0000 | 1.0000 | 1.0000 | 0.0000 | n/a |  |
| current-evidence | 1.0000 | 1.0000 | 1.0000 | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“which datasets did they experiment with?”可从以下证据开始分析：# Setup We evaluate our cross-lingual pre-training based transfer approach against several strong baselines on two public datasets, Europarl (Koehn 2005) and MultiUN (Eisele and Chen 2010), which contain multi-parallel evaluation data to assess the zero-shot performance. In all experiments, we use BLEU as the automatic metric for translation evaluation. $^{1}$ Datasets. The statistics of Europarl and MultiUN corpora are summar

Representative citation: `paper_4989cdaf64974840_chunk_11` Setup

**current-evidence answer preview:**

# Setup We evaluate our cross-lingual pre-training based transfer approach against several strong baselines on two public datasets, Europarl (Koehn 2005) and MultiUN (Eisele and Chen 2010), which contain multi-parallel evaluation data to assess the zero-shot performance. [C1] In our experiments, we use MLM+TLM, MLM+BRLM to represent this training process. [C2] Like experimental results on Europarl, MLM+BRLM-SA performs the best among all proposed cross-lingual pretraining based transfer approach

Representative citation: `paper_4989cdaf64974840_chunk_11` Setup

### qasper-val-0004 (paper-qa)

Question: what language pairs are explored?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | 1.0000 | 0.3333 | n/a |  |
| current-evidence | 0.3333 | 1.0000 | 1.0000 | 0.3333 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“what language pairs are explored?”可从以下证据开始分析：# Introduction Although Neural Machine Translation (NMT) has dominated recent research on translation tasks (Wu et al. 2016; Vaswani et al. 2017; Hassan et al. 2018), NMT heavily relies on large-scale parallel data, resulting in poor performance on low-resource or zero-resource language pairs (Koehn and Knowles 2017). Translation between these low-resource languages (e.g., Arabic→Spanish) is usually accomplished with pivoting through

Representative citation: `paper_4989cdaf64974840_chunk_2` Introduction

**current-evidence answer preview:**

2018), NMT heavily relies on large-scale parallel data, resulting in poor performance on low-resource or zero-resource language pairs (Koehn and Knowles 2017). [C1] \- Multilingual NMT (MNMT) enables training a single model that supports translation from multiple source languages into multiple target languages, even those unseen language pairs (Firat, Cho, and Bengio 2016; Firat et al. [C2] For Europarl corpus, we evaluate on French-English-Spanish (Fr-En-Es), German-English-French (De-En-Fr) an

Representative citation: `paper_4989cdaf64974840_chunk_2` Introduction

### qasper-val-0005 (method)

Question: what ner models were evaluated?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.3333 | 1.0000 | 1.0000 | 0.3333 | n/a |  |
| current-evidence | 0.6667 | 1.0000 | 1.0000 | 0.3333 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“what ner models were evaluated?”可从以下证据开始分析：# VI. DISCUSSION Table III shows the average scores of evaluated models. The highest F1 score was achieved by the recurrent model using a batch size of 8 and Adam optimizer with an initial learning rate of 0.001. Updating word embeddings during training also noticeably improved the performance. GloVe word vector models of four different sizes (50, 100, 200, and 300) were tested, with vectors of size 50 producing the best results (Table

Representative citation: `paper_18c9a8ee5ba54ec6_chunk_13` VI. DISCUSSION

**current-evidence answer preview:**

Klesti Hoxha and Artur Baxhaku employ gazetteers extracted from Wikipedia to generate an annotated corpus for Albanian [4], and Weber and Pötzl propose a rule-based system for German that leverages the information from Wikipedia [5]. [C5] We trained and evaluated Stanford NER $^{4}$ , spaCy 2.0 $^{5}$ , and a recurrent model similar to [14], [15] that uses bidirectional LSTM cells for character-based feature extraction and CRF, described in Guillaume Genthial's Sequence Tagging with Tensorflow b

Representative citation: `paper_18c9a8ee5ba54ec6_chunk_1` I. INTRODUCTION

### qasper-val-0008 (paper-qa)

Question: what are the topics pulled from Reddit?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | 0.5000 | 0.3333 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | 0.5000 | 1.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“what are the topics pulled from Reddit?”可从以下证据开始分析：# 1 Introduction “I’m supposed to trust the opinion of a MS minion? The people that produced Windows ME, Vista and 8? They don’t even understand people, yet they think they can predict the behavior of new, self-guiding AI?” –anonymous “I think an AI would make it easier for Patients to confide their information because by nature, a robot cannot judge them. Win-win? :D” –anonymous Dogmatism describes the tendency to lay down opi

Representative citation: `paper_966b9c5490524541_chunk_2` Introduction

**current-evidence answer preview:**

$^{1}$ Posts on Reddit capture discussion and debate across a diverse set of domains and topics – users talk about everything from climate change and abortion, to world news and relationship advice, to the future of artificial intelligence. [C1] # 2 Dogmatism data Posts on Reddit capture debate and discussion across a diverse set of topics, making them a natural starting point for untangling domain-independent linguistic features of dogmatism. [C2] For example, we might expect to see that subred

Representative citation: `paper_966b9c5490524541_chunk_2` Introduction

### qasper-val-0009 (method)

Question: What predictive model do they build?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | 1.0000 | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | 1.0000 | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“What predictive model do they build?”可从以下证据开始分析：# 1 Introduction “I’m supposed to trust the opinion of a MS minion? The people that produced Windows ME, Vista and 8? They don’t even understand people, yet they think they can predict the behavior of new, self-guiding AI?” –anonymous “I think an AI would make it easier for Patients to confide their information because by nature, a robot cannot judge them. Win-win? :D” –anonymous Dogmatism describes the tendency to lay down opinio

Representative citation: `paper_966b9c5490524541_chunk_2` Introduction

**current-evidence answer preview:**

First, we validate psychological theories by examining the predictive power of feature sets that guide the model's predictions. [C1] Positive coefficients in this model are positively predictive of dogmatism, while negative coefficients are negatively predictive. [C2] Building a useful computational model requires labeled training data. [C8]

Representative citation: `paper_966b9c5490524541_chunk_2` Introduction

### qasper-val-0011 (paper-qa)

Question: How do they match words before reordering them?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | 1.0000 | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | 1.0000 | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“How do they match words before reordering them?”可从以下证据开始分析：# 3 Proposed Solution Consider the task of translating for an extremely low-resource language pair. The parallel corpus between the two languages, if available may be too small to train an NMT model. Similar to Zoph et al. (2016), we use transfer learning to overcome data sparsity between the source and the target languages. We choose English as the assisting language in all our experiments. In our resource-scarce scena

Representative citation: `paper_ee722d8eebe849f9_chunk_4` Proposed Solution

**current-evidence answer preview:**

<table><tr><td>Before Reordering</td><td>After Reordering</td></tr><tr><td><img src="images/8b823142d78335bf9c31d193aa8ed12331a33d08101cf8ad6678553f7e1bb6e7.jpg"/></td><td><img src="images/d492c8af2f577cc04d3200737b86afb2df7956f19c6de98af9ed683511e0a539.jpg"/></td></tr><tr><td><img... [C1] To address the word order divergence, we propose to pre-order the assisting language sentences (SVO) to match the word order of the source language (SOV). [C3] It contains two pre-ordering configurations: (1) 

Representative citation: `paper_ee722d8eebe849f9_chunk_4` Proposed Solution

### qasper-val-0013 (dataset)

Question: Which dataset(s) do they experiment with?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.5000 | 1.0000 | 1.0000 | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | 1.0000 | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“Which dataset(s) do they experiment with?”可从以下证据开始分析：# 4 Experimental Setup In this section, we describe the languages experimented with, datasets used, the network hyperparameters used in our experiments. Languages: We experimented with English → Hindi translation as the parent task. English is the assisting source language. Bengali, Gujarati, Marathi, Malayalam and Tamil are the source languages, and translation from these to Hindi constitute the child tasks. Hindi, Bengali, 

Representative citation: `paper_ee722d8eebe849f9_chunk_5` Experimental Setup

**current-evidence answer preview:**

# 4 Experimental Setup In this section, we describe the languages experimented with, datasets used, the network hyperparameters used in our experiments. [C1] # 5 Results We experiment with two scenarios: (a) an extremely resource scarce scenario with no parallel corpus for child tasks, (b) varying amounts of parallel corpora available for child task. [C2] # 5.1 No Parallel Corpus for Child Task The results from our experiments are presented in the Table 2. [C7]

Representative citation: `paper_ee722d8eebe849f9_chunk_5` Experimental Setup

### qasper-val-0016 (dataset)

Question: On which benchmarks they achieve the state of the art?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 1.0000 | 1.0000 | 1.0000 | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | 1.0000 | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“On which benchmarks they achieve the state of the art?”可从以下证据开始分析：# 6.3 KBQA End-Task Results Table 3 compares our system with two published baselines (1) STAGG (Yih et al., 2015), the state-of-the-art on WebQSP $^{11}$ and (2) AMPCNN (Yin et al., 2016), the state-of-the-art on SimpleQuestions. Since these two baselines are specially designed/tuned for one particular dataset, they do not generalize well when applied to the other dataset. In order to highlight the effect of diff

Representative citation: `paper_ad6cad90ed1d41d6_chunk_20` KBQA End-Task Results

**current-evidence answer preview:**

Note that in contrast to previous KBQA systems, our system does not use joint-inference or feature-based re-ranking step, nevertheless it still achieves better or comparable results to the state-of-the-art. [C1] The AMPCNN result is from (Yin et al., 2016), which yielded state-of-the-art scores by outperforming several attention-based methods. [C3] Our main contributions include: (i) An improved relation detection model by hierarchical matching between questions and relations with residual learn

Representative citation: `paper_ad6cad90ed1d41d6_chunk_20` KBQA End-Task Results

### qasper-val-0017 (paper-qa)

Question: What does KBQA abbreviate for

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | 1.0000 | 0.0000 | n/a |  |
| current-evidence | 1.0000 | 1.0000 | 1.0000 | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“What does KBQA abbreviate for”可从以下证据开始分析：# 4.2 Different Abstractions of Questions Representations From Table 1, we can see that different parts of a relation could match different contexts of question texts. Usually relation names could match longer phrases in the question and relation words could match short phrases. Yet different words might match phrases of different lengths. As a result, we hope the question representations could also comprise vectors that summarize variou

Representative citation: `paper_ad6cad90ed1d41d6_chunk_8` Different Abstractions of Questions Representations

**current-evidence answer preview:**

# 6.3 KBQA End-Task Results Table 3 compares our system with two published baselines (1) STAGG (Yih et al., 2015), the state-of-the-art on WebQSP $^{11}$ and (2) AMPCNN (Yin et al., 2016), the state-of-the-art on SimpleQuestions. [C2] ![](images/9045bf810b97306f3cd9164cfec30e865fec708d5142880f0a3eb85137c462b5.jpg) <details> <summary>flowchart</summary> ```mermaid graph TD A["Question: what episode was mike kelley the writer of"] --> B["Entity Linking"] B --> C["Mike Kelley"] C --> D["episodes_wr

Representative citation: `paper_ad6cad90ed1d41d6_chunk_20` KBQA End-Task Results

### qasper-val-0020 (paper-qa)

Question: How do they calculate a static embedding for each word?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | 1.0000 | 1.0000 | n/a |  |
| current-evidence | 0.5000 | 1.0000 | 1.0000 | 1.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“How do they calculate a static embedding for each word?”可从以下证据开始分析：# 3.1 Contextualizing Models The contextualizing models we study in this paper are ELMo, BERT, and GPT-2 $^{1}$ . We choose the base cased version of BERT because it is most comparable to GPT-2 with respect to number of layers and dimensionality. The models we work with are all pre-trained on their respective language modelling tasks. Although ELMo, BERT, and GPT-2 have 2, 12, and 12 hidden layers respectively, 

Representative citation: `paper_f34858cc477d48bb_chunk_5` Contextualizing Models

**current-evidence answer preview:**

Traditionally, these word embeddings were static: each word had a single vector, regardless of context (Mikolov et al., 2013a; Pennington et al., 2014). [C3] Because they create a single representation for each word, a notable problem with static word embeddings is that all senses of a polysemous word must share a single vector. [C4] As noted earlier, we can create static embeddings for each word by taking the first principal component (PC) of its contextualized representations in a given layer.

Representative citation: `paper_f34858cc477d48bb_chunk_2` Introduction

### qasper-val-0022 (method)

Question: What are the other algorithms tested?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | 0.0000 | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | 0.0000 | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“What are the other algorithms tested?”可从以下证据开始分析：# 3. Materials and Methods The aim of this paper is to evaluate BERT's multilingual model and compare it to other established machine-learning algorithms in a specific task: sensitive data detection and classification in Spanish clinical free text. This section describes the data involved in the experiments and the systems evaluated. Finally, we introduce the experimental setup.

Representative citation: `paper_c23b8432b797410b_chunk_5` Materials and Methods

**current-evidence answer preview:**

Materials and Methods The aim of this paper is to evaluate BERT's multilingual model and compare it to other established machine-learning algorithms in a specific task: sensitive data detection and classification in Spanish clinical free text. [C1] We have compared this BERT-based sequence labelling against other methods and systems. [C2] We also compare BERT to other algorithms. [C5]

Representative citation: `paper_c23b8432b797410b_chunk_5` Materials and Methods

### qasper-val-0024 (dataset)

Question: What are the clinical datasets used in the paper?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.6667 | 1.0000 | 0.0000 | 0.0000 | n/a |  |
| current-evidence | 0.3333 | 1.0000 | 0.0000 | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“What are the clinical datasets used in the paper?”可从以下证据开始分析：# 3.3.1. Experiment A: NUBES-PHI In this experiment set, we evaluate all the systems presented in Section 3.2., namely, the rule-based baseline, the CRF classifier, the spaCy entity tagger, and BERT. The evaluation comprises three scenarios of increasing difficulty: <table><tr><td></td><td colspan="3">Detection</td><td colspan="3">Classification (relaxed)</td><td colspan="3">Classification...

Representative citation: `paper_c23b8432b797410b_chunk_16` Experiment A: NUBES-PHI

**current-evidence answer preview:**

Detecting entity types correctly is important if a system is going to be used to replace sensitive data by fake data of the same type (e.g., random people names). [C1] Experiment B: MEDDOCAN In this experiment set, our BERT implementation is compared to several systems that participated in the MEDDO-CAN challenge: a CRF classifier (Perez et al., 2019), a spaCy entity recogniser (Perez et al., 2019), and NLNDE (Lange et al., 2019), the winner of the shared task and current state of... [C2] Experi

Representative citation: `paper_c23b8432b797410b_chunk_16` Experiment A: NUBES-PHI
