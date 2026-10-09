#!/usr/bin/env python3
"""Recalculate Novelty and Near Copy Rate with word-level normalized Levenshtein.

Usage: python compute_word_levenshtein.py DATA.csv SPLITS.csv PREDICTIONS_DIR --out results/word_levenshtein_audit.json
Requires a C++17 compiler. The saved model predictions and reconstructed split are inputs;
this does not independently establish which historical training partition was used.
"""
import argparse
import csv
import json
import pathlib
import subprocess
import tempfile
from verify_predictions import FILES, load

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('data',type=pathlib.Path)
    ap.add_argument('split',type=pathlib.Path)
    ap.add_argument('predictions_dir',type=pathlib.Path)
    ap.add_argument('--out',type=pathlib.Path,default=pathlib.Path('results/word_levenshtein_audit.json'))
    a=ap.parse_args()
    data=load(a.data)
    partitions={r['id']:r['partition'] for r in load(a.split)}
    train=[r['counterspeech_text'].split() for r in data if partitions[r['id']]=='train']
    preds={name:load(a.predictions_dir/filename) for name,filename in FILES.items()}
    refmap={r['counterspeech_text']:r['id'] for r in data}
    ids=[]
    for name, rows in preds.items():
        this=[refmap[r['reference_counterspeech']] for r in rows]
        if len(rows)!=302 or any(partitions[x]!='test' for x in this):
            raise ValueError(f'{name}: 302 test references required')
        if not ids:ids=this
        elif this!=ids:raise ValueError(f'{name}: test order mismatch')
    tokens={}
    def encode(seq):
        out=[]
        for t in seq:
            if t not in tokens:tokens[t]=len(tokens)+1
            out.append(tokens[t])
        return f'{len(out)} '+ ' '.join(map(str,out))
    lines=[f'{len(train)} {len(preds)} 302']
    lines.extend(encode(s) for s in train)
    for rows in preds.values():lines.extend(encode(r['generated_counterspeech'].split()) for r in rows)
    cpp=pathlib.Path(__file__).with_name('word_levenshtein.cpp')
    with tempfile.TemporaryDirectory() as temp:
        binary=pathlib.Path(temp)/'word_levenshtein'
        subprocess.run(['g++','-std=c++17','-O2',str(cpp),'-o',str(binary)],check=True)
        proc=subprocess.run([str(binary)],input='\n'.join(lines)+'\n',text=True,capture_output=True,check=True)
    maxima={name:[] for name in preds}
    names=list(preds)
    for line in proc.stdout.splitlines():
        mi,ri,score=line.split()
        if int(ri)!=len(maxima[names[int(mi)]]):raise ValueError('Output order mismatch')
        maxima[names[int(mi)]].append(float(score))
    results={}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with (a.out.parent/'word_levenshtein_per_row.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['model','test_row','dataset_id','maximum_similarity'])
        for name,scores in maxima.items():
            results[name]={
                'Novelty':round(1-sum(scores)/len(scores),8),
                'Near Copy Rate':round(sum(s>=.70 for s in scores)/len(scores),8),
                'near_copy_count':sum(s>=.70 for s in scores),
                'test_rows':len(scores)
            }
            w.writerows((name,i,ids[i-1],f'{s:.12f}') for i,s in enumerate(scores,1))
    a.out.write_text(json.dumps({'definition':'similarity = 1 - word-level Levenshtein distance / max token length; empty/empty = 1',
       'threshold':0.70,'training_partition':'reconstructed seed-42 split','models':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
