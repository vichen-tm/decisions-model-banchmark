# Data files and joins

## Counts and units

- 10 models; 12,050 requests per model: 2,050 English tasks × 5 passes, plus 450 tasks × 4 other languages.
- 3,850 task variants: 2,050 EN and 1,800 UK/AR/ES/ZH.
- 38,500 distinct request bodies: model identity is part of the body; repeats reuse it.
- 120,500 accepted responses produce 200,500 decisions. Typed Decisions has five questions per request.
- The ranking slice contains 150,500 decisions with native confidence. Per model: Topic 1,000; Intent 1,000; Sentiment 2,000; Inference 1,350; Decisions 7,000; Proof 2,700.

## Frozen files

`data/manifest.json` records schema version, counts, SHA-256, and byte size. Verification checks the entire data directory: extra, missing, or changed files fail.

`data/corpus/<suite>/<language>.jsonl.gz` contains one task per line:

- `id`, `language`: composite identity;
- `suite`, optional `workflow` and `depth`: task classification;
- `request.state`, `request.questions`: input and questions;
- `gold`: reference answers, never sent to the model;
- `source`: original dataset, split, row, or theory;
- `translation`: original/translation hashes, version, and LLM review status.

`data/requests/<suite>/<language>.jsonl.gz` contains `body_sha256` and `body`. The body has only state, questions, model, and provider. Question and option order is preserved. Encoding is UTF-8 JSON with `ensure_ascii=False`, separators `,` and `:`, no key sorting, and no trailing newline. Canonical re-encoding matches the logged intent hash; a separate wire capture was not recorded.

`data/responses/<model>.jsonl.gz` contains accepted responses:

| Field | Meaning |
|---|---|
| `logical_id` | Logical task identifier from final selection |
| `key` | model, provider, case, repeat, language |
| `body_sha256` | Join to the exact body in requests |
| `raw.response_text` | Response text with numbers and order preserved |
| `raw.body_encoding` | utf8 or base64 for non-UTF8 bytes |
| `raw.body_sha256` | Verifiable response-byte hash |
| `raw.status`, `elapsed_ms`, `received_at`, `attempt` | HTTP status, total request time, receipt time, attempt number |
| `execution` | Start time, queue wait, actual provider concurrency limit where recorded |

## Dataset sources

- `data/sources/datasets.json`: source dataset, retrieval URL, split/config, source size where available, selected count, file hashes, and known licensing metadata. ProofWriter includes the official archive, paper, and selected archive member.
- `data/sources/corpus.json`: final English corpus composition, task/decision counts, and translation languages and datasets.

Task texts, labels, and translations live in `corpus/`; individual records link back to source rows or theories. See the [source table](ATTRIBUTION.md).

## Decision table for analysis

`results/decisions.jsonl.gz` is regenerated from raw. Each row is one decision: request identity, suite/question, type, correctness, prediction, gold, normalized distribution, `confidence` (probability of the selected answer), `native_confidence` (the model's separate confidence), and diagnostic metrics.

J uses **native_confidence**. Do not substitute selected-answer probability. Probability sums may deviate from one by ±0.01; original values remain in raw responses and normalization metadata.

Repeated observations of one task are dependent. Group by original task when separating threshold selection from evaluation; keep its repeats and translations together.

## Streaming example

```python
from decision_benchmark.archive import read_jsonl

for answer in read_jsonl('data/responses/liquid--d1.jsonl.gz'):
    print(answer['key'], answer['raw']['status'])
    break
```

Gzip files use fixed mtime=0; tested reproductions yield identical files. Stream JSONL line by line for large analyses. Preserve benchmark text and response languages when analyzing the archive.
