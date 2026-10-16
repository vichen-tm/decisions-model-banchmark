# Sources and attribution

## Original benchmarks and datasets

| Benchmark / dataset | Source page | Data used | Role in this experiment |
|---|---|---|---|
| System One Bench | [Repository](https://github.com/alilibx/system-one-bench) | Task collection and decision-question format | Starting point for the comparison |
| SST-2 | [Dataset page](https://huggingface.co/datasets/stanfordnlp/sst2) | [validation / Parquet](https://huggingface.co/datasets/stanfordnlp/sst2/resolve/refs%2Fconvert%2Fparquet/default/validation/0000.parquet); 200 EN tasks | Binary sentiment |
| SST-5 | [Dataset page](https://huggingface.co/datasets/SetFit/sst5) | [test / Parquet](https://huggingface.co/datasets/SetFit/sst5/resolve/refs%2Fconvert%2Fparquet/default/test/0000.parquet); 200 EN tasks | Five-class sentiment |
| Banking77 | [Dataset page](https://huggingface.co/datasets/mteb/banking77) | [test / Parquet](https://huggingface.co/datasets/mteb/banking77/resolve/refs%2Fconvert%2Fparquet/default/test/0000.parquet); 200 EN tasks | User intent |
| Typed Decisions | [Dataset page](https://huggingface.co/datasets/LocalLLaMA/typed-decisions) | [test / Parquet](https://huggingface.co/datasets/LocalLLaMA/typed-decisions/resolve/refs%2Fconvert%2Fparquet/all/test/0000.parquet); 400 EN tasks | Decisions under conditions; choice/noul/score |
| Emotion | [Dataset page](https://huggingface.co/datasets/dair-ai/emotion) | [test / Parquet](https://huggingface.co/datasets/dair-ai/emotion/resolve/refs%2Fconvert%2Fparquet/split/test/0000.parquet); 200 EN tasks | Text emotion |
| AG News | [Dataset page](https://huggingface.co/datasets/fancyzhx/ag_news) | [test / Parquet](https://huggingface.co/datasets/fancyzhx/ag_news/resolve/refs%2Fconvert%2Fparquet/default/test/0000.parquet); 200 EN tasks | News topic |
| BoolQ | [Dataset page](https://huggingface.co/datasets/google/boolq) | [validation / Parquet](https://huggingface.co/datasets/google/boolq/resolve/refs%2Fconvert%2Fparquet/default/validation/0000.parquet); 200 EN tasks | Reading comprehension |
| XNLI | [Dataset page](https://huggingface.co/datasets/facebook/xnli) | [test / Parquet](https://huggingface.co/datasets/facebook/xnli/resolve/refs%2Fconvert%2Fparquet/en/test/0000.parquet); 150 EN tasks | Textual entailment |
| ProofWriter | [Dataset page](https://allenai.org/data/proofwriter) · [Paper](https://aclanthology.org/2021.findings-acl.317/) | [V2020.12.3 archive](https://aristo-data-public.s3.amazonaws.com/proofwriter/proofwriter-dataset-V2020.12.3.zip); 300 EN tasks | Deductions from facts and rules |

XNLI also has an [author repository](https://github.com/facebookresearch/XNLI). EN task counts refer to our sample per pass. The experiment extends System One Bench with languages, ProofWriter, measurements, scoring, and the J/U ranking.

## Redistribution status

| Dataset | Recorded licensing metadata |
|---|---|
| SST-2 | unknown |
| SST-5 | Not declared in the saved card |
| Banking77 | MIT in the mirror metadata |
| Typed Decisions | Apache-2.0 |
| Emotion | other |
| AG News | unknown |
| BoolQ | CC-BY-SA-3.0 |
| XNLI | Not declared in the saved card |
| ProofWriter | README present; no confirmed LICENSE file found in the source archive |

The saved material does not establish the license of borrowed System One Bench instructions. This registry records source information; it does not grant third-party permissions. Select a license for original code and verify redistribution of dataset text and derived translations before public release.

Exact snapshot URLs, splits, observed revisions, and SHA-256 hashes are in `data/sources/datasets.json`. A hash identifies the input used; a revision observed later is not retroactively assigned to that snapshot. ProofWriter task records retain theory and question identifiers.

UK XNLI and four ProofWriter translations were prepared with LLMs. AR/ES/ZH XNLI uses official translations with project corrections. Translation terms depend on the source material. A mirror marked MIT does not make the entire package MIT-licensed.

Text shards are separated by dataset and language. Public release may include permitted parts and source retrieval/reconstruction instructions for the rest. Release and licensing decisions remain open.

Code preparation and analysis used Codex. Claude Opus 5.5 reviewed the general plan, technical plan, and implementation. The project owner will determine original-code authorship and licensing before repository publication.

## Metric references

[Jaccard definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.jaccard_score.html). U is the retained-correct rate minus the retained-error rate (TPR−FPR). The exact adopted formulas, scales, and interpretation are self-contained in [METHODOLOGY](METHODOLOGY.md).
