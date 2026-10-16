# Code organization

Each rule and external effect has a specific owner.

| Module | Responsibility |
|---|---|
| archive | Shard loading, hashes, complete inventory, and data joins |
| encoding | Canonical JSON encoding and durable atomic writes |
| scoring | Deterministic choice/noul/score evaluation, version 1.2.0 |
| confidence | Threshold enumeration and exact J/U, without file or network access |
| campaign_metrics | Statistical metrics over decisions |
| rating | Category slice, score scales, weights, and winners |
| analysis | Raw input → scoring → aggregation → output |
| reporting | English tables from calculated ratings |
| simulations | Synthetic cases and noise/shift diagnostics |
| verification | Comparison against independent references |
| runner/dataset | Validation of custom JSONL |
| runner/benchmark | One-command preparation, execution, and report |
| runner/transport | The HTTP/OpenRouter boundary; credentials stay in memory |
| runner/journal | Immutable plans, directory lock, and attempt records |
| runner/execution | Queue, provider limits, retries, and unknown outcomes |
| runner/report | Local evaluation of complete or partial new runs |
| __main__, runner/cli | Command parsing and explicit send opt-in |

Change a confidence formula in confidence and its tests; change ranking scales in rating. Configure a new route in a separate routes file. Transport does not own the model catalog. Attempt storage belongs to journal; retry eligibility belongs to execution.

Only verification reads `tests/golden`. Reproduction derives results from data. The pinned scorer in `tests/fixtures` is an independent test oracle for every raw response.

`benchmark.py` is the one-command entry point. Bundled and custom corpora use the same execution and scoring path. The known J counterexample remains a visible diagnostic.
