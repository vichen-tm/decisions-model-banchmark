# Choosing models for your task

## Starting points from this experiment

| Task | Start with the balance leader | Prioritize accuracy |
|---|---|---|
| Text topic | Perplexity Decider | Mercury Decide |
| User intent | Liquid D1 | Clef Omni |
| Text sentiment and emotion | Mercury Decide | Mercury Decide |
| Decisions under stated conditions | Microsoft Decision | Microsoft Decision |
| Textual entailment | Perplexity Decider | Perplexity Decider |
| Deductions from facts and rules | Perplexity Decider | Perplexity Decider |

Liquid D1 is the overall starting point, followed by Perplexity. See [all ten models](../results/TABLES.md). Overall scores help create a shortlist; category results help match it to a task.

Clef and Liquid have very similar median latency: about 283 and 287 ms. All model medians fall between 283 and 429 ms. Observed cost varies more: Mercury about $7.14 per million calls, Liquid $8.40, and Clef $79.28 on the experimental workload.

Perplexity leads average baseline category accuracy at 81.46%, followed closely by Microsoft at 80.95% and Liquid at 80.33%. Liquid retains quality best across the tested languages, followed by Perplexity and Luna. Jev leads U at J at 24.23 out of 100; ScaleDown follows at 22.98. These measurements answer different questions.

## Practical workflow

1. **Define the decision.** Specify input, allowed answers, correct outcomes, and downstream use. Match the closest category; for yes/no and reading, inspect full dataset results rather than the confidence ranking alone.
2. **Shortlist candidates.** Start with category balance and accuracy leaders. Include required language, input size, deployment options, and modalities.
3. **Create your own labeled examples.** Include common requests, rare classes, ambiguity, and costly errors. Label before comparing models. Preserve source task identity across repeats.
4. **Evaluate original answers.** Inspect per-class and important subgroup accuracy, not just one percentage. Measure cost and latency on your input lengths and concurrency.
5. **Evaluate confidence selection.** Select a J threshold on one split. Apply it unchanged to another split and measure coverage, retained errors, and referral volume. Evaluate any required accuracy target explicitly.
6. **Evaluate the whole workflow.** Count first-model calls, review calls, remaining errors, and both stages' costs. A reviewing model can also make mistakes.
7. **Freeze configuration.** Record model, provider, version, questions, option order, dataset, and threshold. Recheck after changes.

## Confidence example

For ScaleDown in Topic, J retains 951 of 1,000 answers: 876 correct and 75 incorrect. Baseline accuracy is 89.1%; retained accuracy is 92.11%. The 49 rejected answers contain 34 errors. U at J is 29.51 out of 100.

Even perfect review of those 49 rejected answers leaves 75 retained errors: end-to-end accuracy would be 92.5%, not nearly 100%. A near-perfect target needs a different reviewed workflow and direct measurement.

Liquid in the same task retains 987 answers at 89.26% accuracy, versus 88.5% initially; U is 7.37. Confidence selection helps less here, while Liquid may still be preferable on cost and other tasks.

## Adapt priorities to your application

The published score uses equal component weights and fixed scales. If price is unimportant or one error type dominates your application, compare raw metrics and evaluate alternative priorities on the saved data. Raw responses and scored decisions are included for this purpose. Do not replace baseline quality with post-filter accuracy while also rewarding the same selection through U without explicitly redefining the score.
