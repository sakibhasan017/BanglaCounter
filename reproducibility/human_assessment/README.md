# BanglaCounter: Retrospective Audit of Response-Quality Ratings

This document reports a retrospective audit of two sets of response-quality ratings in Bangla and English. It describes the four workbooks, the project account of the rating process, and the agreement and disagreement analyses. The ratings do not measure real-world counterspeech effectiveness or establish external third-party validation.

## 1. Files and Dataset Coverage

Four workbooks were included in the audit. The repository paths below use short filenames; `source_workbook_hashes.csv` records the original workbook names and SHA-256 hashes.

| Original workbook name | Repository path | Rating set | Language version | Records |
|---|---|---|---|---:|
| `Bangla_Counterspeech_Quality.xlsx` | [`raw/evaluator_1_bangla.xlsx`](raw/evaluator_1_bangla.xlsx) | Evaluator 1 | Bangla | 3,011 |
| `Bangla_Counterspeech_Quality_Eval2.xlsx` | [`raw/evaluator_2_bangla.xlsx`](raw/evaluator_2_bangla.xlsx) | Evaluator 2 | Bangla | 3,011 |
| `Translated_Counterspeech_Quality.xlsx` | [`raw/evaluator_1_translated.xlsx`](raw/evaluator_1_translated.xlsx) | Evaluator 1 | English translation | 3,011 |
| `Translated_Counterspeech_Quality_Eval2.xlsx` | [`raw/evaluator_2_translated.xlsx`](raw/evaluator_2_translated.xlsx) | Evaluator 2 | English translation | 3,011 |

All four workbooks contain a worksheet named `BanglaCounter`. Each has 3,011 unique IDs, and the four ID sets match.

Each workbook contains four integer score columns:

- `relevant`
- `safe`
- `factual_accuracy`
- `effectiveness`

The ratings were interpreted on a 1–5 scale. The observed scores range from 2 to 5; no score of 1 was recorded. There is no N/A value in the supplied score columns.

The English workbooks contain English text and responses. Their ratings do not independently establish whether the English translations faithfully represent the original Bangla content.

## 2. Assessment Period and Evaluators

The reported rating period was **23 August to 2 September 2026**. The workbooks contain no item-level scoring timestamps. Their file metadata dates their creation to 2 November 2026, so it cannot establish when the scores were assigned.

The evaluators were described as recent graduates of an Information and Communication Technology (ICT) department working in Bangla Natural Language Processing (NLP). The workbooks do not record their degree titles, institutions, graduation years, or individual research experience.

The reported procedure was that the evaluators rated separately, did not discuss scores during rating, and did not write, generate, or translate the responses. They were personally known to an author. The separate workbooks preserve two score sets but cannot verify those procedural details. This is an author-reported two-evaluator assessment, not an external third-party validation study.

## 3. Scoring Instructions and Rubric Documentation

The reported procedure included a briefing on the purpose of the evaluation, the four criteria, the 1–5 scale, and general scoring guidance. Each workbook records a separate score for relevance, safety, factual accuracy, and effectiveness for every response. The audit package contains no contemporaneous written briefing.

The table is a retrospective written reconstruction of the reported scoring guidance. It gives the intended interpretation of each criterion and score level; it is not a contemporaneous rubric recovered from the rating period.

| Criterion | Score | Description |
|---|---:|---|
| **Relevance** | 1 | The response is unrelated to the offensive text or does not address its content. |
| | 2 | The response has a weak connection to the offensive text and misses the main issue or harm. |
| | 3 | The response addresses part of the issue but does not adequately cover the main concern. |
| | 4 | The response addresses the main issue with minor omissions or limitations. |
| | 5 | The response directly and appropriately addresses the main issue and its context. |
| **Safety** | 1 | The response repeats, promotes, or endorses serious harmful or abusive content. |
| | 2 | The response contains harmful, offensive, or potentially escalating language. |
| | 3 | The response has mixed or ambiguous safety characteristics. |
| | 4 | The response is generally non-abusive but contains minor concerns. |
| | 5 | The response is non-abusive, respectful, and clearly promotes de-escalation. |
| **Factual Accuracy** | 1 | The response contains a demonstrably false central factual claim. |
| | 2 | The response contains materially inaccurate, misleading, or unsupported factual claims. |
| | 3 | The response contains claims that are uncertain, partially supported, or difficult to verify. |
| | 4 | The response is generally factually sound, with minor inaccuracies or imprecision. |
| | 5 | All identifiable factual claims are accurate and adequately supported. |
| **Effectiveness** | 1 | The response is very unlikely to provide constructive value in the given context. |
| | 2 | The response has limited constructive potential and is unlikely to address the situation effectively. |
| | 3 | The response offers some constructive value but has limitations in relevance or usefulness. |
| | 4 | The response is likely to be constructive and useful in addressing the situation. |
| | 5 | The response is highly constructive and well suited to the specific context. |

Each criterion has its own integer score. Higher values represent stronger performance on the corresponding dimension under the reconstructed guidance.

The `factual_accuracy` criterion did not include a separate N/A option in the supplied workbooks. The specific treatment of responses without identifiable factual claims was not separately documented. Similarly, the `effectiveness` ratings represent evaluator assessments under the scoring framework and should not be interpreted as evidence of measured real-world behavioral effectiveness.

The reconstructed descriptions clarify the four columns and the 1–5 scale used in the audit. They do not independently establish the exact instructions available to each evaluator at the time of rating.

## 4. Audit Methodology

The computational audit used the four supplied workbooks and their paired ratings.

1. It checked that each workbook contained 3,011 unique IDs.
2. It verified that the four workbooks contained the same set of IDs.
3. It paired Evaluator 1 and Evaluator 2 scores by ID, language version, and criterion.
4. It calculated exact agreement and linear-weighted Cohen's kappa separately for each of the four criteria in each language version (eight comparisons in total).
5. It identified criterion-level records for further review using the retrospective flagging rule described below.

The ID check reported here compares the four workbooks with one another. It does not, by itself, document a fresh comparison against the public version-5 dataset CSV.

### 4.1 Exact Agreement

Exact agreement is the percentage of complete paired ratings for which both evaluators assigned the same score:

`Exact agreement (%) = (number of identical paired scores / number of complete paired scores) × 100`

### 4.2 Linear-Weighted Cohen's Kappa

Linear-weighted Cohen's kappa was calculated for the ordinal 1–5 scale. The linear agreement weight for scores `x` and `y` was:

`w(x, y) = 1 − |x − y| / 4`

The weighting gives full credit to identical scores and progressively less credit as the distance between scores increases. Kappa was calculated separately for each language and criterion from the original paired ratings. No average or consensus score was created or needed.

### 4.3 Disagreement and Low-Score Flags

A criterion-level event was flagged for review when either of the following conditions was met:

- **Major score difference:** the absolute difference between the two evaluators' scores was at least 2 points; or
- **Low score:** either evaluator assigned a score of 2 or lower.

The overall **review flag** is the union of these two conditions. Major-difference and low-score events are also reported separately. Because an event can meet both conditions, those two counts should not be added to obtain the review-flag total.

These are retrospective screening flags, not adjudicated decisions. A flag does not mean that a score is incorrect, and the analysis did not automatically replace either evaluator's rating or create a final score.

## 5. Agreement Results

Each language-by-criterion comparison contained 3,011 complete paired ratings and no incomplete pairs.

| Language | Criterion | Complete paired ratings | Exact agreements | Exact agreement (%) | Linear-weighted Cohen's kappa |
|---|---|---:|---:|---:|---:|
| Bangla | relevant | 3,011 | 1,338 | 44.4371 | 0.002289 |
| Bangla | safe | 3,011 | 2,587 | 85.9183 | -0.005192 |
| Bangla | factual_accuracy | 3,011 | 2,201 | 73.0986 | -0.005554 |
| Bangla | effectiveness | 3,011 | 2,390 | 79.3756 | 0.008292 |
| English | relevant | 3,011 | 1,087 | 36.1010 | 0.000376 |
| English | safe | 3,011 | 2,577 | 85.5862 | -0.028899 |
| English | factual_accuracy | 3,011 | 2,210 | 73.3975 | 0.022507 |
| English | effectiveness | 3,011 | 2,330 | 77.3829 | -0.004781 |

Across the eight comparisons, exact agreement ranged from **36.10% to 85.92%**. Linear-weighted Cohen's kappa ranged from **-0.029 to 0.023**. The kappa values are close to zero, indicating little agreement beyond that expected from the score distributions under this weighted agreement measure. Raw agreement was higher in some criteria, but ratings were concentrated toward the upper end of the scale, especially for safety. Therefore, raw agreement alone should not be interpreted as strong evaluator reliability or strong discrimination.

## 6. Disagreement and Review-Flag Results

| Language | Criterion | Complete score pairs | Major-difference events | Low-score events | Review-flag events | Unique IDs with a review flag in this comparison |
|---|---|---:|---:|---:|---:|---:|
| Bangla | relevant | 3,011 | 249 | 0 | 249 | 249 |
| Bangla | safe | 3,011 | 0 | 0 | 0 | 0 |
| Bangla | factual_accuracy | 3,011 | 270 | 0 | 270 | 270 |
| Bangla | effectiveness | 3,011 | 54 | 0 | 54 | 54 |
| English | relevant | 3,011 | 550 | 211 | 580 | 580 |
| English | safe | 3,011 | 0 | 0 | 0 | 0 |
| English | factual_accuracy | 3,011 | 303 | 60 | 307 | 307 |
| English | effectiveness | 3,011 | 245 | 0 | 245 | 245 |
| **All comparisons** | **All criteria and languages** | **24,088** | **1,671** | **271** | **1,705** | **1,356 unique IDs overall** |

There were **1,705 flagged criterion-level events** involving **1,356 unique IDs** after deduplication across all four criteria and both language versions. The total of 24,088 complete paired ratings represents 3,011 IDs multiplied by eight language-by-criterion comparisons (four criteria in each of two language versions); it does **not** represent 24,088 unique dataset items.

The major-difference and low-score counts overlap: 237 events met both conditions. The review-flag total (1,705) counts each flagged criterion-level event once, even when both conditions apply.

## 7. Understanding the Output Row Counts

The different row counts in the audit outputs refer to different units:

- **3,011 unique IDs:** the number of dataset items in each workbook.
- **24,088 paired rating checks:** 3,011 IDs × 4 criteria × 2 language versions. A full criterion-level table can therefore contain 24,088 rows if it includes both flagged and unflagged checks.
- **1,705 review-flag events:** the number of criterion-level checks that met at least one flag condition. The filtered `disagreement_flags.csv` contains exactly 1,705 rows.
- **1,356 unique IDs with a flag:** the number of distinct dataset IDs with one or more flags, after deduplicating repeated flags across criteria and language versions.

These counts are not contradictory: a single dataset ID can contribute up to eight criterion-level checks and can be flagged in more than one of them.


## 8. Reproducibility Files

The computational audit outputs are stored in `results/`. All seven CSVs were checked against the four workbooks.

| File | Data rows | Contents |
|---|---:|---|
| [`results/disagreement_flags.csv`](results/disagreement_flags.csv) | 1,705 | Criterion-level records flagged for review. |
| [`results/criterion_review_flags_all.csv`](results/criterion_review_flags_all.csv) | 24,088 | All ID × language × criterion checks, including Yes/No flags. |
| [`results/disagreement_summary.csv`](results/disagreement_summary.csv) | 9 | Eight criterion summaries and one overall total for major differences, low scores, and review flags. |
| [`results/agreement_summary.csv`](results/agreement_summary.csv) | 8 | Exact agreement and linear-weighted Cohen's kappa, with the observed and expected weighted agreements. |
| [`results/agreement_confusion_matrices.csv`](results/agreement_confusion_matrices.csv) | 200 | Eight 5 × 5 paired-score matrices, including zero-count cells. |
| [`results/score_distributions.csv`](results/score_distributions.csv) | 8 | Score frequencies for each rating set, language, and criterion. |
| [`results/source_workbook_hashes.csv`](results/source_workbook_hashes.csv) | 4 | SHA-256 hashes identifying the four source workbooks. The recorded filenames are the original names in Section 1; the bytes are unchanged by repository renaming. |

The seven outputs reproduce the counts and paired-score summaries reported above. They contain no source URLs, evaluator-level timestamps, or case-specific scoring explanations. An executable script that generated these CSVs is not included in this audit package.
