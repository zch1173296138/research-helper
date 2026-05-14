# RAG A/B Evaluation Report

## Run Configuration

- Cases: `evals\rag_ab\qasper_validation_local_subset.jsonl`
- Baseline: `old-code-api`
- Comparison: `current-evidence`
- Mode: `in-process`
- Current API URL: `n/a`
- Old-code API URL: `http://127.0.0.1:8001`
- Deterministic local: `True`
- LLM judge: `False`
- top_k: `8`
- Output directory: `evals/rag_ab/runs/qasper_old_vs_current`
- Case file sha256: `2587cca802ce7a459608757b4210d6ef001fe6b978ee424f6d9c903edf2fe7cd`
- Timestamp: `2026-05-14T06:46:30.319110+00:00`
- Git revision: `c6697200cb09a73fcf21ab06e7cc824461e0c1bc`
- Notes: n/a

## Aggregate Metrics

### old-code-api

| Metric | Value |
| --- | --- |
| `case_count` | 12 |
| `error_count` | 0 |
| `avg_latency_ms` | 12374.5318 |
| `avg_expected_point_coverage` | 0.4722 |
| `missing_evidence_accuracy` | n/a |
| `avg_candidate_recall` | n/a |
| `avg_final_context_recall` | n/a |
| `avg_citation_recall` | n/a |
| `avg_quote_support_recall` | 0.0278 |
| `reference_contamination_rate` | 0.0000 |
| `avg_accepted_evidence_precision` | n/a |
| `avg_accepted_evidence_recall` | n/a |

### current-evidence

| Metric | Value |
| --- | --- |
| `case_count` | 12 |
| `error_count` | 0 |
| `avg_latency_ms` | 67.0996 |
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

**old-code-api**

| Metric | Value |
| --- | --- |
| `case_count` | 4 |
| `error_count` | 0 |
| `avg_latency_ms` | 11740.5068 |
| `avg_expected_point_coverage` | 1.0000 |
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
| `avg_latency_ms` | 137.1362 |
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

**old-code-api**

| Metric | Value |
| --- | --- |
| `case_count` | 3 |
| `error_count` | 0 |
| `avg_latency_ms` | 9481.5417 |
| `avg_expected_point_coverage` | 0.2222 |
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
| `avg_latency_ms` | 59.1247 |
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

**old-code-api**

| Metric | Value |
| --- | --- |
| `case_count` | 5 |
| `error_count` | 0 |
| `avg_latency_ms` | 14617.5458 |
| `avg_expected_point_coverage` | 0.2000 |
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
| `case_count` | 5 |
| `error_count` | 0 |
| `avg_latency_ms` | 15.8552 |
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
| `avg_expected_point_coverage` | 0.4722 | 0.2917 | -0.1805 |
| `missing_evidence_accuracy` | n/a | n/a | n/a |
| `avg_candidate_recall` | n/a | n/a | n/a |
| `avg_final_context_recall` | n/a | n/a | n/a |
| `avg_citation_recall` | n/a | n/a | n/a |
| `avg_quote_support_recall` | 0.0278 | 0.2222 | +0.1944 |
| `avg_accepted_evidence_precision` | n/a | n/a | n/a |
| `avg_accepted_evidence_recall` | n/a | n/a | n/a |
| `reference_contamination_rate` | 0.0000 | 0.0000 | +0.0000 |
| `avg_latency_ms` | 12374.5318 | 67.0996 | -12307.4322 |
| `error_count` | 0 | 0 | +0.0000 |

## Failed Or Weak Cases

| Case | Strategy | Reason |
| --- | --- | --- |
| `qasper-val-0004` | `old-code-api` | expected coverage 0 |
| `qasper-val-0004` | `current-evidence` | expected coverage 0 |
| `qasper-val-0008` | `old-code-api` | expected coverage 0 |
| `qasper-val-0008` | `current-evidence` | expected coverage 0 |
| `qasper-val-0009` | `old-code-api` | expected coverage 0 |
| `qasper-val-0009` | `current-evidence` | expected coverage 0 |
| `qasper-val-0011` | `old-code-api` | expected coverage 0 |
| `qasper-val-0011` | `current-evidence` | expected coverage 0 |
| `qasper-val-0017` | `current-evidence` | expected coverage 0 |
| `qasper-val-0020` | `old-code-api` | expected coverage 0 |
| `qasper-val-0020` | `current-evidence` | expected coverage 0 |
| `qasper-val-0022` | `old-code-api` | expected coverage 0 |
| `qasper-val-0022` | `current-evidence` | expected coverage 0 |

## Case Results

### qasper-val-0003 (dataset)

Question: which datasets did they experiment with?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| old-code-api | 1.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 1.0000 | 1.0000 | n/a | 0.0000 | n/a |  |

**old-code-api answer preview:**

该研究在两个公共数据集上进行了实验，以评估零样本翻译性能 [1]。 **1. Europarl 数据集** * **语言对设置**：以英语为枢纽语言（pivot language），评估了以下三组多平行语料： * 法语-英语-西班牙语 (Fr-En-Es) * 德语-英语-法语 (De-En-Fr) * 罗马尼亚语-英语-德语 (Ro-En-De) [1] * **验证与测试集划分**： * 对于 Fr→Es 和 De→Fr，使用 devtest2006 作为验证集，test2006 作为测试集 [1]。 * 对于远距离语言对 Ro→De，由于缺乏官方验证/测试集，从 newstest2016 中提取了 1,000 个重叠句子作为测试集，并从训练集中分割出 2,000 个句子作为验证集 [1]。 **2. MultiUN 数据集** * **语言设置**：包含四种语言，英语 (En) 为枢纽语言，其他三种语言之间无平行数据 [1]。 * **涉及语言**：英语 (En)、阿拉伯语 (Ar)、西班牙语 (Es) 和俄语 (Ru) [5]。 * **评估方向**：非枢纽语言之间的相互翻译构

Representative citation: `paper_4989cdaf64974840_chunk_11` Setup

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“which datasets did they experiment with?”可从以下证据开始分析：# Setup We evaluate our cross-lingual pre-training based transfer approach against several strong baselines on two public datasets, Europarl (Koehn 2005) and MultiUN (Eisele and Chen 2010), which contain multi-parallel evaluation data to assess the zero-shot performance. In all experiments, we use BLEU as the automatic metric for translation evaluation. $^{1}$ Datasets. The statistics of Europarl and MultiUN corpora are summar

Representative citation: `paper_4989cdaf64974840_chunk_11` Setup

### qasper-val-0004 (paper-qa)

Question: what language pairs are explored?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| old-code-api | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 0.3333 | n/a |  |

**old-code-api answer preview:**

Based on the provided context, the following language pairs and settings are explored: **Europarl Dataset** The study evaluates three pivot settings where English (En) acts as the pivot language. The specific zero-shot translation directions (source → target) are: * **French to Spanish** (Fr → Es) [4] * **German to French** (De → Fr) [4] * **Romanian to German** (Ro → De) [4] **MultiUN Dataset** English (En) is set as the pivot language. It has parallel data with three other languages that do no

Representative citation: `paper_4989cdaf64974840_chunk_2` Introduction

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“what language pairs are explored?”可从以下证据开始分析：# Introduction Although Neural Machine Translation (NMT) has dominated recent research on translation tasks (Wu et al. 2016; Vaswani et al. 2017; Hassan et al. 2018), NMT heavily relies on large-scale parallel data, resulting in poor performance on low-resource or zero-resource language pairs (Koehn and Knowles 2017). Translation between these low-resource languages (e.g., Arabic→Spanish) is usually accomplished with pivoting through

Representative citation: `paper_4989cdaf64974840_chunk_2` Introduction

### qasper-val-0005 (method)

Question: what ner models were evaluated?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| old-code-api | 0.6667 | 1.0000 | n/a | 0.3333 | n/a |  |
| current-evidence | 0.3333 | 1.0000 | n/a | 0.3333 | n/a |  |

**old-code-api answer preview:**

Based on the provided context, the following Named Entity Recognition (NER) models were evaluated: * **Stanford NER**: A Conditional Random Fields (CRF) classifier based on lexical and contextual features [1] [3]. * **spaCy 2.0**: A model utilizing a CNN-based transition system for named entity recognition [1] [3]. * **Char-biLSTM+biLSTM+CRF**: A recurrent model employing bidirectional LSTM cells for character-based feature extraction, combined with another biLSTM for contextual representation a

Representative citation: `paper_18c9a8ee5ba54ec6_chunk_9` V. EXPERIMENTS

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“what ner models were evaluated?”可从以下证据开始分析：# VI. DISCUSSION Table III shows the average scores of evaluated models. The highest F1 score was achieved by the recurrent model using a batch size of 8 and Adam optimizer with an initial learning rate of 0.001. Updating word embeddings during training also noticeably improved the performance. GloVe word vector models of four different sizes (50, 100, 200, and 300) were tested, with vectors of size 50 producing the best results (Table

Representative citation: `paper_18c9a8ee5ba54ec6_chunk_13` VI. DISCUSSION

### qasper-val-0008 (paper-qa)

Question: what are the topics pulled from Reddit?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| old-code-api | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 1.0000 | n/a |  |

**old-code-api answer preview:**

Based on the provided literature, the topics pulled from Reddit for analysis cover a diverse range of domains, primarily categorized by their association with dogmatism levels and user behavior clusters. **General Topic Diversity** * Reddit posts capture discussions across a wide spectrum, including **climate change**, **abortion**, **world news**, **relationship advice**, and the **future of artificial intelligence** [1]. * The training dataset specifically sampled from subreddits focused on **

Representative citation: `paper_966b9c5490524541_chunk_2` Introduction

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“what are the topics pulled from Reddit?”可从以下证据开始分析：# 1 Introduction “I’m supposed to trust the opinion of a MS minion? The people that produced Windows ME, Vista and 8? They don’t even understand people, yet they think they can predict the behavior of new, self-guiding AI?” –anonymous “I think an AI would make it easier for Patients to confide their information because by nature, a robot cannot judge them. Win-win? :D” –anonymous Dogmatism describes the tendency to lay down opi

Representative citation: `paper_966b9c5490524541_chunk_2` Introduction

### qasper-val-0009 (method)

Question: What predictive model do they build?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| old-code-api | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |

**old-code-api answer preview:**

Based on the provided context, the authors build two distinct types of predictive models to analyze dogmatism: **1. Classification Model for Dogmatic Posts** * **Goal:** To classify individual Reddit comments as either "dogmatic" or "non-dogmatic" [4]. * **Algorithm:** They compare several **logistic regression** models [4]. * **Features:** The models utilize unigram bag-of-words (BOW), sentiment signals (SENT), and specific linguistic features (LING) derived from psychological theories [4]. * *

Representative citation: `paper_966b9c5490524541_chunk_16` Conclusion

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“What predictive model do they build?”可从以下证据开始分析：# 1 Introduction “I’m supposed to trust the opinion of a MS minion? The people that produced Windows ME, Vista and 8? They don’t even understand people, yet they think they can predict the behavior of new, self-guiding AI?” –anonymous “I think an AI would make it easier for Patients to confide their information because by nature, a robot cannot judge them. Win-win? :D” –anonymous Dogmatism describes the tendency to lay down opinio

Representative citation: `paper_966b9c5490524541_chunk_2` Introduction

### qasper-val-0011 (paper-qa)

Question: How do they match words before reordering them?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| old-code-api | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |

**old-code-api answer preview:**

基于提供的文献内容，文中**并未描述**在重排序（reordering）之前具体的“单词匹配”（word matching）算法或机制。 文献主要关注的是如何通过**预重排序（pre-ordering）**来调整语序，以解决源语言与辅助语言之间的语序差异，而非描述单词层面的对齐或匹配过程。以下是相关背景信息： * **重排序的目的**：预重排序旨在使辅助语言（如英语，SVO语序）的句子结构与源语言（如印度语言，SOV语序）的语序相匹配，从而确保编码器生成的上下文表示具有一致性 [2] [4]。 * **使用的工具**：研究使用了 **CFILT-preorder** 工具进行英语句子的预重排序 [1]。 * **规则类型**：该工具包含两种配置： * **通用规则（Generic rules）**：适用于所有印度语言 [1]。 * **印地语调优规则（Hindi-tuned rules）**：通过错误分析改进通用规则 [1]。 * **单词翻译方式**：在测试阶段，当没有平行语料库时，源语言句子是通过使用**双语词典（bilingual dictionary）**进行逐词翻译（word

Representative citation: `paper_ee722d8eebe849f9_chunk_7` Experimental Setup

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“How do they match words before reordering them?”可从以下证据开始分析：# 3 Proposed Solution Consider the task of translating for an extremely low-resource language pair. The parallel corpus between the two languages, if available may be too small to train an NMT model. Similar to Zoph et al. (2016), we use transfer learning to overcome data sparsity between the source and the target languages. We choose English as the assisting language in all our experiments. In our resource-scarce scena

Representative citation: `paper_ee722d8eebe849f9_chunk_4` Proposed Solution

### qasper-val-0013 (dataset)

Question: Which dataset(s) do they experiment with?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| old-code-api | 1.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.5000 | 1.0000 | n/a | 0.0000 | n/a |  |

**old-code-api answer preview:**

Based on the provided context, the experiments utilize the following datasets: **Parent Task (English → Hindi)** * **IITB English-Hindi parallel corpus**: Used for training, containing 1.46 million sentences from the training set [1]. * **ILCI English-Hindi parallel corpus**: Used for training, containing 44.7K sentences [1]. * **IITB Dev-set**: A 520-sentence development set from the IITB corpus used for validation [1]. **Child Tasks (Indian Languages → Hindi)** The child tasks involve translat

Representative citation: `paper_ee722d8eebe849f9_chunk_5` Experimental Setup

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“Which dataset(s) do they experiment with?”可从以下证据开始分析：# 4 Experimental Setup In this section, we describe the languages experimented with, datasets used, the network hyperparameters used in our experiments. Languages: We experimented with English → Hindi translation as the parent task. English is the assisting source language. Bengali, Gujarati, Marathi, Malayalam and Tamil are the source languages, and translation from these to Hindi constitute the child tasks. Hindi, Bengali, 

Representative citation: `paper_ee722d8eebe849f9_chunk_5` Experimental Setup

### qasper-val-0016 (dataset)

Question: On which benchmarks they achieve the state of the art?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| old-code-api | 1.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 1.0000 | 1.0000 | n/a | 0.0000 | n/a |  |

**old-code-api answer preview:**

基于提供的文献内容，该研究在以下基准测试中达到了最先进水平（State-of-the-Art, SOTA）： **1. SimpleQuestions (SQ) 基准** * **KBQA 端到端任务**：该方法取得了新的最先进结果。当使用多个关系检测器时，准确率提升至 **78.7%** [1]。 * **关系检测任务**：提出的 HR-BiLSTM 模型在该任务上也超越了之前的最佳基线，准确率达到 **93.3%** [3]。 **2. WebQSP (WQ) 基准** * **KBQA 端到端任务**该方法取得了与最先进水平相当的结果。在使用多检测器配置下，其表现与之前的 SOTA (STAGG) 持平，准确率为 **63.9%** [1]。 * **关系检测任务**：HR-BiLSTM 模型在此任务上同样优于之前的最佳基线，准确率达到 **82.53%** [3]。 **总结** * 论文明确指出，其 KBQA 系统在 **SimpleQuestions**（单关系）和 **WebQSP**（多关系）这两个 QA 基准上均实现了最先进的准确性 [2]。 * 特别是在 Simpl

Representative citation: `paper_ad6cad90ed1d41d6_chunk_20` KBQA End-Task Results

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“On which benchmarks they achieve the state of the art?”可从以下证据开始分析：# 6.3 KBQA End-Task Results Table 3 compares our system with two published baselines (1) STAGG (Yih et al., 2015), the state-of-the-art on WebQSP $^{11}$ and (2) AMPCNN (Yin et al., 2016), the state-of-the-art on SimpleQuestions. Since these two baselines are specially designed/tuned for one particular dataset, they do not generalize well when applied to the other dataset. In order to highlight the effect of diff

Representative citation: `paper_ad6cad90ed1d41d6_chunk_20` KBQA End-Task Results

### qasper-val-0017 (paper-qa)

Question: What does KBQA abbreviate for

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| old-code-api | 1.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |

**old-code-api answer preview:**

**KBQA** abbreviates for **Knowledge Base Question Answering** [1]. It refers to systems that answer questions by retrieving information from Knowledge Base (KB) tuples [1].

Representative citation: `paper_ad6cad90ed1d41d6_chunk_2` Introduction

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“What does KBQA abbreviate for”可从以下证据开始分析：# 4.2 Different Abstractions of Questions Representations From Table 1, we can see that different parts of a relation could match different contexts of question texts. Usually relation names could match longer phrases in the question and relation words could match short phrases. Yet different words might match phrases of different lengths. As a result, we hope the question representations could also comprise vectors that summarize variou

Representative citation: `paper_ad6cad90ed1d41d6_chunk_8` Different Abstractions of Questions Representations

### qasper-val-0020 (paper-qa)

Question: How do they calculate a static embedding for each word?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| old-code-api | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 1.0000 | n/a |  |

**old-code-api answer preview:**

Based on the provided context, static embeddings are calculated from contextualized models using the following method: **Method: First Principal Component (PC)** * For contextualizing models like ELMo, BERT, and GPT-2, a static embedding for a specific word is derived by taking the **first principal component** of that word's contextualized representations within a given layer [2]. * This process involves analyzing the variance in the word's contextualized representations across different contex

Representative citation: `paper_f34858cc477d48bb_chunk_8` Measures of Contextuality

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“How do they calculate a static embedding for each word?”可从以下证据开始分析：# 3.1 Contextualizing Models The contextualizing models we study in this paper are ELMo, BERT, and GPT-2 $^{1}$ . We choose the base cased version of BERT because it is most comparable to GPT-2 with respect to number of layers and dimensionality. The models we work with are all pre-trained on their respective language modelling tasks. Although ELMo, BERT, and GPT-2 have 2, 12, and 12 hidden layers respectively, 

Representative citation: `paper_f34858cc477d48bb_chunk_5` Contextualizing Models

### qasper-val-0022 (method)

Question: What are the other algorithms tested?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| old-code-api | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.0000 | 1.0000 | n/a | 0.0000 | n/a |  |

**old-code-api answer preview:**

Based on the provided context, the following algorithms and systems were tested alongside the BERT-based model: * **Baseline System**: A rule-based approach utilizing **regular expressions** and **dictionary look-ups** (gazetteers) for detecting specific categories like dates, ages, and locations [7]. * **spaCy**: This system was used as a competitor in the experiments. In the NUBES-PHI dataset, it was noted as the second-best system in terms of recall, though it performed lower than BERT [6]. *

Representative citation: `paper_c23b8432b797410b_chunk_5` Materials and Methods

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“What are the other algorithms tested?”可从以下证据开始分析：# 3. Materials and Methods The aim of this paper is to evaluate BERT's multilingual model and compare it to other established machine-learning algorithms in a specific task: sensitive data detection and classification in Spanish clinical free text. This section describes the data involved in the experiments and the systems evaluated. Finally, we introduce the experimental setup. [C1]

Representative citation: `paper_c23b8432b797410b_chunk_5` Materials and Methods

### qasper-val-0024 (dataset)

Question: What are the clinical datasets used in the paper?

| Strategy | Expected Coverage | Citation Validity | Final Recall | Quote Recall | Missing OK | Error |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| old-code-api | 1.0000 | 1.0000 | n/a | 0.0000 | n/a |  |
| current-evidence | 0.6667 | 1.0000 | n/a | 0.0000 | n/a |  |

**old-code-api answer preview:**

该论文使用了两个包含西班牙语临床叙事的临床数据集： * **NUBES-PHI**：这是一个由真实医疗报告组成的语料库，其中敏感信息经过人工标注 [2]。由于该语料库不公开，它被用于评估模型在真实数据上的表现 [4]。 * **MEDDOCAN 2019 shared task dataset**：这是 MEDDOCAN（Medical Document Anonymization）共享任务竞赛的数据集 [6]。由于 NUBES-PHI 不可公开获取，该数据集被用于将基于 BERT 的模型与其他已发表系统进行对比 [4]。 这两个数据集均包含纯文本形式的临床叙事及其对应的敏感信息手动标注，并转换为 BIO 序列表示方案以输入算法 [1]。

Representative citation: `paper_c23b8432b797410b_chunk_6` Data

**current-evidence answer preview:**

根据已导入文献中最相关的片段，问题“What are the clinical datasets used in the paper?”可从以下证据开始分析：# 3.3.1. Experiment A: NUBES-PHI In this experiment set, we evaluate all the systems presented in Section 3.2., namely, the rule-based baseline, the CRF classifier, the spaCy entity tagger, and BERT. The evaluation comprises three scenarios of increasing difficulty: <table><tr><td></td><td colspan="3">Detection</td><td colspan="3">Classification (relaxed)</td><td colspan="3">Classification... [C1]

Representative citation: `paper_c23b8432b797410b_chunk_16` Experiment A: NUBES-PHI
