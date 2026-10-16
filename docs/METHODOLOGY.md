# Methodology

## Full experiment and current ranking

The full experiment contains nine datasets in seven categories: Topic (AG News), Intent (Banking77), Sentiment (SST-2/SST-5/Emotion), Reading (BoolQ), Inference (XNLI), Decisions (Typed Decisions), and Proof (ProofWriter).

The current ranking uses six categories with native confidence. BoolQ, SST-2, and noul fields are excluded from this ranking. Sentiment combines SST-5 and Emotion. Inference and Proof combine five English passes with one pass in each of four other languages. Decisions includes choice/score fields; cost and latency apply to the complete request containing all five questions.

## Scoring one response: version 1.2.0

- **choice:** use the model's explicit choice even when it differs from the probability argmax. Record the conflict separately.
- **noul:** values at least 0.5 predict class 1; smaller values predict class 0.
- **score:** take the argmax over zero-based indices; ties choose the first index. Do not round the expected numeric score into a class.
- Probabilities must be finite and within [0,1]. If their sum differs from 1 by at most 0.01 (boundary epsilon 1e-12), divide by the sum. Gold distributions use the stricter tolerance 1e-4.
- Validate HTTP status, provider, model version, question set, and response completeness. Missing answers do not become correct answers. Mark incomplete runs explicitly.
- Macro F1 includes every allowed class; a class with neither support nor predictions gets F1=0. Also report macro F1 over classes present in gold, confusion matrices, Brier score, NLL (clip=1e-12), and ECE over ten equal-width bins.

## The J operating threshold

Let N be the number of decisions, G the original number correct, and E=N−G. At threshold t, retain every answer with native confidence ≥t. Never split equal-confidence answers. Let g and e be the retained correct and incorrect counts; n=g+e.

**J(t)=g/(G+e).** Maximize J; break ties by fewer retained errors, then more retained correct answers. Comparisons use exact fractions. Candidates include all distinct confidence values, no filtering, and the empty selection. Threshold 0 denotes no filtering; null denotes an empty selection. When G+e=0, define J=1, following equality of empty sets. Accuracy of an empty selection is undefined.

This favors removing errors while retaining correct answers. In the control examples, neither five clean answers out of 2,000 at 50% baseline accuracy nor a rise from 99% to 100% at the cost of half the coverage wins.

## Confidence utility U at J

**U(tJ)=g/G−e/E = (E−e)/E−(G−g)/G.**

This is the fraction of errors removed minus the fraction of correct answers lost at the selected operating threshold. No filtering gives U=0. Display U×100. If there are no correct answers or no errors, U is undefined: an individual result can contain null and ranking construction stops. Both classes exist in all 60 current model/category combinations.

U at J measures the practical utility of selection at this operating point. The quality component continues to use accuracy **before** filtering. U is neither an answer's probability of correctness nor a numerical calibration score.

## Score scales and weights

- **Confidence:** max(1,min(10,ceil(10U))). Exact fractions avoid boundary errors.
- **Quality:** a leader gets 10. Round its lead in percentage points as floor(gap+0.5). A rounded gap up to 2 gets 9; up to 5 gets 7; up to 10 gets 5; up to 20 gets 3; larger gaps get 1.
- **Speed and price:** max(1,10−2log₂(value/min)).
- **Languages:** average the eight nonnegative accuracy drops relative to English. An improvement in one language does not cancel a drop in another. Compare with the smallest average drop using the quality scale.
- **Category score:** mean of four scores: original quality, confidence, speed, and price.
- **Overall score:** mean of five scores, including languages. First average the six original category accuracies for quality. First average the six U values, then apply the confidence scale. The overall score is not the mean of category scores.

Determine winners before display rounding. The winners table retains all tied models. Compare confidence utility using U even when several rounded confidence scores are equal.

## Cost, latency, and repeatability

Cost is the observed request cost on this workload. Machine-readable `cost`/`cost_per_1000` ranking fields retain the per-thousand unit; reader-facing tables show **per million calls**. Request count and decision count are different.

Overall p50 uses nearest-rank p50 over all 12,050 requests per model. Category p50 uses `statistics.median` over requests in that category, including language runs. These definitions can differ for even-sized samples; both are preserved to reproduce the published ranking. Overall cost and speed include SST-2/BoolQ, while quality/confidence use the six-category slice.

Prediction stability compares responses to the same tasks in passes 2–5 with pass 1. Per-pass suite accuracy remains available in `campaign.json`.

## Verification

`confidence.py` and `rating.py` own the formulas; `scoring.py` owns response scoring. Raw reproduction does not read `tests/golden/`. Verification compares against that independent reference: integers, thresholds, and rational U are exact; floating-point values use tolerance 1e-10 and report the maximum deviation.

See [limitations](LIMITATIONS.md) and `results/simulations.json` for counterexamples and diagnostic scenarios.
