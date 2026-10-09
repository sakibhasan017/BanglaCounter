# BanglaCounter dataset and reproducibility materials

BanglaCounter contains 3,011 Bangla offensive-text and counterspeech pairs, with three independent annotations for each of two label schemes. The version-5 dataset of record is archived at [Mendeley Data, DOI 10.17632/6ysbv3mg3s.5](https://doi.org/10.17632/6ysbv3mg3s.5). This GitHub repository hosts a copy of the data, model notebooks, predictions, saved metric summaries, and the calculations accompanying the revised *Data in Brief* manuscript, DIB-D-26-02376.

## Use the correct files

| Location | Contents and status |
| --- | --- |
| [`dataset/`](dataset/) | Original and English-translated data in CSV and XLSX. The English-translated release has 3,011 rows and 13 fields. The version-5 Mendeley DOI remains the dataset citation. |
| [`Predictions/`](Predictions/) | Saved test predictions. The five files for manuscript Table 6 are `bloom_560m_test_predictions.csv`, `mbart50_test_predictions.csv`, `byt5_small_test_predictions.csv`, `mt5_base_test_predictions.csv`, and `banglagpt_test_predictions.csv`. Each has 302 rows. |
| [`models/`](models/) | Available notebooks cover BLOOM-560M, ByT5-small, mT5-base, and BanglaGPT among the five Table 6 models. The mBART50 notebook is not present. The notebooks do not establish exact package versions, checkpoint revisions, or the archived training partition used in completed runs. |
| [`Final Metrics/`](Final%20Metrics/) | Saved historical aggregate metrics for a broader set of models. **The Novelty and Near Copy Rate values in these files used token-set Jaccard and are not the revised Table 6 values.** Other model rows are outside the five-model table. |
| [`reproducibility/`](reproducibility/) | Scripts, reconstructed split IDs, prediction-row ID map, descriptive and agreement audit, cross-partition screen, revised word-level Levenshtein results, and the seven-column Table 6 summary. Read its [method and file guide](reproducibility/README.md). |

## Revised Table 6

The first five metrics below retain the available saved-run values. Novelty and Near Copy Rate were recalculated from the saved predictions against the **reconstructed** seed-42 training partition, using word-level normalized Levenshtein similarity and a near-copy threshold of 0.70. The [aggregate audit](reproducibility/results/word_levenshtein_audit.json), [per-row maxima](reproducibility/results/word_levenshtein_per_row.csv), and [calculation code](reproducibility/compute_word_levenshtein.py) document these two revised columns.

| Model | BLEU-4 | ROUGE-L | BERTScore F1 | METEOR | Diversity | Novelty | Near Copy Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BLOOM-560M | 0.0202 | 0.1015 | 0.8733 | 0.0660 | 0.2305 | 0.2029 | 82.12% |
| mBART50 | 0.0140 | 0.0673 | 0.8783 | 0.0447 | 0.0673 | 0.3014 | 54.97% |
| ByT5-small | 0.0150 | 0.0798 | 0.8777 | 0.0537 | 0.0585 | 0.5326 | 0.00% |
| mT5-base | 0.0161 | 0.0847 | 0.8746 | 0.0583 | 0.0282 | 0.5096 | 0.00% |
| BanglaGPT | 0.0071 | 0.0407 | 0.8568 | 0.0228 | 0.4696 | 0.7331 | 0.00% |

The BLEU-4, ROUGE-L, and Diversity values were independently recomputed from the saved predictions in [`prediction_audit.json`](reproducibility/results/prediction_audit.json). BERTScore F1 and METEOR come from the saved aggregate results and have not been independently rerun in this supplement. See [`table6_revised_metrics.json`](reproducibility/results/table6_revised_metrics.json) for the values and their provenance.

## Reproducibility boundary

The five prediction files match 302 references and their order in the version-5 data. The 2,408/301/302 train/validation/test IDs reconstruct the two `train_test_split` calls in the available notebooks with seed 42. The test references and order agree with that reconstruction. The original run's training and validation manifest, model checkpoint revisions, complete environment, and training logs have not been independently established. Thus, Novelty and Near Copy Rate are retrospective measurements against the reconstructed training partition, not verified measurements against an archived run partition.

The authors state that five Bangla-speaking contributors wrote the final version-5 counterspeech responses without AI drafting. Earlier Mendeley versions described AI-drafted responses followed by human review; the final version is represented by the authors as a replacement. A row-level writing and replacement log is not deposited here. Annotation agreement measures consistency of category labels, not independent human quality ratings of the responses.

## Citation and rights

Cite the dataset as: BanglaCounter, Mendeley Data, version 5, [10.17632/6ysbv3mg3s.5](https://doi.org/10.17632/6ysbv3mg3s.5). For the calculations in this repository, identify the GitHub commit or tagged release used. The manuscript is under review; do not cite it as a published article.

The MIT license in this repository applies to author-contributed software. Mendeley Data states CC BY 4.0 for the released dataset; third-party social-media expressions may have separate rights and platform restrictions. Review those rights before redistributing comments or predictions that repeat them.
