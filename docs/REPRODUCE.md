# Offline reproduction

## Main workflow

Extract the package anywhere. Python 3.10+ is required. No original research directory or API key is needed.

```sh
cd /path/to/decision-benchmark-publication
python3 -m decision_benchmark verify-data
python3 -m decision_benchmark reproduce --output /tmp/decision-results
python3 -m decision_benchmark verify-results --output /tmp/decision-results
```

`verify-data` checks the complete file inventory, hashes, response bodies, joins between requests/tasks/routes, and the full model × task × pass × language population.

`reproduce` scores all 200,500 decisions and builds campaign statistics, 60 confidence curves, 60 category scores, and 10 overall scores. It reads only `data/`; reference tables do not participate in calculation.

`verify-results` compares fresh output with the saved research reference. Small floating-point summation differences are reported. A mismatch fails the command.

## Full acceptance with networking blocked

```sh
python3 tools/acceptance.py --output /tmp/decision-acceptance --reproduce
```

The process blocks network connections, runs the tests, compares every raw response with the pinned 1.2.0 reference scorer, and performs a fresh reproduction. It writes `acceptance.json` to the chosen directory. Test temporary files stay outside the package.

## Simulations

```sh
python3 -m decision_benchmark simulate --output /tmp/confidence-simulations.json
```

The suite includes 51 synthetic cases, 60 real curves, 18 relationships between examples, random confidence, leakage of identical repeats across splits, and splitting by original task. Seeds are fixed. Diagnostics use 400 repetitions by default; `--repetitions` changes that count.

The diagnostic expectation that correcting an answer must never introduce a newly retained error is not always satisfied. The report keeps that counterexample visible; tests assert the agreed J behavior.

## Inputs, references, and output integrity

`results/` contains the ready-made output. `tests/golden/` contains the independent research reference. To check determinism, compare SHA-256 hashes from two fresh reproductions; gzip headers are fixed.

Use a new, empty output directory. Reproduction rejects protected input locations and does not overwrite existing results. `complete.json` is written last and hashes every generated file. Verification checks this marker, the full generated file set, required fields, unique rows, language results, and prediction stability.

Manifests detect corruption relative to a trusted manifest. They are not an author signature; verify the archive SHA-256 obtained separately when transferring the package.
