# Evidence Failure Analysis

- Input: `evals\rag_ab\runs\latest\case_results.jsonl`
- Rows: `24`

## Stage Counts

| Failure stage | Count |
| --- | ---: |
| `citation_selection_missed_gold` | 12 |
| `evidence_rejected_gold` | 2 |
| `final_context_truncated_gold` | 0 |
| `not_applicable` | 0 |
| `ok` | 9 |
| `retrieval_miss` | 1 |

## Rows

| Case | Strategy | Stage | Gold positions | Final hits | Citation hits | Final count | Citation count |
| --- | --- | --- | --- | --- | --- | ---: | ---: |
| `qasper-val-0003` | `current-evidence` | `ok` | `paper_4989cdaf64974840_chunk_11`=1 | `paper_4989cdaf64974840_chunk_11` | `paper_4989cdaf64974840_chunk_11` | 8 | 3 |
| `qasper-val-0003` | `old-code-api` | `ok` | `paper_4989cdaf64974840_chunk_11`=1 | `paper_4989cdaf64974840_chunk_11` | `paper_4989cdaf64974840_chunk_11` | 8 | 3 |
| `qasper-val-0004` | `current-evidence` | `citation_selection_missed_gold` | `paper_4989cdaf64974840_chunk_11`=7 | `paper_4989cdaf64974840_chunk_11` |  | 8 | 3 |
| `qasper-val-0004` | `old-code-api` | `citation_selection_missed_gold` | `paper_4989cdaf64974840_chunk_11`=7 | `paper_4989cdaf64974840_chunk_11` |  | 8 | 3 |
| `qasper-val-0005` | `current-evidence` | `citation_selection_missed_gold` | `paper_18c9a8ee5ba54ec6_chunk_9`=6, `paper_18c9a8ee5ba54ec6_chunk_10`=8 | `paper_18c9a8ee5ba54ec6_chunk_9`, `paper_18c9a8ee5ba54ec6_chunk_10` |  | 8 | 3 |
| `qasper-val-0005` | `old-code-api` | `citation_selection_missed_gold` | `paper_18c9a8ee5ba54ec6_chunk_9`=6, `paper_18c9a8ee5ba54ec6_chunk_10`=8 | `paper_18c9a8ee5ba54ec6_chunk_9`, `paper_18c9a8ee5ba54ec6_chunk_10` |  | 8 | 3 |
| `qasper-val-0008` | `current-evidence` | `ok` | `paper_966b9c5490524541_chunk_3`=2, `paper_966b9c5490524541_chunk_9`=- | `paper_966b9c5490524541_chunk_3` | `paper_966b9c5490524541_chunk_3` | 8 | 3 |
| `qasper-val-0008` | `old-code-api` | `ok` | `paper_966b9c5490524541_chunk_3`=2, `paper_966b9c5490524541_chunk_9`=- | `paper_966b9c5490524541_chunk_3` | `paper_966b9c5490524541_chunk_3` | 8 | 3 |
| `qasper-val-0009` | `current-evidence` | `citation_selection_missed_gold` | `paper_966b9c5490524541_chunk_8`=4 | `paper_966b9c5490524541_chunk_8` |  | 8 | 3 |
| `qasper-val-0009` | `old-code-api` | `citation_selection_missed_gold` | `paper_966b9c5490524541_chunk_8`=4 | `paper_966b9c5490524541_chunk_8` |  | 8 | 3 |
| `qasper-val-0011` | `current-evidence` | `citation_selection_missed_gold` | `paper_ee722d8eebe849f9_chunk_7`=5 | `paper_ee722d8eebe849f9_chunk_7` |  | 8 | 3 |
| `qasper-val-0011` | `old-code-api` | `citation_selection_missed_gold` | `paper_ee722d8eebe849f9_chunk_7`=5 | `paper_ee722d8eebe849f9_chunk_7` |  | 8 | 3 |
| `qasper-val-0013` | `current-evidence` | `ok` | `paper_ee722d8eebe849f9_chunk_5`=1 | `paper_ee722d8eebe849f9_chunk_5` | `paper_ee722d8eebe849f9_chunk_5` | 8 | 3 |
| `qasper-val-0013` | `old-code-api` | `ok` | `paper_ee722d8eebe849f9_chunk_5`=1 | `paper_ee722d8eebe849f9_chunk_5` | `paper_ee722d8eebe849f9_chunk_5` | 8 | 3 |
| `qasper-val-0016` | `current-evidence` | `ok` | `paper_ad6cad90ed1d41d6_chunk_20`=1, `paper_ad6cad90ed1d41d6_chunk_18`=3 | `paper_ad6cad90ed1d41d6_chunk_20`, `paper_ad6cad90ed1d41d6_chunk_18` | `paper_ad6cad90ed1d41d6_chunk_20`, `paper_ad6cad90ed1d41d6_chunk_18` | 8 | 3 |
| `qasper-val-0016` | `old-code-api` | `ok` | `paper_ad6cad90ed1d41d6_chunk_20`=1, `paper_ad6cad90ed1d41d6_chunk_18`=7 | `paper_ad6cad90ed1d41d6_chunk_20`, `paper_ad6cad90ed1d41d6_chunk_18` | `paper_ad6cad90ed1d41d6_chunk_20` | 8 | 3 |
| `qasper-val-0017` | `current-evidence` | `citation_selection_missed_gold` | `paper_ad6cad90ed1d41d6_chunk_2`=5 | `paper_ad6cad90ed1d41d6_chunk_2` |  | 8 | 3 |
| `qasper-val-0017` | `old-code-api` | `citation_selection_missed_gold` | `paper_ad6cad90ed1d41d6_chunk_2`=5 | `paper_ad6cad90ed1d41d6_chunk_2` |  | 8 | 3 |
| `qasper-val-0020` | `current-evidence` | `citation_selection_missed_gold` | `paper_f34858cc477d48bb_chunk_15`=5 | `paper_f34858cc477d48bb_chunk_15` |  | 8 | 3 |
| `qasper-val-0020` | `old-code-api` | `ok` | `paper_f34858cc477d48bb_chunk_15`=3 | `paper_f34858cc477d48bb_chunk_15` | `paper_f34858cc477d48bb_chunk_15` | 8 | 3 |
| `qasper-val-0022` | `current-evidence` | `evidence_rejected_gold` | `paper_c23b8432b797410b_chunk_12`=-, `paper_c23b8432b797410b_chunk_13`=- |  |  | 8 | 3 |
| `qasper-val-0022` | `old-code-api` | `retrieval_miss` | `paper_c23b8432b797410b_chunk_12`=-, `paper_c23b8432b797410b_chunk_13`=- |  |  | 8 | 3 |
| `qasper-val-0024` | `current-evidence` | `evidence_rejected_gold` | `paper_c23b8432b797410b_chunk_6`=-, `paper_c23b8432b797410b_chunk_7`=- |  |  | 8 | 3 |
| `qasper-val-0024` | `old-code-api` | `citation_selection_missed_gold` | `paper_c23b8432b797410b_chunk_6`=6, `paper_c23b8432b797410b_chunk_7`=- | `paper_c23b8432b797410b_chunk_6` |  | 8 | 3 |
