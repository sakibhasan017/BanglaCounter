# BanglaCounter: A Benchmark Dataset and Transformer-Based Evaluation Framework for Bangla Counterspeech

BanglaCounter is a benchmark dataset and evaluation framework for Bangla counterspeech generation. It was developed as part of an undergraduate thesis to support research on generating constructive Bangla counterspeech from offensive Bangla text.

The benchmark contains paired offensive text and counterspeech responses collected and curated for conditional text generation. Multiple transformer-based models were evaluated under the same experimental settings using lexical, semantic, diversity, originality, memorization, safety, and generation-quality metrics.

---

## Repository Structure

```
BanglaCounter/
│
├── dataset/
│   └── BanglaCounter.csv
│
├── models/
│   ├── BanglaT5.ipynb
│   ├── ByT5_small.ipynb
│   ├── mT5_small.ipynb
│   ├── mT5_base.ipynb
│   ├── mBART50.ipynb
│   ├── BLOOM-560M.ipynb
│   ├── BanglaGPT.ipynb
│   ├── BanglaBERT_EncoderDecoder.ipynb
│   └── Gemini.ipynb
│   └── IndicBART.ipynb
│   └── Merge.ipynb
│
├── outputs/
│   ├── Bangla-T5.csv
│   ├── ByT5-small.csv
│   ├── mT5-small.csv
│   ├── mT5-base.csv
│   ├── mBART50.csv
│   ├── BLOOM-560M.csv
│   ├── BanglaGPT.csv
│   ├── BanglaBERT.csv
│   └── Gemini.csv
│
├── evaluation/
│   └── model_comparison.xlsx
│
├── README.md
├── LICENSE
└── .gitignore
```

---

## Dataset

The BanglaCounter dataset contains **3,011** Bangla offensive text and counterspeech pairs.

Each record includes:

- Offensive text
- Counterspeech response
- Harmful text category
- Counterspeech strategy
- Record ID

The dataset was cleaned, anonymized, and checked for duplicate records before experimentation.

---

## Evaluated Models

The following models were evaluated:

- Bangla-T5
- ByT5-small
- mT5-small
- mT5-base
- mBART50
- BLOOM-560M
- BanglaGPT
- BanglaBERT Encoder–Decoder
- Gemini

Each model was evaluated on the same benchmark using identical evaluation settings.

---

## Evaluation Metrics

### Lexical Similarity

- BLEU-1
- BLEU-2
- BLEU-3
- BLEU-4
- ROUGE-1
- ROUGE-2
- ROUGE-L
- METEOR

### Semantic Similarity

- BERTScore Precision
- BERTScore Recall
- BERTScore F1

### Diversity

- Diversity
- Distinct-1
- Distinct-2

### Originality and Memorization

- Novelty
- Average Maximum Train Similarity
- Near Copy Rate

### Safety

- Abuse-word Rate
- Abusive Outputs

### Generation Quality

- Average Generated Length
- Empty Output Rate

---

## Generated Outputs

The `outputs/` directory contains the generated counterspeech responses produced by each evaluated model.

These outputs are the original model predictions used during evaluation and have not been manually edited.

---

## Model Comparison

The final evaluation results are provided in:

```
evaluation/model_comparison.xlsx
```

This file contains all reported evaluation metrics for every model.

---

## Citation

If you use this dataset or repository in your research, please cite:

```
@mastersthesis{BanglaCounter2026,
  title={BanglaCounter:  Benchmark Dataset and Transformer-Based Evaluation Framework for Bangla Counterspeech},
  author={YOUR NAME},
  school={YOUR UNIVERSITY},
  year={2026}
}
```

---

## License

This repository is released under the MIT License.

---

## Contact

For questions or suggestions, please open an Issue on GitHub.

## Authors

- Md Sakib Hasan
- Shihaful Islam Ornob