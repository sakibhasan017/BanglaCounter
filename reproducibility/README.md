# Reproducing the revised Data in Brief summaries

This directory supports the revised five-model Table 6 and the descriptive and agreement statistics for BanglaCounter version 5. It reads [`../dataset/BanglaCounter_EnglishTranslated.csv`](../dataset/BanglaCounter_EnglishTranslated.csv) and the five matching CSVs in [`../Predictions/`](../Predictions/). No script modifies those input files.

## Inputs and environment

- The English-translated CSV contains 3,011 records and 13 fields. The GitHub copy uses LF line endings (SHA-256 `f3f6cd90ac63f756491f33e2d86fc4a2e1cce300cc4e904d0fb8aef536320c6a`). A separately verified CRLF copy has SHA-256 `6c9a08bf46f0750d306b156d1a27f6f2af8853909b5ea44d0dd8e0b92d31db21`. The GitHub copy is otherwise byte-identical after line-ending normalization; the corresponding XLSX matched the verified local file byte for byte. The deposited `release_audit.json` was rerun against the GitHub LF bytes.
- Use Python 3, `scikit-learn==1.8.0` for the split reconstruction, and a C++17 compiler (`g++`) for the word-level edit-distance script. These are the **audit environment** requirements. The original model-training environments and checkpoint revisions were not archived in a way that can be verified here.
- The five `../Predictions/*_test_predictions.csv` files contain 302 outputs each and match the version-5 references. They include offensive input text, so apply the dataset's rights and privacy considerations when reusing them.

From this directory, run:

```bash
python -m pip install -r requirements.txt
python verify_release.py ../dataset/BanglaCounter_EnglishTranslated.csv --out results
python check_partition_similarity.py ../dataset/BanglaCounter_EnglishTranslated.csv results/reconstructed_split_ids.csv --out results/cross_partition_similarity_screen.csv
python verify_predictions.py ../dataset/BanglaCounter_EnglishTranslated.csv results/reconstructed_split_ids.csv ../Predictions --out results/prediction_audit.json
python compute_word_levenshtein.py ../dataset/BanglaCounter_EnglishTranslated.csv results/reconstructed_split_ids.csv ../Predictions --out results/word_levenshtein_audit.json
```

`verify_release.py` records the SHA-256 of the input as read. Running it against the Mendeley CSV with CRLF instead of GitHub's LF copy may therefore change only the `source_sha256` field while preserving parsed records and statistics.

## File guide

| File | Purpose |
| --- | --- |
| `verify_release.py` and `results/release_audit.json` | Validate field order, row counts, missing cells, class counts, exact text uniqueness, Fleiss' kappa, nominal Krippendorff's alpha, majority resolution, and split sizes. |
| `results/reconstructed_split_ids.csv` | ID-to-partition mapping reconstructed from two seed-42 `train_test_split` calls on the released row order: 2,408 train, 301 validation, 302 test. It is **not** an archived manifest from a completed model run. |
| `verify_predictions.py`, `results/prediction_audit.json`, and `results/prediction_row_ids.csv` | Check saved prediction references, source inputs, 302-row test order, and generated lengths; recompute BLEU-4, ROUGE-L, Diversity, and the historical Jaccard-based Novelty and Near Copy Rate. The Jaccard columns in this diagnostic audit are **not** the revised Table 6 columns. The row map links each prediction row to a released dataset ID. |
| `compute_word_levenshtein.py`, `word_levenshtein.cpp`, `results/word_levenshtein_audit.json`, and `results/word_levenshtein_per_row.csv` | Recompute revised Novelty and Near Copy Rate as the complement of mean maximum word-level normalized Levenshtein similarity and the proportion with maximum similarity at least 0.70. The per-row CSV gives model, test row, dataset ID, and maximum similarity. |
| `results/table6_revised_metrics.json` | All seven displayed Table 6 metrics and their sources; BERTScore F1 and METEOR are retained saved aggregates, not independently rerun here. |
| `check_partition_similarity.py` and `results/cross_partition_similarity_screen.csv` | Exploratory token-set Jaccard screen of text pairs across reconstructed partitions. This is a different diagnostic from the word-level model-output metrics. |

## Agreement and partition checks

Each of the 3,011 records has three ratings for counterspeech strategy and three for offensive-content category. Agreement is calculated on individual votes **before** adjudication. The audit reports strategy Fleiss' kappa 0.600899 and nominal Krippendorff's alpha 0.600943; category kappa 0.616261 and alpha 0.616303. There are 137 three-way strategy disagreements and 98 three-way category disagreements. All 2-to-1 final labels match the majority. These calculations do not measure response quality.

The test references and test-row order in all five prediction files match the seed-42 reconstruction. Exact test-to-training overlap is zero for both released Bangla text fields. In the exploratory token-set Jaccard screen at similarity at least 0.70, 0/302 test offensive texts and 25/302 test responses have a close reconstructed training counterpart. These are lexical screens, not a determination of semantic duplication or verified historical training leakage.

The original run's train/validation manifest, training-input checksum, exact library versions, checkpoint revisions, and training logs have not been independently established. The saved BERTScore F1 and METEOR aggregates have not been independently rerun. Do not describe reconstructed partitions or retained aggregates as archived run evidence.
