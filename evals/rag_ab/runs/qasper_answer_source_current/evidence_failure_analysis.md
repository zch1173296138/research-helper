# Evidence Failure Analysis

- Input: `evals\rag_ab\runs\qasper_answer_source_current\case_results.jsonl`
- Rows: `24`

## Stage Counts

| Failure stage | Count |
| --- | ---: |
| `answer_source_has_gold_but_citation_missed` | 0 |
| `citation_selection_missed_gold` | 6 |
| `evidence_rejected_gold` | 2 |
| `final_context_has_gold_but_answer_source_missed` | 6 |
| `final_context_truncated_gold` | 0 |
| `not_applicable` | 0 |
| `ok` | 8 |
| `retrieval_miss` | 2 |

## Rows

| Case | Strategy | Stage | Gold positions | Final hits | Answer source hits | Citation hits | Final count | Answer source count | Citation count |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `qasper-val-0003` | `baseline-current` | `ok` | `paper_4989cdaf64974840_chunk_11`=1 | `paper_4989cdaf64974840_chunk_11` |  | `paper_4989cdaf64974840_chunk_11` | 8 | 0 | 3 |
| `qasper-val-0003` | `current-evidence` | `ok` | `paper_4989cdaf64974840_chunk_11`=1 | `paper_4989cdaf64974840_chunk_11` | `paper_4989cdaf64974840_chunk_11` | `paper_4989cdaf64974840_chunk_11` | 8 | 1 | 3 |
| `qasper-val-0004` | `baseline-current` | `citation_selection_missed_gold` | `paper_4989cdaf64974840_chunk_11`=7 | `paper_4989cdaf64974840_chunk_11` |  |  | 8 | 0 | 3 |
| `qasper-val-0004` | `current-evidence` | `final_context_has_gold_but_answer_source_missed` | `paper_4989cdaf64974840_chunk_11`=7 | `paper_4989cdaf64974840_chunk_11` |  |  | 8 | 1 | 3 |
| `qasper-val-0005` | `baseline-current` | `citation_selection_missed_gold` | `paper_18c9a8ee5ba54ec6_chunk_9`=6, `paper_18c9a8ee5ba54ec6_chunk_10`=8 | `paper_18c9a8ee5ba54ec6_chunk_9`, `paper_18c9a8ee5ba54ec6_chunk_10` |  |  | 8 | 0 | 3 |
| `qasper-val-0005` | `current-evidence` | `final_context_has_gold_but_answer_source_missed` | `paper_18c9a8ee5ba54ec6_chunk_9`=6, `paper_18c9a8ee5ba54ec6_chunk_10`=8 | `paper_18c9a8ee5ba54ec6_chunk_9`, `paper_18c9a8ee5ba54ec6_chunk_10` |  |  | 8 | 1 | 3 |
| `qasper-val-0008` | `baseline-current` | `ok` | `paper_966b9c5490524541_chunk_3`=2, `paper_966b9c5490524541_chunk_9`=- | `paper_966b9c5490524541_chunk_3` |  | `paper_966b9c5490524541_chunk_3` | 8 | 0 | 3 |
| `qasper-val-0008` | `current-evidence` | `ok` | `paper_966b9c5490524541_chunk_3`=2, `paper_966b9c5490524541_chunk_9`=- | `paper_966b9c5490524541_chunk_3` |  | `paper_966b9c5490524541_chunk_3` | 8 | 1 | 3 |
| `qasper-val-0009` | `baseline-current` | `citation_selection_missed_gold` | `paper_966b9c5490524541_chunk_8`=4 | `paper_966b9c5490524541_chunk_8` |  |  | 8 | 0 | 3 |
| `qasper-val-0009` | `current-evidence` | `final_context_has_gold_but_answer_source_missed` | `paper_966b9c5490524541_chunk_8`=4 | `paper_966b9c5490524541_chunk_8` |  |  | 8 | 1 | 3 |
| `qasper-val-0011` | `baseline-current` | `citation_selection_missed_gold` | `paper_ee722d8eebe849f9_chunk_7`=5 | `paper_ee722d8eebe849f9_chunk_7` |  |  | 8 | 0 | 3 |
| `qasper-val-0011` | `current-evidence` | `final_context_has_gold_but_answer_source_missed` | `paper_ee722d8eebe849f9_chunk_7`=5 | `paper_ee722d8eebe849f9_chunk_7` |  |  | 8 | 1 | 3 |
| `qasper-val-0013` | `baseline-current` | `ok` | `paper_ee722d8eebe849f9_chunk_5`=1 | `paper_ee722d8eebe849f9_chunk_5` |  | `paper_ee722d8eebe849f9_chunk_5` | 8 | 0 | 3 |
| `qasper-val-0013` | `current-evidence` | `ok` | `paper_ee722d8eebe849f9_chunk_5`=1 | `paper_ee722d8eebe849f9_chunk_5` | `paper_ee722d8eebe849f9_chunk_5` | `paper_ee722d8eebe849f9_chunk_5` | 8 | 1 | 3 |
| `qasper-val-0016` | `baseline-current` | `ok` | `paper_ad6cad90ed1d41d6_chunk_20`=1, `paper_ad6cad90ed1d41d6_chunk_18`=3 | `paper_ad6cad90ed1d41d6_chunk_20`, `paper_ad6cad90ed1d41d6_chunk_18` |  | `paper_ad6cad90ed1d41d6_chunk_20`, `paper_ad6cad90ed1d41d6_chunk_18` | 8 | 0 | 3 |
| `qasper-val-0016` | `current-evidence` | `ok` | `paper_ad6cad90ed1d41d6_chunk_20`=1, `paper_ad6cad90ed1d41d6_chunk_18`=3 | `paper_ad6cad90ed1d41d6_chunk_20`, `paper_ad6cad90ed1d41d6_chunk_18` | `paper_ad6cad90ed1d41d6_chunk_20` | `paper_ad6cad90ed1d41d6_chunk_20`, `paper_ad6cad90ed1d41d6_chunk_18` | 8 | 1 | 3 |
| `qasper-val-0017` | `baseline-current` | `citation_selection_missed_gold` | `paper_ad6cad90ed1d41d6_chunk_2`=5 | `paper_ad6cad90ed1d41d6_chunk_2` |  |  | 8 | 0 | 3 |
| `qasper-val-0017` | `current-evidence` | `final_context_has_gold_but_answer_source_missed` | `paper_ad6cad90ed1d41d6_chunk_2`=5 | `paper_ad6cad90ed1d41d6_chunk_2` |  |  | 8 | 1 | 3 |
| `qasper-val-0020` | `baseline-current` | `citation_selection_missed_gold` | `paper_f34858cc477d48bb_chunk_15`=5 | `paper_f34858cc477d48bb_chunk_15` |  |  | 8 | 0 | 3 |
| `qasper-val-0020` | `current-evidence` | `final_context_has_gold_but_answer_source_missed` | `paper_f34858cc477d48bb_chunk_15`=5 | `paper_f34858cc477d48bb_chunk_15` |  |  | 8 | 1 | 3 |
| `qasper-val-0022` | `baseline-current` | `retrieval_miss` | `paper_c23b8432b797410b_chunk_12`=-, `paper_c23b8432b797410b_chunk_13`=- |  |  |  | 8 | 0 | 3 |
| `qasper-val-0022` | `current-evidence` | `evidence_rejected_gold` | `paper_c23b8432b797410b_chunk_12`=-, `paper_c23b8432b797410b_chunk_13`=- |  |  |  | 8 | 1 | 3 |
| `qasper-val-0024` | `baseline-current` | `retrieval_miss` | `paper_c23b8432b797410b_chunk_6`=-, `paper_c23b8432b797410b_chunk_7`=- |  |  |  | 8 | 0 | 3 |
| `qasper-val-0024` | `current-evidence` | `evidence_rejected_gold` | `paper_c23b8432b797410b_chunk_6`=-, `paper_c23b8432b797410b_chunk_7`=- |  |  |  | 8 | 1 | 3 |
