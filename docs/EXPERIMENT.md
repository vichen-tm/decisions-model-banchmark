# Experiment conditions

## Date and route

The main campaign ran on October 14, 2026 UTC; its completion falls on October 15 in Europe/Warsaw. Requests used **OpenRouter**, endpoint `https://openrouter.ai/api/alpha/decisions`, with one pinned provider and `allow_fallbacks=false`.

`data/routes.json` records exact model identifiers, providers, and expected returned versions. Individual versions are dated September 17 through October 9, 2026. Results describe these routes and this workload.

## Sample

| Dataset | English tasks per pass | English passes |
|---|---:|---:|
| AG News | 200 | 5 |
| Banking77 | 200 | 5 |
| SST-2 | 200 | 5 |
| SST-5 | 200 | 5 |
| Emotion | 200 | 5 |
| BoolQ | 200 | 5 |
| XNLI | 150 | 5 |
| Typed Decisions | 400 | 5 |
| ProofWriter | 300 | 5 |

Typed Decisions has five questions per task. One English pass contains 2,050 requests and 3,650 decisions per model. Ukrainian, Arabic, Spanish, and Chinese each add one XNLI/ProofWriter pass: 450 requests per language/model.

Final corpora are english-v2 and languages-v3. The base sampling seed is 0; ProofWriter uses 20261014. Source rows, theories, splits, and option order are preserved. Shards are separated by dataset; translations retain hashes of original and translated content.

## Concurrency and repeats

Provider concurrency varied among 1, 2, 4, and 8. Both Drex models shared DeepInfra. The actual limit, where recorded, is in each response's execution metadata. Technically failed requests were rerun; this package contains the selected final responses.

No additional paid model requests were made while preparing this package.

## Measurements

- Latency is full HTTP request–response time, including network and OpenRouter overhead. Client slot wait is recorded separately where available.
- The sum of reported costs for accepted responses is **$3.11716813**.
- Pass comparisons reuse the same tasks. Five passes measure repeatability, not five times as many independent examples.
- Corpus preparation used Python 3.12.13 with pinned libraries. Portable standard-library reproduction and acceptance were checked on Python 3.14.

## Package scope

The working data excludes pilots, route-availability probes, separate EN/ES translation diagnostics, earlier corpora, account/balance information, and internal discussion logs. Final responses and useful synthetic algorithm checks are retained.
