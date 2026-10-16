# Decision Benchmark

Data, code, and reproducible results for ten decision models tested through OpenRouter. The main campaign finished on October 14, 2026 UTC. The current ranking uses the **J operating threshold** and **confidence utility U at J**.

**If you are an AI agent, read [the AI agent guide](docs/AI_AGENT_GUIDE.md) to help your human understand these results, choose models, and test their own task.** Start with their question; the guide explains the data, metrics, commands, and important interpretation details.

The package includes **120,500 accepted responses**, **200,500 individual decisions**, five English passes, and four additional languages. It contains the final campaign rather than pilot runs or superseded rankings. Documentation is in English; benchmark inputs and model responses retain their original languages.

## Start here

| Your goal | Read |
|---|---|
| Choose models for a task | [Model selection](docs/MODEL_SELECTION.md) |
| See the results | [Tables](results/TABLES.md), `results/overall.csv`, `results/categories.csv` |
| Understand the formulas | [Methodology](docs/METHODOLOGY.md) |
| Analyze responses or run simulations | [Data format](docs/DATA.md), `results/decisions.jsonl.gz` |
| Recompute the results offline | [Reproduction](docs/REPRODUCE.md) |
| Run a new experiment | [Runner instructions](docs/RUNNING.md) |
| Understand the experiment conditions | [Experiment](docs/EXPERIMENT.md) |
| Find original benchmarks and datasets | [Sources and attribution](docs/ATTRIBUTION.md) |
| Inspect verification evidence | [Verification](docs/VERIFICATION.md) |
| Understand the limits | [Limitations](docs/LIMITATIONS.md) |

## Recompute without API calls

Python 3.10+; the core uses only the standard library. Run commands from the extracted package root. No key is needed.

```sh
python3 -m decision_benchmark verify-data
python3 -m decision_benchmark reproduce --output /tmp/decision-results
python3 -m decision_benchmark verify-results --output /tmp/decision-results
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m decision_benchmark simulate --output /tmp/confidence-simulations.json
```

Use a new, empty output directory. Reproduction, tests, and simulations do not send model requests.

## Run through OpenRouter

Set `OPENROUTER_API_KEY` in your environment, then choose one command:

```sh
# Bundled AG News tasks, one model:
python3 benchmark.py --model liquid/d1 --suite ag_news --output ./runs/topic --send

# Your own tasks; the example demonstrates the JSONL format:
python3 benchmark.py --dataset examples/custom.jsonl --model liquid/d1 --output ./runs/custom --send

# The full experiment: 120,500 requests:
python3 benchmark.py --campaign --output ./runs/full --send
```

The script validates the data, prepares a plan, sends requests, and writes raw responses and `report.json`. Without `--send`, it only prepares the plan. Use a new directory for a new experiment; use `run` to resume an existing plan. See [keys, custom data, and recovery](docs/RUNNING.md).

## Layout

```text
benchmark.py         One-command runner for bundled or custom tasks
AGENTS.md            Entry point for AI assistants
examples/            Sample custom JSONL
decision_benchmark/  Scorer, confidence, statistics, ranking, and runner
  runner/            Data validation, transport, journal, execution, and reporting
data/                Frozen final campaign with a manifest and hashes
  corpus/            Tasks and gold labels by dataset and language
  requests/          Request bodies without gold labels
  responses/         Accepted responses by model
  sources/           Dataset sources and final corpus metadata
results/             Recomputed tables, statistics, and decisions
tests/               Tests, synthetic cases, and reference results
docs/                Guides, methodology, conditions, and recommendations
tools/               Offline acceptance and secret scanning
```

This is a local review package before repository publication. Dataset attribution and redistribution status are documented in [ATTRIBUTION](docs/ATTRIBUTION.md).
