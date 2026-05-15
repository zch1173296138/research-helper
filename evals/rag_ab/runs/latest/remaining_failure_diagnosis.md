# Remaining QASPER Failure Diagnosis

Source run: `evals\rag_ab\runs\qasper_claim_sources_answer_linked\case_results.jsonl`

## Summary

| Case | Failure type | Candidate has gold | Accepted has gold | Final has gold | Answer source has gold | Citation has gold | Miss reason | Recommended fix |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `qasper-val-0004` | `claim_selector_missed_gold` | yes | yes | yes | no | no | `claim_score_too_low` | Add lightweight answer-intent term expansion or phrase matching in claim scoring, not citation supplementation. |
| `qasper-val-0011` | `claim_selector_missed_gold` | yes | yes | yes | no | no | `claim_cut_by_max_claims` | Consider a small tie-breaker that reserves a slot for later high-scoring chunks with strong exact-answer terms; keep max_claims unchanged unless separately approved. |
| `qasper-val-0022` | `final_context_missing_gold` | yes | no | no | no | no | `judge_rejected_gold` | Improve evidence ranking/judging diagnostics before claim selection; gold is in candidates but outside the accepted final context. Do not adjust citation selection. |
| `qasper-val-0024` | `final_context_missing_gold` | yes | no | no | no | no | `judge_rejected_gold` | Improve evidence ranking/judging diagnostics before claim selection; gold is in candidates but outside the accepted final context. Do not adjust citation selection. |

## Detailed Rows

### qasper-val-0004

| Field | Value |
| --- | --- |
| failure_type | `claim_selector_missed_gold` |
| question | what language pairs are explored? |
| supporting_chunk_ids | `paper_4989cdaf64974840_chunk_11` |
| candidate_chunk_ids contains gold? | yes |
| accepted_chunk_ids contains gold? | yes |
| final_context_chunk_ids contains gold? | yes |
| answer_source_chunk_ids contains gold? | no |
| citation_chunk_ids contains gold? | no |
| gold evidence decision | `accept` |
| gold support_level | `partial` |
| gold evidence reason | Accepted by ranked fallback. |
| gold_position_in_final_context | {"paper_4989cdaf64974840_chunk_11": 7} |
| gold_best_sentence_score | `40.3333` |
| reason why gold chunk was missed | `claim_score_too_low` |
| reason detail | Gold best sentence scored below the selected claim cutoff under question-token overlap plus decision boost. |
| recommended_fix | Add lightweight answer-intent term expansion or phrase matching in claim scoring, not citation supplementation. |

Supporting quotes:
- For MultiUN corpus, we use four languages: English (En) is set as the pivot language, which has parallel data with other three languages which do not have parallel data between each other. The three languages are Arabic (Ar), Spanish (Es), and Russian (Ru), and mutual translation between themselves constitutes six zero-shot translation direction for evaluation.
- The statistics of Europarl and MultiUN corpora are summarized in Table TABREF18. For Europarl corpus, we evaluate on French-English-Spanish (Fr-En-Es), German-English-French (De-En-Fr) and Romanian-English-German (Ro-En-De), where English acts as the pivot language, its left side is the source language, and its right side is the target language.
- For MultiUN corpus, we use four languages: English (En) is set as the pivot language, which has parallel data with other three languages which do not have parallel data between each other. The three languages are Arabic (Ar), Spanish (Es), and Russian (Ru), and mutual translation between themselves constitutes six zero-shot translation direction for evaluation. We use 80K BPE splits as the vocabulary. Note that all sentences are tokenized by the tokenize.perl script, and we lowercase all data to avoid a large vocabulary for the MultiUN corpus.

Gold best sentence:

For Europarl corpus, we evaluate on French-English-Spanish (Fr-En-Es), German-English-French (De-En-Fr) and Romanian-English-German (Ro-En-De), where English acts as the pivot language, its left side is the source language, and its right side is the target language.

Selected claims:
- `C1` `paper_4989cdaf64974840_chunk_2` score=`40.6667`: 2018), NMT heavily relies on large-scale parallel data, resulting in poor performance on low-resource or zero-resource language pairs (Koehn and Knowles 2017).
- `C2` `paper_4989cdaf64974840_chunk_4` score=`40.6667`: \- Multilingual NMT (MNMT) enables training a single model that supports translation from multiple source languages into multiple target languages, even those unseen language pairs (Firat, Cho, and Bengio 2016; Firat et al.
- `C3` `paper_4989cdaf64974840_chunk_6` score=`40.6667`: The BRLM extends MLM (Lample and Conneau 2019) to pairs of parallel sentences and leverages explicit alignment information obtained by external aligner tool or additional attention layer to encourage word representation alignment across different languages.

Selected claim chunk IDs:

`paper_4989cdaf64974840_chunk_2`, `paper_4989cdaf64974840_chunk_4`, `paper_4989cdaf64974840_chunk_6`

Gold sentence scores:
- `paper_4989cdaf64974840_chunk_11`
  - idx=1 total=40.0 text=0.0: # Setup We evaluate our cross-lingual pre-training based transfer approach against several strong baselines on two public datasets, Europarl (Koehn 2005) and MultiUN (Eisele and Chen 2010), which contain multi-parallel e
  - idx=2 total=40.0 text=0.0: In all experiments, we use BLEU as the automatic metric for translation evaluation.
  - idx=3 total=40.0 text=0.0: $^{1}$ Datasets.
  - idx=4 total=40.0 text=0.0: The statistics of Europarl and MultiUN corpora are summarized in Table 1.
  - idx=5 total=40.3333 text=0.3333: For Europarl corpus, we evaluate on French-English-Spanish (Fr-En-Es), German-English-French (De-En-Fr) and Romanian-English-German (Ro-En-De), where English acts as the pivot language, its left side is the source langua
  - idx=6 total=40.0 text=0.0: We remove the multi-parallel sentences between different training corpora to ensure zero-shot settings.
  - idx=7 total=40.0 text=0.0: We use the devtest2006 as the validation set and the test2006 as the test set for Fr→Es and De→Fr.
  - idx=8 total=40.3333 text=0.3333: For distant language pair Ro→De, we extract 1,000 overlapping sentences from newstest2016 as the test set and the 2,000 overlapping sentences split from the training set as the validation set since there is no official v
  - ... +5 more

### qasper-val-0011

| Field | Value |
| --- | --- |
| failure_type | `claim_selector_missed_gold` |
| question | How do they match words before reordering them? |
| supporting_chunk_ids | `paper_ee722d8eebe849f9_chunk_7` |
| candidate_chunk_ids contains gold? | yes |
| accepted_chunk_ids contains gold? | yes |
| final_context_chunk_ids contains gold? | yes |
| answer_source_chunk_ids contains gold? | no |
| citation_chunk_ids contains gold? | no |
| gold evidence decision | `accept` |
| gold support_level | `partial` |
| gold evidence reason | Accepted by ranked fallback. |
| gold_position_in_final_context | {"paper_ee722d8eebe849f9_chunk_7": 5} |
| gold_best_sentence_score | `40.2` |
| reason why gold chunk was missed | `claim_cut_by_max_claims` |
| reason detail | Gold had a score competitive with selected claims but appeared later in final_context and max_claims=3 cut it off. |
| recommended_fix | Consider a small tie-breaker that reserves a slot for later high-scoring chunks with strong exact-answer terms; keep max_claims unchanged unless separately approved. |

Supporting quotes:
- We use the CFILT-preorder system for reordering English sentences to match the Indian language word order. It contains two re-ordering systems: (1) generic rules that apply to all Indian languages BIBREF17 , and (2) hindi-tuned rules which improve the generic rules by incorporating improvements found through an error analysis of English-Hindi reordering BIBREF28 .
- We use the CFILT-preorder system for reordering English sentences to match the Indian language word order. It contains two re-ordering systems: (1) generic rules that apply to all Indian languages BIBREF17 , and (2) hindi-tuned rules which improve the generic rules by incorporating improvements found through an error analysis of English-Hindi reordering BIBREF28 . These Hindi-tuned rules have been found to improve reordering for many English to Indian language pairs BIBREF29 .

Gold best sentence:

Pre-ordering: We use CFILT-preorder $^{3}$ for pre-reordering English sentences.

Selected claims:
- `C1` `paper_ee722d8eebe849f9_chunk_4` score=`40.4`: <table><tr><td>Before Reordering</td><td>After Reordering</td></tr><tr><td><img src="images/8b823142d78335bf9c31d193aa8ed12331a33d08101cf8ad6678553f7e1bb6e7.jpg"/></td><td><img src="images/d492c8af2f577cc04d3200737b86afb2df7956f19c6de98af9ed683511e0a539.jpg"/></td></tr><tr><td><img...
- `C2` `paper_ee722d8eebe849f9_chunk_3` score=`40.2`: The approach does not show any significant improvements, possibly because the divergence has to be addressed before/during construction of the contextual embeddings in the Bi-LSTM layer.
- `C3` `paper_ee722d8eebe849f9_chunk_2` score=`40.2`: To address the word order divergence, we propose to pre-order the assisting language sentences (SVO) to match the word order of the source language (SOV).

Selected claim chunk IDs:

`paper_ee722d8eebe849f9_chunk_4`, `paper_ee722d8eebe849f9_chunk_3`, `paper_ee722d8eebe849f9_chunk_2`

Gold sentence scores:
- `paper_ee722d8eebe849f9_chunk_7`
  - idx=1 total=40.0 text=0.0: Table 3: Number of UNK tokens generated by each model on the test set.
  - idx=2 total=40.2 text=0.2: Pre-ordering: We use CFILT-preorder $^{3}$ for pre-reordering English sentences.
  - idx=3 total=40.2 text=0.2: It contains two pre-ordering configurations: (1) generic rules (G) that apply to all Indian languages (Ramanathan et al., 2008), and (2) hindi-tuned rules (HT) which improves generic rules by incorporating improvements f
  - idx=4 total=40.0 text=0.0: The Hindi-tuned rules improve translation for other English to Indian language pairs too (Kunchukuttan et al., 2014).

### qasper-val-0022

| Field | Value |
| --- | --- |
| failure_type | `final_context_missing_gold` |
| question | What are the other algorithms tested? |
| supporting_chunk_ids | `paper_c23b8432b797410b_chunk_12`, `paper_c23b8432b797410b_chunk_13` |
| candidate_chunk_ids contains gold? | yes |
| accepted_chunk_ids contains gold? | no |
| final_context_chunk_ids contains gold? | no |
| answer_source_chunk_ids contains gold? | no |
| citation_chunk_ids contains gold? | no |
| gold evidence decision | `reject` |
| gold support_level | `none` |
| gold evidence reason | Outside ranked fallback context. |
| gold_position_in_final_context | {"paper_c23b8432b797410b_chunk_12": null, "paper_c23b8432b797410b_chunk_13": null} |
| gold_best_sentence_score | `0.0` |
| reason why gold chunk was missed | `judge_rejected_gold` |
| reason detail | Gold chunk appears in candidates but is outside ranked fallback context and marked reject/none. |
| recommended_fix | Improve evidence ranking/judging diagnostics before claim selection; gold is in candidates but outside the accepted final context. Do not adjust citation selection. |

Supporting quotes:
- Conditional Random Fields (CRF) BIBREF15 have been extensively used for tasks of sequential nature. In this paper, we propose as one of the competitive baselines a CRF classifier trained with sklearn-crfsuite for Python 3.5 and the following configuration: algorithm = lbfgs; maximum iterations = 100; c1 = c2 = 0.1; all transitions = true; optimise = false.
- spaCy is a widely used NLP library that implements state-of-the-art text processing pipelines, including a sequence-labelling pipeline similar to the one described by strubell2017fast. spaCy offers several pre-trained models in Spanish, which perform basic NLP tasks such as Named Entity Recognition (NER). In this paper, we have trained a new NER model to detect NUBes-PHI labels.
- Conditional Random Fields (CRF) BIBREF15 have been extensively used for tasks of sequential nature. In this paper, we propose as one of the competitive baselines a CRF classifier trained with sklearn-crfsuite for Python 3.5 and the following configuration: algorithm = lbfgs; maximum iterations = 100; c1 = c2 = 0.1; all transitions = true; optimise = false. The features extracted from each token are as follows:

Gold best sentence:

# 3.2.2.

Selected claims:
- `C1` `paper_c23b8432b797410b_chunk_5` score=`40.6667`: Materials and Methods The aim of this paper is to evaluate BERT's multilingual model and compare it to other established machine-learning algorithms in a specific task: sensitive data detection and classification in Spanish clinical free text.
- `C2` `paper_c23b8432b797410b_chunk_30` score=`40.3333`: We have compared this BERT-based sequence labelling against other methods and systems.
- `C5` `paper_c23b8432b797410b_chunk_1` score=`40.6667`: We also compare BERT to other algorithms.

Selected claim chunk IDs:

`paper_c23b8432b797410b_chunk_5`, `paper_c23b8432b797410b_chunk_30`, `paper_c23b8432b797410b_chunk_1`

Gold sentence scores:
- `paper_c23b8432b797410b_chunk_12`
  - idx=1 total=0.0 text=0.0: # 3.2.2.
  - idx=2 total=0.0 text=0.0: CRF Conditional Random Fields (CRF) (Lafferty et al., 2001) have been extensively used for tasks of sequential nature.
  - idx=3 total=0.0 text=0.0: In this paper, we propose as one of the competitive baselines a CRF classifier trained with sklearn-crfsuite $^{3}$ for Python 3.5 and the following configuration: algorithm = lbfgs; maximum iterations = 100; c1 = c2 = 0
  - idx=4 total=0.0 text=0.0: The features extracted from each token are as follows: - prefixes and suffixes of 2 and 3 characters
  - idx=5 total=0.0 text=0.0: the length of the token in characters and the length of the sentence in tokens
  - idx=6 total=0.0 text=0.0: whether the token is all-letters, a number, or a sequence of punctuation marks
  - idx=7 total=0.0 text=0.0: whether the token contains the character '@'
  - idx=8 total=0.0 text=0.0: whether the token is the start or end of the sentence
  - ... +4 more
- `paper_c23b8432b797410b_chunk_13`
  - idx=1 total=0.0 text=0.0: # 3.2.3.
  - idx=2 total=0.0 text=0.0: spaCy spaCy $^{5}$ is a widely used NLP library that implements state-of-the-art text processing pipelines, including a sequence-labelling pipeline similar to the one described by Strubell et al.
  - idx=3 total=0.0 text=0.0: (2017).
  - idx=4 total=0.0 text=0.0: spaCy offers several pre-trained models in Spanish, which perform basic NLP tasks such as Named Entity Recognition (NER).
  - idx=5 total=0.0 text=0.0: In this paper, we have trained a new NER model to detect NUBES-PHI labels.
  - idx=6 total=0.0 text=0.0: For this purpose, the new model uses all the labels of the training corpus coded with its context at sentence level.
  - idx=7 total=0.0 text=0.0: The network optimisation parameters and dropout values are the ones recommended in the documentation for small datasets $^{6}$ .
  - idx=8 total=0.0 text=0.0: Finally, the model is trained using batches of size 64.
  - ... +1 more

### qasper-val-0024

| Field | Value |
| --- | --- |
| failure_type | `final_context_missing_gold` |
| question | What are the clinical datasets used in the paper? |
| supporting_chunk_ids | `paper_c23b8432b797410b_chunk_6`, `paper_c23b8432b797410b_chunk_7` |
| candidate_chunk_ids contains gold? | yes |
| accepted_chunk_ids contains gold? | no |
| final_context_chunk_ids contains gold? | no |
| answer_source_chunk_ids contains gold? | no |
| citation_chunk_ids contains gold? | no |
| gold evidence decision | `reject` |
| gold support_level | `none` |
| gold evidence reason | Outside ranked fallback context. |
| gold_position_in_final_context | {"paper_c23b8432b797410b_chunk_6": null, "paper_c23b8432b797410b_chunk_7": null} |
| gold_best_sentence_score | `0.6667` |
| reason why gold chunk was missed | `judge_rejected_gold` |
| reason detail | Gold chunk appears in candidates but is outside ranked fallback context and marked reject/none. |
| recommended_fix | Improve evidence ranking/judging diagnostics before claim selection; gold is in candidates but outside the accepted final context. Do not adjust citation selection. |

Supporting quotes:
- Two datasets are exploited in this article. Both datasets consist of plain text containing clinical narrative written in Spanish, and their respective manual annotations of sensitive information in BRAT BIBREF13 standoff format.
- NUBes BIBREF4 is a corpus of around 7,000 real medical reports written in Spanish and annotated with negation and uncertainty information.
- In order to avoid confusion between the two corpus versions, we henceforth refer to the version relevant in this paper as NUBes-PHI (from `NUBes with Personal Health Information').

Gold best sentence:

Both datasets consist of plain text containing clinical narrative written in Spanish, and their respective manual annotations of sensitive information in BRAT (Stenetorp et al., 2012) standoff format $^{2}$ .

Selected claims:
- `C1` `paper_c23b8432b797410b_chunk_16` score=`40.3333`: Detecting entity types correctly is important if a system is going to be used to replace sensitive data by fake data of the same type (e.g., random people names).
- `C2` `paper_c23b8432b797410b_chunk_17` score=`40.0`: Experiment B: MEDDOCAN In this experiment set, our BERT implementation is compared to several systems that participated in the MEDDO-CAN challenge: a CRF classifier (Perez et al., 2019), a spaCy entity recogniser (Perez et al., 2019), and NLNDE (Lange et al., 2019), the winner of the shared task and current state of...
- `C3` `paper_c23b8432b797410b_chunk_15` score=`40.6667`: Experimental design We have conducted experiments with BERT in the two datasets of Spanish clinical narrative presented in Section 3.1.

Selected claim chunk IDs:

`paper_c23b8432b797410b_chunk_16`, `paper_c23b8432b797410b_chunk_17`, `paper_c23b8432b797410b_chunk_15`

Gold sentence scores:
- `paper_c23b8432b797410b_chunk_6`
  - idx=1 total=0.0 text=0.0: # 3.1.
  - idx=2 total=0.3333 text=0.3333: Data Two datasets are exploited in this article.
  - idx=3 total=0.6667 text=0.6667: Both datasets consist of plain text containing clinical narrative written in Spanish, and their respective manual annotations of sensitive information in BRAT (Stenetorp et al., 2012) standoff format $^{2}$ .
  - idx=4 total=0.6667 text=0.6667: In order to feed the data to the different algorithms presented in Section 3.2., these datasets were transformed to comply with the commonly used BIO sequence representation scheme (Ramshaw and Marcus, 1999).
- `paper_c23b8432b797410b_chunk_7`
  - idx=1 total=0.0 text=0.0: # 3.1.1.
  - idx=2 total=0.0 text=0.0: NUBES-PHI NUBES (Lima et al., 2019) is a corpus of around 7,000 real medical reports written in Spanish and annotated with negation and uncertainty information.
  - idx=3 total=0.0 text=0.0: Before being published, sensitive information had to be manually annotated and replaced for the corpus to be safely shared.
  - idx=4 total=0.0 text=0.0: In this article, we work with the NUBES version prior to its anonymisation, that is, with the manual annotations of sensitive information.
  - idx=5 total=0.0 text=0.0: It follows that the version we work with is not publicly available and, due to contractual restrictions, we cannot reveal the provenance of the data.
  - idx=6 total=0.0 text=0.0: In order to avoid confusion between the two corpus versions, we henceforth refer to the version relevant in this paper as NUBES-PHI (from ‘NUBES with Personal Health Information’).
  - idx=7 total=0.0 text=0.0: NUBES-PHI consists of 32,055 sentences annotated for 11 different sensitive information categories.
  - idx=8 total=0.0 text=0.0: Overall, it contains 7,818 annotations.
  - ... +7 more
