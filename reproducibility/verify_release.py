#!/usr/bin/env python3
"""Recalculate dataset summaries and a documented seed-42 split.

Usage: python verify_release.py path/to/BanglaCounter_EnglishTranslated.csv --out results
The input is not modified. Requires Python 3 and scikit-learn (for the split).
"""
import argparse
import collections
import csv
import hashlib
import json
import math
import pathlib
import unicodedata

from sklearn.model_selection import train_test_split

FIELDS = [
    "id", "offensive_text", "offensive_text_en", "counterspeech_text",
    "counterspeech_text_en", "counterspeech_type_annotator_1",
    "counterspeech_type_annotator_2", "counterspeech_type_annotator_3",
    "counterspeech_type_final", "text_type_annotator_1",
    "text_type_annotator_2", "text_type_annotator_3", "text_type_final",
]


def agreement(rows, columns):
    """Fleiss kappa and nominal Krippendorff alpha for complete 3-rater units."""
    n, m = len(rows), len(columns)
    labels = sorted({r[c] for r in rows for c in columns})
    totals = collections.Counter(r[c] for r in rows for c in columns)
    pair_agreement = sum(
        sum(v * (v - 1) for v in collections.Counter(r[c] for c in columns).values())
        / (m * (m - 1)) for r in rows
    ) / n
    pooled = {x: totals[x] / (n * m) for x in labels}
    chance_agreement = sum(v * v for v in pooled.values())
    kappa = (pair_agreement - chance_agreement) / (1 - chance_agreement)
    # Krippendorff's coincidence-matrix correction for finite pooled ratings.
    observed_disagreement = 1 - pair_agreement
    n_ratings = n * m
    expected_disagreement = 1 - sum(v * (v - 1) for v in totals.values()) / (n_ratings * (n_ratings - 1))
    alpha = 1 - observed_disagreement / expected_disagreement
    patterns = collections.Counter()
    wrong_majority = []
    for r in rows:
        votes = collections.Counter(r[c] for c in columns)
        if len(votes) == 1:
            patterns["unanimous"] += 1
        elif len(votes) == 2:
            patterns["two_to_one"] += 1
            if votes.most_common(1)[0][0] != r["counterspeech_type_final" if columns[0].startswith("counterspeech") else "text_type_final"]:
                wrong_majority.append(r["id"])
        else:
            patterns["three_different"] += 1
    return {
        "fleiss_kappa": round(kappa, 6), "krippendorff_alpha_nominal": round(alpha, 6),
        "agreement_patterns": dict(patterns), "majority_final_disagreements": wrong_majority,
        "pooled_rating_counts": dict(totals),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv_path", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path("results"))
    args = ap.parse_args()
    raw = args.csv_path.read_bytes()
    with args.csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        rows = list(reader)
    if columns != FIELDS:
        raise ValueError(f"Expected 13 columns in the documented order; received {columns!r}")
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Record IDs are duplicated")
    if len(rows) != 3011:
        raise ValueError(f"Expected 3011 records; received {len(rows)}")

    # Same two calls and order as the available model notebooks. The manifest
    # reconstructs the code path; it is not an archived run-time artifact.
    train_index, temp_index = train_test_split(list(range(len(rows))), test_size=0.2, random_state=42)
    val_index, test_index = train_test_split(temp_index, test_size=0.5, random_state=42)
    partitions = {i: "train" for i in train_index}
    partitions.update({i: "validation" for i in val_index})
    partitions.update({i: "test" for i in test_index})
    if len(partitions) != len(rows):
        raise AssertionError("Split does not cover all rows")

    def text_summary(key):
        values = [unicodedata.normalize("NFC", r[key]).strip() for r in rows]
        lengths = [len(v.split()) for v in values]
        return {"unique": len(set(values)), "word_min": min(lengths),
                "word_max": max(lengths), "word_mean": round(sum(lengths) / len(lengths), 4)}

    result = {
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "row_count": len(rows), "field_count": len(columns), "fields": columns,
        "ids_are_1_to_3011_in_order": ids == [str(i) for i in range(1, 3012)],
        "empty_cell_counts": {c: sum(not r[c].strip() for r in rows) for c in columns},
        "texts": {c: text_summary(c) for c in ["offensive_text", "counterspeech_text"]},
        "final_label_counts": {
            c: dict(collections.Counter(r[c] for r in rows))
            for c in ["counterspeech_type_final", "text_type_final"]
        },
        "strategy_agreement": agreement(rows, [f"counterspeech_type_annotator_{i}" for i in range(1, 4)]),
        "category_agreement": agreement(rows, [f"text_type_annotator_{i}" for i in range(1, 4)]),
        "split_method": "sklearn.model_selection.train_test_split indices in CSV row order: test_size=0.2, random_state=42; split temporary 50/50 with random_state=42",
        "split_counts": dict(collections.Counter(partitions.values())),
        "sklearn_version": __import__("sklearn").__version__,
    }
    for c in ("offensive_text", "counterspeech_text"):
        train_texts = {rows[i][c] for i in train_index}
        result[f"exact_test_to_train_overlap_{c}"] = sum(rows[i][c] in train_texts for i in test_index)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "release_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (args.out / "reconstructed_split_ids.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "partition"])
        writer.writerows((r["id"], partitions[i]) for i, r in enumerate(rows))
    print(json.dumps({k: result[k] for k in ("source_sha256", "row_count", "split_counts", "strategy_agreement", "category_agreement")}, indent=2))


if __name__ == "__main__":
    main()
