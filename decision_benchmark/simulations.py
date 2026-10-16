"""Frozen counterexamples and reproducible generalization diagnostics for J/U."""

import json
from pathlib import Path
import random
import statistics
from .confidence import OperatingPoint, choose_threshold
from .encoding import write_json


def evaluate_fixed(levels, threshold):
    total = sum(n for _, n, _ in levels)
    good = sum(g for _, _, g in levels)
    kept = [(n, g) for t, n, g in levels if threshold is not None and t >= threshold]
    return OperatingPoint(
        threshold, sum(n for n, _ in kept), sum(g for _, g in kept), total, good
    )


def simulate(root, output, repetitions=400):
    if repetitions < 1:
        raise ValueError("Repetitions must be positive")
    fixture = json.loads((Path(root) / "tests/fixtures/cases.json").read_text())
    real = json.loads((Path(root) / "tests/fixtures/real.json").read_text())["cases"]
    rows, points = [], {}
    for case in fixture["cases"] + real:
        point = choose_threshold(case["levels"])
        points[case["id"]] = point
        row = {
            "id": case["id"],
            **point.record(),
            "J": float(point.j),
            "U_at_J": float(point.utility) if point.utility is not None else None,
        }
        expected = case.get("expected", {}).get("n")
        row["expected_count_passed"] = (
            point.retained == expected if expected is not None else None
        )
        if case.get("evaluation_levels"):
            row["distribution_shift"] = evaluate_fixed(
                case["evaluation_levels"], point.threshold
            ).record()
        rows.append(row)
    pairs = []
    for relation in fixture["pairs"]:
        before, after = points[relation["before"]], points[relation["after"]]
        passed = (
            after.j >= before.j
            if relation["check"] == "score_nondecrease"
            else after.errors <= before.errors
        )
        pairs.append(
            {
                **relation,
                "passed": passed,
                "before": before.record(),
                "after": after.record(),
            }
        )
    rng = random.Random(20261016)
    diagnostics = {
        name: [] for name in ("independent_null", "repeated_rows_leak", "split_by_task")
    }

    def trial(name, train, test):
        training = [[t, 1, y] for t, y in train]
        testing = [[t, 1, y] for t, y in test]
        point = choose_threshold(training)
        evaluated = evaluate_fixed(testing, point.threshold)
        diagnostics[name].append(
            {
                "train_coverage": point.retained / point.total,
                "test_coverage": evaluated.retained / evaluated.total,
                "train_accuracy_gain": (
                    point.correct / point.retained - point.total_correct / point.total
                    if point.retained
                    else None
                ),
                "test_accuracy_gain": (
                    evaluated.correct / evaluated.retained
                    - evaluated.total_correct / evaluated.total
                    if evaluated.retained
                    else None
                ),
            }
        )

    for _ in range(repetitions):
        train = [(rng.random(), int(rng.random() < 0.8)) for _ in range(200)]
        test = [(rng.random(), int(rng.random() < 0.8)) for _ in range(2000)]
        trial("independent_null", train, test)
        tasks = [(rng.random(), int(rng.random() < 0.8)) for _ in range(200)]
        copies = tasks * 5
        rng.shuffle(copies)
        trial("repeated_rows_leak", copies[:800], copies[800:])
        trial("split_by_task", tasks[:160] * 5, tasks[160:] * 5)
    summary = {
        name: {
            key: statistics.mean(r[key] for r in runs if r[key] is not None)
            for key in runs[0]
        }
        for name, runs in diagnostics.items()
    }
    result = {
        "method": "J/U_at_J",
        "seed": 20261016,
        "repetitions": repetitions,
        "cases": rows,
        "relations": pairs,
        "diagnostics": diagnostics,
        "diagnostic_summary": summary,
        "known_limitation": "Repairing one answer can change the optimum and admit an additional error (18/20 to 19/20). Failed relational expectations remain visible.",
    }
    write_json(Path(output), result)
    return {
        "cases": len(rows),
        "relational_checks": len(pairs),
        "relational_failures": sum(not p["passed"] for p in pairs),
        "diagnostic_repetitions": repetitions,
        "output": str(output),
    }
