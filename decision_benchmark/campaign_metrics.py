"""Campaign statistics: full-label metrics and historical latency quantiles."""

import collections
import math
import statistics


def mean(xs):
    return statistics.mean(xs) if xs else None


def percentiles(xs):
    xs = sorted(xs)
    return {
        "n": len(xs),
        "mean": mean(xs),
        **{
            f"p{p}": xs[max(0, math.ceil(len(xs) * p / 100) - 1)] if xs else None
            for p in (50, 90, 95, 99)
        },
        "min": min(xs) if xs else None,
        "max": max(xs) if xs else None,
        **{
            f"at_least_{ms}ms": sum((v >= ms for v in xs))
            for ms in (1000, 5000, 30000, 60000)
        },
    }


def metrics(qq, labels=None):
    n = len(qq)
    if not n or not all(q["valid"] for q in qq):
        raise ValueError("Metrics require nonempty valid decisions")
    labels = labels or sorted(
        {str(q["gold"]) for q in qq} | {str(q["prediction"]) for q in qq}
    )
    cm = collections.Counter(((str(q["gold"]), str(q["prediction"])) for q in qq))
    per = []
    for lab in labels:
        tp = cm[lab, lab]
        support = sum((v for (g, p), v in cm.items() if g == lab))
        pred = sum((v for (g, p), v in cm.items() if p == lab))
        precision = tp / pred if pred else 0
        recall = tp / support if support else 0
        per.append(
            {
                "label": lab,
                "support": support,
                "predicted": pred,
                "precision": precision,
                "recall": recall,
                "f1": 2 * tp / (support + pred) if support + pred else 0,
            }
        )
    conf = [q for q in qq if q.get("confidence") is not None]
    bins = []
    for i in range(10):
        rr = [q for q in conf if min(9, int(q["confidence"] * 10)) == i]
        bins.append(
            {
                "lower": i / 10,
                "upper": (i + 1) / 10,
                "n": len(rr),
                "mean_confidence": mean([q["confidence"] for q in rr]),
                "accuracy": mean([int(q["correct"]) for q in rr]),
            }
        )
    risk = []
    ranked = sorted(conf, key=lambda q: q["confidence"], reverse=True)
    for frac in (0.1, 0.25, 0.5, 0.75, 0.9, 1):
        if not ranked:
            break
        threshold = ranked[max(0, math.ceil(frac * len(ranked)) - 1)]["confidence"]
        rr = [q for q in ranked if q["confidence"] >= threshold]
        risk.append(
            {
                "requested_coverage": frac,
                "actual_coverage": len(rr) / n,
                "threshold": threshold,
                "n": len(rr),
                "error_rate": 1 - mean([int(q["correct"]) for q in rr]),
            }
        )
    return {
        "n": n,
        "correct": sum((q["correct"] for q in qq)),
        "accuracy": 100 * mean([int(q["correct"]) for q in qq]),
        "macro_f1": mean([p["f1"] for p in per]),
        "macro_f1_present_gold": mean([p["f1"] for p in per if p["support"]]),
        "gold_classes_present": sum((p["support"] > 0 for p in per)),
        "classes_in_metric": len(per),
        "macro_precision": mean([p["precision"] for p in per]),
        "macro_recall": mean([p["recall"] for p in per]),
        "weighted_f1": sum((p["f1"] * p["support"] for p in per)) / n,
        "per_class": per,
        "confusion": [
            {"gold": g, "prediction": p, "n": v} for (g, p), v in sorted(cm.items())
        ],
        "confidence_coverage": len(conf),
        "native_confidence_coverage": sum(
            (q.get("native_confidence") is not None for q in qq)
        ),
        "ece_10_equal_width": (
            sum(
                (
                    b["n"] * abs(b["accuracy"] - b["mean_confidence"])
                    for b in bins
                    if b["n"]
                )
            )
            / len(conf)
            if conf
            else None
        ),
        "calibration_bins": bins,
        "risk_coverage": risk,
        **{
            key: mean([q[key] for q in qq if q.get(key) is not None])
            for key in [
                "nll",
                "brier",
                "score_mae",
                "score_class_mae",
                "soft_gold_at_prediction",
                "soft_kl",
            ]
        },
        "normalization_count": sum(
            (q.get("normalization", {}).get("applied", False) for q in qq)
        ),
        "choice_probability_conflicts": sum(
            ("choice_probability_conflict" in q for q in qq)
        ),
    }
