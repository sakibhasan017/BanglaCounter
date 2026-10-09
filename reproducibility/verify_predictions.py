#!/usr/bin/env python3
"""Validate five Table 6 prediction CSVs and recompute five reported metrics.

Usage: python verify_predictions.py DATA.csv SPLITS.csv PREDICTIONS_DIR --out results/prediction_audit.json
The prediction files in PREDICTIONS_DIR must have the canonical names listed
in README.md. All inputs are read-only; outputs contain aggregate statistics.
"""
import argparse
import collections
import csv
import hashlib
import json
import math
import pathlib
import re
from sklearn.model_selection import train_test_split

FILES = {
    'BLOOM-560M': 'bloom_560m_test_predictions.csv',
    'mBART50': 'mbart50_test_predictions.csv',
    'ByT5-small': 'byt5_small_test_predictions.csv',
    'mT5-base': 'mt5_base_test_predictions.csv',
    'BanglaGPT': 'banglagpt_test_predictions.csv',
}

def load(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def clean(s):
    return re.sub(r'\s+', ' ', s.strip()).replace('\u200c', '').replace('\u200d', '')

def bleu4(h, r):
    """Sentence BLEU-4, clipped precision, brevity penalty, method-1 ε=.1."""
    if not h or not r or not set(h).intersection(r):
        return 0.
    precisions=[]
    for n in range(1, 5):
        hc=collections.Counter(tuple(h[i:i+n]) for i in range(len(h)-n+1))
        rc=collections.Counter(tuple(r[i:i+n]) for i in range(len(r)-n+1))
        numerator=sum(min(v,rc[k]) for k,v in hc.items())
        denominator=max(1,sum(hc.values()))
        precisions.append(numerator/denominator if numerator else 0.1/denominator)
    bp=1 if len(h)>len(r) else math.exp(1-len(r)/len(h))
    return bp*math.exp(sum(math.log(x) for x in precisions)/4)

def rouge_l(h,r):
    if not h or not r:return 0.
    dp=[0]*(len(r)+1)
    for x in h:
        old=0
        for j,y in enumerate(r,1):
            prev=dp[j]
            dp[j]=old+1 if x==y else max(dp[j],dp[j-1])
            old=prev
    return 2*dp[-1]/(len(h)+len(r))

def mean(values):
    return sum(values)/len(values)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('data',type=pathlib.Path)
    ap.add_argument('split',type=pathlib.Path)
    ap.add_argument('predictions_dir',type=pathlib.Path)
    ap.add_argument('--out',type=pathlib.Path,default=pathlib.Path('prediction_audit.json'))
    args=ap.parse_args()
    data=load(args.data)
    by_ref={r['counterspeech_text']:r for r in data}
    if len(by_ref)!=len(data):raise ValueError('Reference responses are not unique')
    split={r['id']:r['partition'] for r in load(args.split)}
    train=[set(clean(r['counterspeech_text']).split()) for r in data if split[r['id']]=='train']
    results={}
    order=None
    for model,filename in FILES.items():
        p=args.predictions_dir/filename
        rows=load(p)
        required={'input_text','reference_counterspeech','generated_counterspeech'}
        if not rows or not required.issubset(rows[0]):raise ValueError(f'{model}: missing columns')
        ids=[];hlist=[];rlist=[]
        for row in rows:
            ref=row['reference_counterspeech']
            if ref not in by_ref:raise ValueError(f'{model}: reference not in released dataset')
            source=by_ref[ref]
            ids.append(source['id'])
            if split[source['id']]!='test':raise ValueError(f'{model}: non-test ID {source["id"]}')
            if clean(source['offensive_text']) not in clean(row['input_text']):
                raise ValueError(f'{model}: input mismatch ID {source["id"]}')
            hyp=row['generated_counterspeech'].split()
            if 'generated_length' in row and int(row['generated_length'])!=len(hyp):
                raise ValueError(f'{model}: generated length mismatch ID {source["id"]}')
            hlist.append(hyp)
            rlist.append(ref.split())
        if len(ids)!=302 or len(set(ids))!=302:raise ValueError(f'{model}: expected 302 unique test IDs')
        if order is None:order=ids
        elif order!=ids:raise ValueError(f'{model}: test order differs')
        uni=[x for h in hlist for x in h]
        bi=[(a,b) for h in hlist for a,b in zip(h,h[1:])]
        distinct1=len(set(uni))/len(uni)
        distinct2=len(set(bi))/len(bi)
        maxima=[]
        for h in hlist:
            s=set(h)
            maxima.append(max((len(s&t)/len(s|t) for t in train if s and t),default=0))
        results[model]={
            'filename':filename,
            'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
            'test_rows':len(ids),
            'unique_test_ids':len(set(ids)),
            'reference_and_input_match_released_csv':True,
            'predicted_word_lengths_match_column':True,
            'BLEU-4':round(mean([bleu4(h,r) for h,r in zip(hlist,rlist)]),8),
            'ROUGE-L':round(mean([rouge_l(h,r) for h,r in zip(hlist,rlist)]),8),
            'Diversity':round((distinct1+distinct2)/2,8),
            'Novelty':round(1-mean(maxima),8),
            'Near Copy Rate':round(sum(x>=.70 for x in maxima)/len(maxima),8),
            'near_copy_count':sum(x>=.70 for x in maxima),
        }
    # The manifest is in source row order; the notebooks and prediction files
    # use the second train_test_split return order.
    results['test_ids_match_manifest']=(set(order)=={i for i,p in split.items() if p=='test'})
    _, temp=train_test_split([r['id'] for r in data],test_size=.20,random_state=42,shuffle=True)
    _, test=train_test_split(temp,test_size=.50,random_state=42,shuffle=True)
    results['test_id_order_matches_two_stage_seed42']=(order==test)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (args.out.parent/'prediction_row_ids.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['prediction_row_number_1_based','dataset_id','partition'])
        writer.writerows((i,record_id,'test') for i,record_id in enumerate(order,1))
    for model in FILES:
        r=results[model]
        print(model,*(f'{k}={r[k]:.4f}' for k in ['BLEU-4','ROUGE-L','Diversity','Novelty']),f'near={r["near_copy_count"]}/302')

if __name__=='__main__':main()
