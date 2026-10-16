# Package verification

Verified on October 16, 2026 using Python 3.14.

| Check | Result |
|---|---|
| Data inventory | 3,850 tasks, 38,500 distinct request bodies, 120,500 accepted responses |
| Active tests | 55 passing |
| Raw scoring | 120,500 responses / 200,500 decisions match the pinned 1.2.0 scorer |
| Current ranking | All 10 overall and 60 category results reproduced |
| Numeric accuracy | Maximum deviation 1.865174681370263e−14; tolerance 1e−10 |
| Portability | Full acceptance from a separate copy with networking blocked |
| Custom data | JSONL, duplicate IDs, invalid formats, and end-to-end sending/scoring with a local transport tested |
| Bundled data | 200 AG News tasks prepared with one command, without sending |
| Secrets | Allowlisted export and expanded-content scan |

The machine-readable acceptance record is `results/verification.json`.

Runner tests cover resume without resending accepted responses, shared provider limits, queue stopping on exceptions, explicit retries, unknown outcomes, competing owners, and repeated Ctrl+C. Corrupt hashes and altered plan bodies are rejected before sending. Result verification detects missing fields and duplicate rows.

The one-command runner was tested with a local substitute for OpenRouter; packaging made no paid API calls. Synthetic tests retain the known J edge case of exchanging 18 clean answers for 19 correct answers and one error.

The English documentation update preserves frozen benchmark data and numeric results. Generated table labels and the illustrative custom dataset are in English; benchmark tasks and raw answers remain in their original languages.
