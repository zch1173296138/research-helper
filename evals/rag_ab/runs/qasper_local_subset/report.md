# RAG A/B Evaluation Report

## Run Configuration

- Cases: `evals\rag_ab\qasper_validation_local_subset.jsonl`
- Baseline: `baseline-current`
- Comparison: `current-evidence`
- Mode: `in-process`
- Current API URL: `n/a`
- Old-code API URL: `n/a`
- Deterministic local: `True`
- LLM judge: `False`
- top_k: `8`
- Output directory: `evals/rag_ab/runs/qasper_local_subset`
- Case file sha256: `2587cca802ce7a459608757b4210d6ef001fe6b978ee424f6d9c903edf2fe7cd`
- Timestamp: `2026-05-14T06:18:30.253961+00:00`
- Git revision: `c6697200cb09a73fcf21ab06e7cc824461e0c1bc`
- Notes: n/a

## Aggregate Metrics

### baseline-current

| Metric | Value |
| --- | --- |
| `case_count` | 12 |
| `error_count` | 0 |
| `avg_latency_ms` | 55.3691 |
| `avg_expected_point_coverage` | 0.2917 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 0.1667 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

### current-evidence

| Metric | Value |
| --- | --- |
| `case_count` | 12 |
| `error_count` | 0 |
| `avg_latency_ms` | 37.5497 |
| `avg_expected_point_coverage` | 0.2917 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 0.2222 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

## Metrics By Category

### dataset

**baseline-current**

| Metric | Value |
| --- | --- |
| `case_count` | 4 |
| `error_count` | 0 |
| `avg_latency_ms` | 124.0700 |
| `avg_expected_point_coverage` | 0.7917 |
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
| `case_count` | 4 |
| `error_count` | 0 |
| `avg_latency_ms` | 67.9250 |
| `avg_expected_point_coverage` | 0.7917 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 0.0000 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

### method

**baseline-current**

| Metric | Value |
| --- | --- |
| `case_count` | 3 |
| `error_count` | 0 |
| `avg_latency_ms` | 30.8067 |
| `avg_expected_point_coverage` | 0.1111 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 0.1111 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

**current-evidence**

| Metric | Value |
| --- | --- |
| `case_count` | 3 |
| `error_count` | 0 |
| `avg_latency_ms` | 35.7850 |
| `avg_expected_point_coverage` | 0.1111 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 0.1111 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

### paper-qa

**baseline-current**

| Metric | Value |
| --- | --- |
| `case_count` | 5 |
| `error_count` | 0 |
| `avg_latency_ms` | 15.1458 |
| `avg_expected_point_coverage` | 0.0000 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 0.3333 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

**current-evidence**

| Metric | Value |
| --- | --- |
| `case_count` | 5 |
| `error_count` | 0 |
| `avg_latency_ms` | 14.3082 |
| `avg_expected_point_coverage` | 0.0000 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 0.4667 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

## A/B Deltas

| Metric | Baseline | Comparison | Delta |
| --- | ---: | ---: | ---: |
| `avg_expected_point_coverage` | 0.2917 | 0.2917 | +0.0000 |
| `missing_evidence_accuracy` | n/a | n/a | n/a |
| `avg_candidate_recall` | n/a | n/a | n/a |
| `avg_final_context_recall` | n/a | n/a | n/a |
| `avg_citation_recall` | n/a | n/a | n/a |
| `avg_quote_support_recall` | 0.1667 | 0.2222 | +0.0555 |
| `avg_accepted_evidence_precision` | n/a | n/a | n/a |
| `avg_accepted_evidence_recall` | n/a | n/a | n/a |
| `reference_contamination_rate` | 0.0000 | 0.0000 | +0.0000 |
| `avg_latency_ms` | 55.3691 | 37.5497 | -17.8194 |
| `error_count` | 0 | 0 | +0.0000 |

## Failed Or Weak Cases

| Case | Strategy | Reason |
| --- | --- | --- |
| `qasper-val-0004` | `baseline-current` | expected coverage 0 |
| `qasper-val-0004` | `current-evidence` | expected coverage 0 |
| `qasper-val-0008` | `baseline-current` | expected coverage 0 |
| `qasper-val-0008` | `current-evidence` | expected coverage 0 |
| `qasper-val-0009` | `baseline-current` | expected coverage 0 |
| `qasper-val-0009` | `current-evidence` | expected coverage 0 |
| `qasper-val-0011` | `baseline-current` | expected coverage 0 |
| `qasper-val-0011` | `current-evidence` | expected coverage 0 |
| `qasper-val-0017` | `baseline-current` | expected coverage 0 |
| `qasper-val-0017` | `current-evidence` | expected coverage 0 |
| `qasper-val-0020` | `baseline-current` | expected coverage 0 |
| `qasper-val-0020` | `current-evidence` | expected coverage 0 |
| `qasper-val-0022` | `baseline-current` | expected coverage 0 |
| `qasper-val-0022` | `current-evidence` | expected coverage 0 |

## Case Results

### qasper-val-0003 (dataset)

Question: which datasets did they experiment with?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 1.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 1.0000 | 1.0000 | n/a | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“which datasets did they experiment with?”可从以下证据开始分析：# Setup We evaluate our cross-lingual pre-training based transfer approach against several strong baselines on two public datasets, Europarl (Koehn 2005) and MultiUN (Eisele and Chen 2010), which contain multi-parallel evaluation data to assess the zero-shot performance. In all experiments, we use BLEU as the automatic metric for translation evaluation. $^{1}$ Datasets. The statistics of Europarl and MultiUN corpora are summar

Representative citation: `paper_4989cdaf64974840_chunk_11` Setup

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“which datasets did they experiment with?”可从以下证据开始分析：# Setup We evaluate our cross-lingual pre-training based transfer approach against several strong baselines on two public datasets, Europarl (Koehn 2005) and MultiUN (Eisele and Chen 2010), which contain multi-parallel evaluation data to assess the zero-shot performance. In all experiments, we use BLEU as the automatic metric for translation evaluation. $^{1}$ Datasets. The statistics of Europarl and MultiUN corpora are summar

Representative citation: `paper_4989cdaf64974840_chunk_11` Setup

### qasper-val-0004 (paper-qa)

Question: what language pairs are explored?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | n/a | 0.3333 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 0.3333 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“what language pairs are explored?”可从以下证据开始分析：# Introduction Although Neural Machine Translation (NMT) has dominated recent research on translation tasks (Wu et al. 2016; Vaswani et al. 2017; Hassan et al. 2018), NMT heavily relies on large-scale parallel data, resulting in poor performance on low-resource or zero-resource language pairs (Koehn and Knowles 2017). Translation between these low-resource languages (e.g., Arabic→Spanish) is usually accomplished with pivoting through

Representative citation: `paper_4989cdaf64974840_chunk_2` Introduction

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“what language pairs are explored?”可从以下证据开始分析：# Introduction Although Neural Machine Translation (NMT) has dominated recent research on translation tasks (Wu et al. 2016; Vaswani et al. 2017; Hassan et al. 2018), NMT heavily relies on large-scale parallel data, resulting in poor performance on low-resource or zero-resource language pairs (Koehn and Knowles 2017). Translation between these low-resource languages (e.g., Arabic→Spanish) is usually accomplished with pivoting through

Representative citation: `paper_4989cdaf64974840_chunk_2` Introduction

### qasper-val-0005 (method)

Question: what ner models were evaluated?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.3333 | 1.0000 | n/a | 0.3333 | n/a |  |
| current-evidence | 0.3333 | 1.0000 | n/a | 0.3333 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“what ner models were evaluated?”可从以下证据开始分析：# VI. DISCUSSION Table III shows the average scores of evaluated models. The highest F1 score was achieved by the recurrent model using a batch size of 8 and Adam optimizer with an initial learning rate of 0.001. Updating word embeddings during training also noticeably improved the performance. GloVe word vector models of four different sizes (50, 100, 200, and 300) were tested, with vectors of size 50 producing the best results (Table

Representative citation: `paper_18c9a8ee5ba54ec6_chunk_13` VI. DISCUSSION

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“what ner models were evaluated?”可从以下证据开始分析：# VI. DISCUSSION Table III shows the average scores of evaluated models. The highest F1 score was achieved by the recurrent model using a batch size of 8 and Adam optimizer with an initial learning rate of 0.001. Updating word embeddings during training also noticeably improved the performance. GloVe word vector models of four different sizes (50, 100, 200, and 300) were tested, with vectors of size 50 producing the best results (Table

Representative citation: `paper_18c9a8ee5ba54ec6_chunk_13` VI. DISCUSSION

### qasper-val-0008 (paper-qa)

Question: what are the topics pulled from Reddit?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | n/a | 0.3333 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 1.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“what are the topics pulled from Reddit?”可从以下证据开始分析：# 1 Introduction “I’m supposed to trust the opinion of a MS minion? The people that produced Windows ME, Vista and 8? They don’t even understand people, yet they think they can predict the behavior of new, self-guiding AI?” –anonymous “I think an AI would make it easier for Patients to confide their information because by nature, a robot cannot judge them. Win-win? :D” –anonymous Dogmatism describes the tendency to lay down opi

Representative citation: `paper_966b9c5490524541_chunk_2` Introduction

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“what are the topics pulled from Reddit?”可从以下证据开始分析：# 1 Introduction “I’m supposed to trust the opinion of a MS minion? The people that produced Windows ME, Vista and 8? They don’t even understand people, yet they think they can predict the behavior of new, self-guiding AI?” –anonymous “I think an AI would make it easier for Patients to confide their information because by nature, a robot cannot judge them. Win-win? :D” –anonymous Dogmatism describes the tendency to lay down opi

Representative citation: `paper_966b9c5490524541_chunk_2` Introduction

### qasper-val-0009 (method)

Question: What predictive model do they build?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“What predictive model do they build?”可从以下证据开始分析：# 1 Introduction “I’m supposed to trust the opinion of a MS minion? The people that produced Windows ME, Vista and 8? They don’t even understand people, yet they think they can predict the behavior of new, self-guiding AI?” –anonymous “I think an AI would make it easier for Patients to confide their information because by nature, a robot cannot judge them. Win-win? :D” –anonymous Dogmatism describes the tendency to lay down opinio

Representative citation: `paper_966b9c5490524541_chunk_2` Introduction

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“What predictive model do they build?”可从以下证据开始分析：# 1 Introduction “I’m supposed to trust the opinion of a MS minion? The people that produced Windows ME, Vista and 8? They don’t even understand people, yet they think they can predict the behavior of new, self-guiding AI?” –anonymous “I think an AI would make it easier for Patients to confide their information because by nature, a robot cannot judge them. Win-win? :D” –anonymous Dogmatism describes the tendency to lay down opinio

Representative citation: `paper_966b9c5490524541_chunk_2` Introduction

### qasper-val-0011 (paper-qa)

Question: How do they match words before reordering them?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“How do they match words before reordering them?”可从以下证据开始分析：# 3 Proposed Solution Consider the task of translating for an extremely low-resource language pair. The parallel corpus between the two languages, if available may be too small to train an NMT model. Similar to Zoph et al. (2016), we use transfer learning to overcome data sparsity between the source and the target languages. We choose English as the assisting language in all our experiments. In our resource-scarce scena

Representative citation: `paper_ee722d8eebe849f9_chunk_4` Proposed Solution

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“How do they match words before reordering them?”可从以下证据开始分析：# 3 Proposed Solution Consider the task of translating for an extremely low-resource language pair. The parallel corpus between the two languages, if available may be too small to train an NMT model. Similar to Zoph et al. (2016), we use transfer learning to overcome data sparsity between the source and the target languages. We choose English as the assisting language in all our experiments. In our resource-scarce scena

Representative citation: `paper_ee722d8eebe849f9_chunk_4` Proposed Solution

### qasper-val-0013 (dataset)

Question: Which dataset(s) do they experiment with?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.5000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.5000 | 1.0000 | n/a | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“Which dataset(s) do they experiment with?”可从以下证据开始分析：# 4 Experimental Setup In this section, we describe the languages experimented with, datasets used, the network hyperparameters used in our experiments. Languages: We experimented with English → Hindi translation as the parent task. English is the assisting source language. Bengali, Gujarati, Marathi, Malayalam and Tamil are the source languages, and translation from these to Hindi constitute the child tasks. Hindi, Bengali, 

Representative citation: `paper_ee722d8eebe849f9_chunk_5` Experimental Setup

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“Which dataset(s) do they experiment with?”可从以下证据开始分析：# 4 Experimental Setup In this section, we describe the languages experimented with, datasets used, the network hyperparameters used in our experiments. Languages: We experimented with English → Hindi translation as the parent task. English is the assisting source language. Bengali, Gujarati, Marathi, Malayalam and Tamil are the source languages, and translation from these to Hindi constitute the child tasks. Hindi, Bengali, 

Representative citation: `paper_ee722d8eebe849f9_chunk_5` Experimental Setup

### qasper-val-0016 (dataset)

Question: On which benchmarks they achieve the state of the art?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 1.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 1.0000 | 1.0000 | n/a | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“On which benchmarks they achieve the state of the art?”可从以下证据开始分析：# 6.3 KBQA End-Task Results Table 3 compares our system with two published baselines (1) STAGG (Yih et al., 2015), the state-of-the-art on WebQSP $^{11}$ and (2) AMPCNN (Yin et al., 2016), the state-of-the-art on SimpleQuestions. Since these two baselines are specially designed/tuned for one particular dataset, they do not generalize well when applied to the other dataset. In order to highlight the effect of diff

Representative citation: `paper_ad6cad90ed1d41d6_chunk_20` KBQA End-Task Results

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“On which benchmarks they achieve the state of the art?”可从以下证据开始分析：# 6.3 KBQA End-Task Results Table 3 compares our system with two published baselines (1) STAGG (Yih et al., 2015), the state-of-the-art on WebQSP $^{11}$ and (2) AMPCNN (Yin et al., 2016), the state-of-the-art on SimpleQuestions. Since these two baselines are specially designed/tuned for one particular dataset, they do not generalize well when applied to the other dataset. In order to highlight the effect of diff

Representative citation: `paper_ad6cad90ed1d41d6_chunk_20` KBQA End-Task Results

### qasper-val-0017 (paper-qa)

Question: What does KBQA abbreviate for

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“What does KBQA abbreviate for”可从以下证据开始分析：# 4.2 Different Abstractions of Questions Representations From Table 1, we can see that different parts of a relation could match different contexts of question texts. Usually relation names could match longer phrases in the question and relation words could match short phrases. Yet different words might match phrases of different lengths. As a result, we hope the question representations could also comprise vectors that summarize variou

Representative citation: `paper_ad6cad90ed1d41d6_chunk_8` Different Abstractions of Questions Representations

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“What does KBQA abbreviate for”可从以下证据开始分析：# 4.2 Different Abstractions of Questions Representations From Table 1, we can see that different parts of a relation could match different contexts of question texts. Usually relation names could match longer phrases in the question and relation words could match short phrases. Yet different words might match phrases of different lengths. As a result, we hope the question representations could also comprise vectors that summarize variou

Representative citation: `paper_ad6cad90ed1d41d6_chunk_8` Different Abstractions of Questions Representations

### qasper-val-0020 (paper-qa)

Question: How do they calculate a static embedding for each word?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | n/a | 1.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 1.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“How do they calculate a static embedding for each word?”可从以下证据开始分析：# 3.1 Contextualizing Models The contextualizing models we study in this paper are ELMo, BERT, and GPT-2 $^{1}$ . We choose the base cased version of BERT because it is most comparable to GPT-2 with respect to number of layers and dimensionality. The models we work with are all pre-trained on their respective language modelling tasks. Although ELMo, BERT, and GPT-2 have 2, 12, and 12 hidden layers respectively, 

Representative citation: `paper_f34858cc477d48bb_chunk_5` Contextualizing Models

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“How do they calculate a static embedding for each word?”可从以下证据开始分析：# 3.1 Contextualizing Models The contextualizing models we study in this paper are ELMo, BERT, and GPT-2 $^{1}$ . We choose the base cased version of BERT because it is most comparable to GPT-2 with respect to number of layers and dimensionality. The models we work with are all pre-trained on their respective language modelling tasks. Although ELMo, BERT, and GPT-2 have 2, 12, and 12 hidden layers respectively, 

Representative citation: `paper_f34858cc477d48bb_chunk_5` Contextualizing Models

### qasper-val-0022 (method)

Question: What are the other algorithms tested?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“What are the other algorithms tested?”可从以下证据开始分析：# 3. Materials and Methods The aim of this paper is to evaluate BERT's multilingual model and compare it to other established machine-learning algorithms in a specific task: sensitive data detection and classification in Spanish clinical free text. This section describes the data involved in the experiments and the systems evaluated. Finally, we introduce the experimental setup.

Representative citation: `paper_c23b8432b797410b_chunk_5` Materials and Methods

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“What are the other algorithms tested?”可从以下证据开始分析：# 3. Materials and Methods The aim of this paper is to evaluate BERT's multilingual model and compare it to other established machine-learning algorithms in a specific task: sensitive data detection and classification in Spanish clinical free text. This section describes the data involved in the experiments and the systems evaluated. Finally, we introduce the experimental setup. [C1]

Representative citation: `paper_c23b8432b797410b_chunk_5` Materials and Methods

### qasper-val-0024 (dataset)

Question: What are the clinical datasets used in the paper?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| baseline-current | 0.6667 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.6667 | 1.0000 | n/a | 0.0000 | n/a |  |

**baseline-current answer preview:**

根据已导入文献中最相关的片段，问题“What are the clinical datasets used in the paper?”可从以下证据开始分析：# 3.3.1. Experiment A: NUBES-PHI In this experiment set, we evaluate all the systems presented in Section 3.2., namely, the rule-based baseline, the CRF classifier, the spaCy entity tagger, and BERT. The evaluation comprises three scenarios of increasing difficulty: <table><tr><td></td><td colspan="3">Detection</td><td colspan="3">Classification (relaxed)</td><td colspan="3">Classification...

Representative citation: `paper_c23b8432b797410b_chunk_16` Experiment A: NUBES-PHI

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“What are the clinical datasets used in the paper?”可从以下证据开始分析：# 3.3.1. Experiment A: NUBES-PHI In this experiment set, we evaluate all the systems presented in Section 3.2., namely, the rule-based baseline, the CRF classifier, the spaCy entity tagger, and BERT. The evaluation comprises three scenarios of increasing difficulty: <table><tr><td></td><td colspan="3">Detection</td><td colspan="3">Classification (relaxed)</td><td colspan="3">Classification... [C1]

Representative citation: `paper_c23b8432b797410b_chunk_16` Experiment A: NUBES-PHI
