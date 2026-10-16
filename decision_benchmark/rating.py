"""Current six-category rating. All scales and weighting live here."""

from fractions import Fraction
import math

from .confidence import choose_threshold

CATEGORY_SUITES = {
    "ag_news": "topic",
    "banking77": "intent",
    "sst5": "sentiment",
    "emotion": "sentiment",
    "xnli_en": "inference",
    "typed-decisions": "decisions",
    "proofwriter": "proof",
}
CATEGORIES = ("topic", "intent", "sentiment", "inference", "decisions", "proof")


def relative_quality(value, best):
    if abs(value - best) < 1e-12:
        return 10
    gap = math.floor((best - value) * 100 + 0.5)
    for limit, score in ((2, 9), (5, 7), (10, 5), (20, 3)):
        if gap <= limit:
            return score
    return 1


def utility_score(value: Fraction):
    if value is None:
        raise ValueError(
            "Confidence utility undefined: both correct and incorrect answers are required"
        )
    return max(1, min(10, math.ceil(10 * value)))


def efficiency_score(value, best):
    if value <= 0 or best <= 0:
        raise ValueError("Cost and latency must be positive")
    return max(1, 10 - 2 * math.log2(value / best))


def build_rating(levels, operations, campaign, names):
    categories = []
    for (model, category), bins in sorted(levels.items()):
        point = choose_threshold(
            [(threshold, *counts) for threshold, counts in bins.items()]
        )
        utility = point.utility
        if utility is None:
            raise ValueError(f"Undefined utility: {model}/{category}")
        categories.append(
            {
                "model": model,
                "name": names[model],
                "category": category,
                "total": point.total,
                "baseline_accuracy": point.total_correct / point.total,
                "result": point.record(),
                "confidence_utility": float(utility),
                "confidence_utility_exact": str(utility),
                "jaccard": float(point.j),
                "jaccard_exact": str(point.j),
                "operations": operations[model, category],
            }
        )
    for row in categories:
        peers = [other for other in categories if other["category"] == row["category"]]
        op = row["operations"]
        row["scores"] = {
            "quality": relative_quality(
                row["baseline_accuracy"], max(p["baseline_accuracy"] for p in peers)
            ),
            "confidence": utility_score(Fraction(row["confidence_utility_exact"])),
            "speed": efficiency_score(
                op["p50"], min(p["operations"]["p50"] for p in peers)
            ),
            "price": efficiency_score(
                op["cost_per_1000"],
                min(p["operations"]["cost_per_1000"] for p in peers),
            ),
        }
        row["overall"] = sum(row["scores"].values()) / 4
    overall = []
    for model, report in campaign.items():
        cells = [r for r in categories if r["model"] == model]
        if {r["category"] for r in cells} != set(CATEGORIES):
            raise ValueError("Missing rating category")
        utility = (
            sum((Fraction(r["confidence_utility_exact"]) for r in cells), Fraction())
            / 6
        )
        overall.append(
            {
                "model": model,
                "name": names[model],
                "accuracy": sum(r["baseline_accuracy"] for r in cells) / 6,
                "confidence_utility": float(utility),
                "confidence_utility_exact": str(utility),
                "latency": report["http_request_response_ms"]["p50"],
                "cost": report["cost_per_1000_requests"],
                "language_drop": sum(
                    max(0, -v["delta_from_english_mean_pp"])
                    for v in report["languages"].values()
                )
                / 8,
            }
        )
    for row in overall:
        row["scores"] = {
            "quality": relative_quality(
                row["accuracy"], max(r["accuracy"] for r in overall)
            ),
            "confidence": utility_score(Fraction(row["confidence_utility_exact"])),
            "speed": efficiency_score(
                row["latency"], min(r["latency"] for r in overall)
            ),
            "price": efficiency_score(row["cost"], min(r["cost"] for r in overall)),
            "languages": relative_quality(
                -row["language_drop"] / 100,
                -min(r["language_drop"] for r in overall) / 100,
            ),
        }
        row["overall"] = sum(row["scores"].values()) / 5
    overall.sort(key=lambda r: (-r["overall"], r["model"]))
    for row in overall:
        row["rank"] = 1 + sum(r["overall"] > row["overall"] + 1e-12 for r in overall)
    winners = []
    for category in CATEGORIES:
        peers = [r for r in categories if r["category"] == category]
        best = max(r["overall"] for r in peers)
        quality = max(r["baseline_accuracy"] for r in peers)
        winners.append(
            {
                "category": category,
                "balance": [
                    r["name"] for r in peers if abs(r["overall"] - best) < 1e-12
                ],
                "accuracy": [
                    r["name"]
                    for r in peers
                    if abs(r["baseline_accuracy"] - quality) < 1e-12
                ],
            }
        )
    return {
        "method": "jaccard-threshold-u-at-j-v1",
        "overall": overall,
        "categories": categories,
        "winners": winners,
        "confidence_winner": max(overall, key=lambda r: r["confidence_utility"])[
            "name"
        ],
    }
