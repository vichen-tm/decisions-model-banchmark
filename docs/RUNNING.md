# Running a new experiment

The runner uses OpenRouter Decisions API and scorer 1.2.0. It requires Python 3.10+ on macOS/Linux (POSIX file locking).

## One command

Provide the key through `OPENROUTER_API_KEY`. In bash/zsh, enter it without echoing it or placing its value in shell history:

```sh
read -s OPENROUTER_API_KEY
export OPENROUTER_API_KEY
```

After the first command, type the key and press Enter. Then choose a run:

```sh
# Bundled tasks: 200 AG News examples for Liquid
python3 benchmark.py --model liquid/d1 --suite ag_news --output ./runs/topic --send

# Custom JSONL; languages are read from the file
python3 benchmark.py --dataset examples/custom.jsonl --model liquid/d1 --output ./runs/custom --send

# All bundled models and tasks: EN × 5, UK/AR/ES/ZH × 1
python3 benchmark.py --campaign --output ./runs/full --send
```

Repeat `--model`, `--suite`, or `--language` to select several values. `--all-models` selects all configured routes. `--repeats` applies one repeat count to the selected tasks. `--campaign` is a standalone preset for the full 120,500-request composition; do not combine it with dataset/model/language/suite/repeat selection.

`--concurrency` is a shared per-provider limit, default 1. Both Drex models share DeepInfra slots. This default does not reproduce the changing concurrency of the original campaign.

Without `--send`, the script validates data, prepares a plan, and displays the number of requests. To send that prepared plan, use `python3 -m decision_benchmark run --run-dir ./runs/topic --send`. Run `report-run` to inspect it. Each new `benchmark.py` invocation requires a fresh, empty output directory; resume with `run`.

On normal completion, the one-command runner writes `report.json`: accuracy, counts, known accepted cost, and J/U by model/language/suite/question. Raw responses and the plan remain beside it. An incomplete run reports its states and exits with code 2. After an exception, use `report-run` to inspect the saved journal.

## Custom data

Each JSONL line is a task with `id`, `suite`, `language`, `request`, and `gold`. Copy `examples/custom.jsonl` and replace its two English support requests, choices, and labels.

```json
{"id":"001","suite":"my_task","language":"en","request":{"state":{"text":"I cannot sign in"},"questions":{"intent":{"type":"choice","instructions":"Classify the support request","criteria":{"access":"Account access","billing":"Payments"}}}},"gold":{"intent":{"type":"choice","label":"access"}}}
```

Only `request` is sent to the model; `gold` stays local. The id+language pair must be unique. The scorer supports choice, noul, and score; see bundled tasks and [methodology](METHODOLOGY.md) for those contracts. Gzipped JSONL is supported. All rows are validated before sending. Custom suites get their own report groups; the benchmark's category ranking scales are not automatically applied to arbitrary tasks.

The prepared plan freezes the data, routes, gold labels, and a plan hash. Do not edit it. Create a new plan for changed data or routing.

## Separate preparation and sending

```sh
python3 -m decision_benchmark prepare \
  --run-dir /tmp/my-decision-run \
  --model liquid/d1 --suite ag_news --language en \
  --repeats 1 --concurrency 1
python3 -m decision_benchmark run --run-dir /tmp/my-decision-run --send
python3 -m decision_benchmark report-run --run-dir /tmp/my-decision-run
```

This prepares 200 tasks. Omitting `--suite` selects all available datasets for the chosen language. Non-English bundled tasks are XNLI and ProofWriter. The original composition uses five EN repeats and one for each other language; the one-command `--campaign` preset implements it.

## Routes and credentials

`data/routes.json` pins a provider and expected returned model version. A changed version is not accepted under the old identity. For a new version, create a routes JSON containing model, provider.only, provider.allow_fallbacks=false, expected_provider, and expected_version; pass `--routes` to `benchmark.py` or `prepare` with a new output directory.

Sending requires `--send`. The key is read from the environment and not saved. Connections are direct by default; `--allow-env-proxy` explicitly permits environment proxies. HTTP redirects are disabled. There is no client execution timeout; the service can return its own error.

## Reports and durable records

`report-run` shows task states, valid decision counts, accuracy by model/language/suite/question, and J/U where native confidence exists. A partial run has `complete=false` and `valid_only_accuracy`; do not report this as full-population accuracy.

Responses are stored in `attempts/<task_id>/<attempt>/response.json`. The runner durably records intent before sending, then the received response. Records have checksums and prior attempts are not overwritten. Only one process can own a run directory.

## Resume and retry

Resume skips accepted tasks. A technical failure stops new sends; already active requests finish and save responses. Pending tasks stay queued.

For received HTTP 429/500/502/503, explicitly permit one retry per eligible task:

```sh
python3 -m decision_benchmark run --run-dir /tmp/my-decision-run --send --retry-technical
```

There is no hidden retry loop. Authorization, format, version, and provider failures are not retried automatically.

An interrupted connection, intent without a response, or HTTP 408/504/520/522/524 is an unknown outcome. Inspect the provider state before authorizing a retry; it may be billed again.

```sh
python3 -m decision_benchmark resolve-unknown \
  --run-dir /tmp/my-decision-run --task-id TASK_ID --action retry
python3 -m decision_benchmark run --run-dir /tmp/my-decision-run --send
```

Use `--action abandon` instead to preserve the unresolved volume in the report and prohibit another send for that task. Original records stay intact.

After repairing a failed condition such as authorization, use `resolve-failed --run-dir ... --task-id ... --action retry`, then `run --send`. For a changed route, prepare a new plan. Resolution decisions are recorded.

Ctrl+C stops new sends. Active HTTP calls finish and save their responses while the directory lock remains held, including after repeated Ctrl+C. With no client deadline an active call may keep waiting. A forced process termination leaves any unrecorded outcome unknown.

## Corruption and verification

An unknown run path is rejected without creating a directory. Corrupt JSON or a checksum mismatch stops execution. Restore a verified backup; do not delete the attempt to trigger a retry. If recovery is impossible, preserve the directory and reconcile possibly executed requests before starting again.

Local tests cover storage/resume, explicit send opt-in, shared provider limits, retries, unknown outcomes, and custom-data execution with a fake transport. No paid calls were made while preparing this package.
