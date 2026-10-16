# Limitations and publication questions

## Operating thresholds and required accuracy

J selects a compromise on the observed sample. It does not set a 95% or 99% target or minimize referrals while guaranteeing such a target. Reviewing only rejected answers cannot fix errors among retained answers.

U at J describes confidence utility at this operating point. It is not a probability of truth or a calibration measure independent of baseline quality.

The known edge case remains visible: after one answer is corrected, the selection can change from 18 correct answers without errors to 19 correct answers plus one error. This follows the agreed J optimization; the number of retained errors need not decrease under every corpus improvement.

## Threshold selection and evaluation use the same sample

Published thresholds and U describe the research sample. For deployment, select a threshold on one part and evaluate the fixed threshold on a different set of original tasks. Keep repeats and translations of each task together.

Revalidate thresholds after data shifts or model/provider changes. Diagnostics include noise, repeat leakage, and distribution shift.

## Languages and labeling

Translation and review used LLMs. XNLI AR/ES/ZH started from official translations and includes project corrections. UK XNLI and all four ProofWriter translations were prepared separately. The final review targeted problematic records; one independent expert did not recheck all 1,800 pairs from scratch. Borderline XNLI tasks `xnli_en-11` and `xnli_en-17` remain in the agreed corpus. Two corrupted source rows were replaced for english-v2.

Measured representatives of language groups do not establish quality for every language in a group. The language comparison covers only XNLI and ProofWriter.

## Ranking coverage

Noul has no native confidence; Reading/BoolQ and SST-2 are outside the current ranking. Their responses, accuracy, and full-experiment metrics remain available. Cost and latency depend on input length, task composition, network routing, and concurrency.

## Before public distribution

This complete package is for local review. Some saved dataset cards do not establish redistribution terms, and request texts contain those materials. Determine the licenses for original code and translations and the permission to distribute third-party text before publication. See [ATTRIBUTION](ATTRIBUTION.md).

Text shards are separated by dataset and language, allowing permitted parts to be released independently or replaced by source-retrieval instructions. No repository has been created in this workflow.

## Request and response bytes

Raw responses have verifiable hashes. Request bodies were canonically re-encoded from saved intents and matched their recorded hashes. There was no independent wire capture.
