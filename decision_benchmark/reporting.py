"""Human-readable tables generated from the same calculated rating."""

from pathlib import Path
from .rating import CATEGORIES


def write_tables(rating, path):
    lines = [
        "# Benchmark results",
        "",
        "Recomputed from raw responses. Cost is per million calls; latency is HTTP p50 in milliseconds.",
        "",
        "| Rank | Model | Score | Baseline accuracy | U at J ×100 | p50, ms | USD / million calls | Language drop, pp |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rating["overall"]:
        lines.append(
            f"| {row['rank']} | {row['name']} | {row['overall']:.2f} | {100*row['accuracy']:.2f}% | {100*row['confidence_utility']:.2f} | {row['latency']:.2f} | {1000*row['cost']:.2f} | {row['language_drop']:.2f} |"
        )
    for category in CATEGORIES:
        lines += [
            "",
            "## " + category,
            "",
            "| Model | Score | Baseline accuracy | J coverage | Retained accuracy | U at J ×100 | Threshold |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for row in sorted(
            (r for r in rating["categories"] if r["category"] == category),
            key=lambda r: -r["overall"],
        ):
            point = row["result"]
            lines.append(
                f"| {row['name']} | {row['overall']:.2f} | {100*row['baseline_accuracy']:.2f}% | {100*point['coverage']:.2f}% | {100*point['accuracy']:.2f}% | {100*row['confidence_utility']:.2f} | {point['threshold']} |"
            )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
