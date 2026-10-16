"""Replay raw responses into campaign statistics and the current J/U rating."""

from collections import defaultdict, Counter
import csv
import gzip
import json
from pathlib import Path
import statistics

from .archive import load_corpus, load_routes, responses, verify_archive
from .encoding import encode, write_json, sha256
from .scoring import (
    finite_number,
    score_response,
    options,
)
from .campaign_metrics import metrics, percentiles
from .rating import CATEGORY_SUITES, build_rating


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_model_report(model, corpora, grouped, cases, lookup):
    """Aggregate one model across suites, repeats and languages."""
    repeats = []
    for repeat in range(1, 6):
        suites = {}
        for suite in sorted({c["suite"] for c in corpora["en"]}):
            answers = [
                a
                for row in grouped[model, "en", repeat]
                if row["suite"] == suite
                for a in row["results"].values()
            ]
            suites[suite] = {
                "decisions": len(answers),
                "correct": sum(a["correct"] for a in answers),
                "accuracy": 100 * sum(a["correct"] for a in answers) / len(answers),
            }
        repeats.append({"repeat": repeat, "suites": suites})
    all_rows = [
        row for (m, _, _), rows in grouped.items() if m == model for row in rows
    ]
    cost = sum(row["usage"]["cost"] for row in all_rows)
    report = {
        "model": model,
        "repeats": repeats,
        "requests": len(all_rows),
        "decisions": sum(len(row["results"]) for row in all_rows),
        "correct_decisions": sum(
            a["correct"] for row in all_rows for a in row["results"].values()
        ),
        "cost": cost,
        "cost_per_1000_requests": cost * 1000 / len(all_rows),
        "tokens": {
            field: sum(row["usage"][field] for row in all_rows)
            for field in ("input_tokens", "output_tokens")
        },
        "http_request_response_ms": percentiles(
            [row["elapsed_ms"] for row in all_rows]
        ),
        "suite_metrics": {},
        "languages": {},
        "prediction_stability": {},
    }
    english = [row for repeat in range(1, 6) for row in grouped[model, "en", repeat]]
    for suite in repeats[0]["suites"]:
        selected = [row for row in english if row["suite"] == suite]
        question_groups = defaultdict(list)
        for row in selected:
            case = cases["en", row["id"]]
            for question, answer in row["results"].items():
                workflow = case.get("workflow", "")
                label = f"{workflow}/{question}" if workflow else question
                question_groups[label].append(
                    (case["request"]["questions"][question], answer)
                )
        report["suite_metrics"][suite] = {
            "latency_ms": percentiles([row["elapsed_ms"] for row in selected]),
            "cost": sum(row["usage"]["cost"] for row in selected),
            "questions": {
                name: metrics(
                    [a for _, a in values],
                    (
                        options(values[0][0])
                        if values[0][0]["type"] == "choice"
                        else [str(i) for i in range(len(options(values[0][0])))]
                    ),
                )
                for name, values in question_groups.items()
            },
        }
    for language in ("uk", "ar", "es", "zh"):
        for suite in ("xnli_en", "proofwriter"):
            selected = [
                row for row in grouped[model, language, 1] if row["suite"] == suite
            ]
            labels = sorted({
                label
                for row in selected
                for question in cases[language, row["id"]]["request"]["questions"].values()
                for label in options(question)
            })
            met = metrics(
                [a for row in selected for a in row["results"].values()], labels
            )
            english_accuracy = sum(p["suites"][suite]["accuracy"] for p in repeats) / 5
            report["languages"][language + "/" + suite] = {
                "metrics": met,
                "english_mean_accuracy": english_accuracy,
                "delta_from_english_mean_pp": met["accuracy"] - english_accuracy,
                "latency_ms": percentiles([row["elapsed_ms"] for row in selected]),
                "cost": sum(row["usage"]["cost"] for row in selected),
            }
    flips = []
    for repeat in range(2, 6):
        changes = correct_to_wrong = wrong_to_correct = 0
        for case in corpora["en"]:
            first = lookup[model, "en", 1, case["id"]]["results"]
            later = lookup[model, "en", repeat, case["id"]]["results"]
            for question, before in first.items():
                after = later[question]
                changes += before["prediction"] != after["prediction"]
                correct_to_wrong += before["correct"] and not after["correct"]
                wrong_to_correct += not before["correct"] and after["correct"]
        flips.append(
            {
                "repeat": repeat,
                "decisions": sum(len(c["gold"]) for c in corpora["en"]),
                "changed": changes,
                "correct_to_wrong": correct_to_wrong,
                "wrong_to_correct": wrong_to_correct,
            }
        )
    report["prediction_stability"] = {
        "vs_first": flips,
        "mean_flip_rate": statistics.mean(r["changed"] / r["decisions"] for r in flips),
    }
    return report


def replay(root, output):
    root, output = Path(root), Path(output)
    target = output.resolve()
    protected = [
        (root / name).resolve()
        for name in (
            "data",
            "tests",
            "decision_benchmark",
            "docs",
            "tools",
        )
    ]
    if target == root.resolve() or any(
        target == p or p in target.parents for p in protected
    ):
        raise ValueError("Output overlaps protected package inputs")
    if output.exists() and any(output.iterdir()):
        raise ValueError(
            "Use a new empty output directory; partial or old results cannot be reused"
        )
    integrity = verify_archive(root)
    output.mkdir(parents=True, exist_ok=True)
    cases = load_corpus(root)
    routes = {r["model"]: r for r in load_routes(root)}
    corpora = {
        language: [c for (lang, _), c in cases.items() if lang == language]
        for language in ("en", "uk", "ar", "es", "zh")
    }
    grouped = defaultdict(list)
    levels = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    operations = defaultdict(list)
    native_counts = Counter()
    excluded = Counter()
    lookup = {}
    decisions = 0
    with (output / "decisions.jsonl.gz").open("wb") as file:
        with gzip.GzipFile(filename="", mode="wb", fileobj=file, mtime=0) as stream:
            for row in responses(root):
                key = row["key"]
                case = cases[key["language"], key["case"]]
                scored = score_response(case, row["raw"], routes[key["model"]])
                if not scored["complete"] or scored["error"]:
                    raise ValueError(f'Invalid accepted response: {row["logical_id"]}')
                scored["execution_limit"] = row["execution"].get(
                    "provider_concurrency_limit"
                )
                grouped[key["model"], key["language"], key["repeat"]].append(scored)
                lookup[key["model"], key["language"], key["repeat"], key["case"]] = (
                    scored
                )
                category = CATEGORY_SUITES.get(case["suite"])
                if category:
                    operations[key["model"], category].append(scored)
                for question, answer in scored["results"].items():
                    record = {
                        **key,
                        "question": question,
                        "suite": case["suite"],
                        "logical_id": row["logical_id"],
                        **answer,
                    }
                    stream.write(encode(record) + b"\n")
                    decisions += 1
                    confidence = answer.get("native_confidence")
                    if confidence is None:
                        excluded[key["model"], case["suite"], answer["type"]] += 1
                        continue
                    if category is None:
                        raise ValueError(
                            "Unexpected native confidence outside declared slice"
                        )
                    if not finite_number(confidence) or not 0 <= confidence <= 1:
                        raise ValueError("Invalid native confidence")
                    counts = levels[key["model"], category][confidence]
                    counts[0] += 1
                    counts[1] += int(answer["correct"])
                    native_counts[key["model"]] += 1
    if decisions != 200500 or any(native_counts[model] != 15050 for model in routes):
        raise ValueError("Decision/native-confidence population mismatch")
    for model in routes:
        omitted = {
            suite: sum(
                n for (m, s, _), n in excluded.items() if m == model and s == suite
            )
            for suite in ("sst2", "boolq", "typed-decisions")
        }
        if omitted != {"sst2": 1000, "boolq": 1000, "typed-decisions": 3000}:
            raise ValueError("Excluded population mismatch")
    campaign = {
        model: build_model_report(model, corpora, grouped, cases, lookup)
        for model in routes
    }
    op_metrics = {
        (model, category): {
            "model": model,
            "category": category,
            "n": len(rows),
            "p50": statistics.median(row["elapsed_ms"] for row in rows),
            "cost_per_1000": sum(row["usage"]["cost"] for row in rows)
            * 1000
            / len(rows),
        }
        for (model, category), rows in operations.items()
    }
    names = {
        r["model"]: r["name"]
        for r in json.loads((root / "data/models.json").read_text())
    }
    rating = build_rating(levels, op_metrics, campaign, names)
    from .reporting import write_tables

    write_tables(rating, output / "TABLES.md")
    write_json(output / "rating.json", rating)
    write_json(output / "campaign.json", campaign)
    write_json(
        output / "confidence-levels.json",
        [
            {
                "model": model,
                "category": category,
                "levels": [[t, *v] for t, v in sorted(bins.items())],
            }
            for (model, category), bins in sorted(levels.items())
        ],
    )
    write_json(
        output / "summary.json",
        {
            **integrity,
            "decisions": decisions,
            "native_confidence_decisions": sum(native_counts.values()),
            "reported_accepted_cost_usd": sum(r["cost"] for r in campaign.values()),
            "confidence_winner": rating["confidence_winner"],
        },
    )
    write_csv(
        output / "overall.csv",
        [
            {
                k: row[k]
                for k in (
                    "rank",
                    "model",
                    "name",
                    "overall",
                    "accuracy",
                    "confidence_utility",
                    "latency",
                    "cost",
                    "language_drop",
                )
            }
            for row in rating["overall"]
        ],
    )
    write_csv(
        output / "categories.csv",
        [
            {
                "model": row["model"],
                "category": row["category"],
                "overall": row["overall"],
                "accuracy": row["baseline_accuracy"],
                "U_at_J": row["confidence_utility"],
                **{k: v for k, v in row["result"].items() if k != "accuracy"},
                "retained_accuracy": row["result"]["accuracy"],
            }
            for row in rating["categories"]
        ],
    )
    completion = {
        "schema_version": 1,
        "files": {
            p.name: sha256(p.read_bytes())
            for p in sorted(output.iterdir())
            if p.is_file()
        },
    }
    write_json(output / "complete.json", completion)
    return json.loads((output / "summary.json").read_text())
