"""Compare regenerated outputs with independent, read-only research references."""

import json
import math
from pathlib import Path
from .encoding import sha256


def compare_values(actual, expected, path="", deviations=None):
    """Compare reference keys; derived reports may intentionally add new fields."""
    deviations = deviations if deviations is not None else []
    if isinstance(expected, dict):
        for key, value in expected.items():
            if key not in actual:
                raise ValueError(f"Missing reference field {path}/{key}")
            compare_values(actual[key], value, f"{path}/{key}", deviations)
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError(f"Length differs: {path}")
        for index, (a, b) in enumerate(zip(actual, expected)):
            compare_values(a, b, f"{path}/{index}", deviations)
    elif type(expected) is float:
        if not isinstance(actual, (int, float)) or not math.isfinite(actual):
            raise ValueError(f"Invalid numeric value: {path}")
        difference = abs(actual - expected)
        if difference > 1e-10:
            raise ValueError(f"Numeric mismatch {path}: {actual} != {expected}")
        deviations.append(difference)
    elif actual != expected:
        raise ValueError(f"Exact mismatch {path}: {actual} != {expected}")
    return deviations


def check_results(root, output):
    root, output = Path(root), Path(output)
    completion = json.loads((output / "complete.json").read_text())
    for name, expected_hash in completion["files"].items():
        if sha256((output / name).read_bytes()) != expected_hash:
            raise ValueError("Generated result changed or incomplete: " + name)
    required = {
        "rating.json",
        "campaign.json",
        "summary.json",
        "decisions.jsonl.gz",
        "confidence-levels.json",
        "overall.csv",
        "categories.csv",
        "TABLES.md",
    }
    if set(completion["files"]) != required:
        raise ValueError("Incomplete generated file set")
    current = json.loads((output / "rating.json").read_text())
    reference = json.loads((root / "tests/golden/rating.json").read_text())
    differences = []
    for group, keys in [("overall", ("model",)), ("categories", ("model", "category"))]:
        rows = {tuple(r[k] for k in keys): r for r in current[group]}
        old = {tuple(r[k] for k in keys): r for r in reference[group]}
        if len(rows) != len(current[group]) or len(old) != len(reference[group]):
            raise ValueError("Duplicate rating row")
        if set(rows) != set(old):
            raise ValueError("Rating populations differ")
        for key, target in old.items():
            required_keys = (
                (
                    "model",
                    "name",
                    "accuracy",
                    "confidence_utility",
                    "confidence_utility_exact",
                    "latency",
                    "cost",
                    "language_drop",
                    "scores",
                    "overall",
                    "rank",
                )
                if group == "overall"
                else (
                    "model",
                    "name",
                    "category",
                    "total",
                    "baseline_accuracy",
                    "result",
                    "confidence_utility",
                    "confidence_utility_exact",
                    "jaccard",
                    "operations",
                    "scores",
                    "overall",
                )
            )
            target = {k: target[k] for k in required_keys}
            # Thresholds and rational utility are exact contracts, not tolerant floats.
            if (
                "result" in target
                and rows[key]["result"]["threshold"] != target["result"]["threshold"]
            ):
                raise ValueError("Threshold differs")
            compare_values(rows[key], target, str(key), differences)
    campaigns = json.loads((output / "campaign.json").read_text())
    expected = json.loads((root / "tests/golden/campaign.json").read_text())
    for model, target in expected.items():
        actual = campaigns[model]
        for key in (
            "requests",
            "decisions",
            "correct_decisions",
            "cost",
            "cost_per_1000_requests",
            "tokens",
            "http_request_response_ms",
            "suite_metrics",
        ):
            compare_values(actual[key], target[key], model + "/" + key, differences)
        if set(actual["languages"]) != set(target["languages"]):
            raise ValueError("Missing or extra language result")
        for language, expected_language in target["languages"].items():
            fields = (
                "metrics",
                "english_mean_accuracy",
                "delta_from_english_mean_pp",
                "latency_ms",
                "cost",
            )
            compare_values(
                actual["languages"][language],
                {k: expected_language[k] for k in fields},
                model + "/" + language,
                differences,
            )
        expected_stability = target["prediction_stability"]
        actual_stability = actual["prediction_stability"]
        expected_rows = [
            {
                k: row[k]
                for k in (
                    "repeat",
                    "decisions",
                    "changed",
                    "correct_to_wrong",
                    "wrong_to_correct",
                )
            }
            for row in expected_stability["vs_first"]
        ]
        compare_values(
            actual_stability["vs_first"],
            expected_rows,
            model + "/stability",
            differences,
        )
        compare_values(
            actual_stability["mean_flip_rate"],
            expected_stability["mean_flip_rate"],
            model + "/mean_flip_rate",
            differences,
        )
    return {
        "passed": True,
        "overall_rows": len(current["overall"]),
        "category_rows": len(current["categories"]),
        "campaign_models": len(campaigns),
        "float_comparisons": len(differences),
        "max_absolute_deviation": max(differences, default=0),
        "tolerance": 1e-10,
    }
