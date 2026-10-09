#!/usr/bin/env python3
"""Exploratory token-set Jaccard screen across all three split boundaries.

This screens text overlap, not whether a response is safe or a model copied it.
Usage: python check_partition_similarity.py DATA.csv SPLIT.csv --out screen.csv
"""
import argparse
import collections
import csv
import pathlib
import unicodedata


def tokens(s):
    return set(unicodedata.normalize("NFC", s).strip().split())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("data", type=pathlib.Path)
    p.add_argument("split", type=pathlib.Path)
    p.add_argument("--out", type=pathlib.Path, default=pathlib.Path("similarity_screen.csv"))
    p.add_argument("--threshold", type=float, default=0.70)
    args = p.parse_args()
    with args.data.open(encoding="utf-8-sig", newline="") as f:
        records = {r["id"]: r for r in csv.DictReader(f)}
    with args.split.open(encoding="utf-8", newline="") as f:
        parts = {r["id"]: r["partition"] for r in csv.DictReader(f)}
    if set(records) != set(parts):
        raise ValueError("Data and split manifests have different ID sets")
    output = []
    comparisons = [("validation", "train"), ("test", "train"), ("test", "validation")]
    for field in ("offensive_text", "counterspeech_text"):
        for held_partition, compare_partition in comparisons:
            others = [(i, tokens(records[i][field])) for i in records if parts[i] == compare_partition]
            inverted = collections.defaultdict(set)
            for index, (_, words) in enumerate(others):
                for word in words:
                    inverted[word].add(index)
            for held_id in records:
                if parts[held_id] != held_partition:
                    continue
                words = tokens(records[held_id][field])
                candidates = set().union(*(inverted[word] for word in words)) if words else set()
                best = (0.0, "")
                for index in candidates:
                    other_id, other_words = others[index]
                    union = words | other_words
                    score = len(words & other_words) / len(union) if union else 1.0
                    if score > best[0] or score == best[0] and other_id < best[1]:
                        best = (score, other_id)
                output.append((field, held_id, held_partition, compare_partition, best[1], f"{best[0]:.6f}", int(best[0] >= args.threshold)))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["field", "held_out_id", "held_out_partition", "comparison_partition", "closest_comparison_id", "max_token_set_jaccard", "at_or_above_threshold"])
        w.writerows(output)
    summary = collections.Counter((r[0], r[2], r[3]) for r in output if r[6])
    for key in sorted({(r[0], r[2], r[3]) for r in output}):
        print(f"{key[0]} {key[1]} vs {key[2]}: {summary[key]} of {sum((r[0],r[2],r[3])==key for r in output)} >= {args.threshold}")


if __name__ == "__main__":
    main()
