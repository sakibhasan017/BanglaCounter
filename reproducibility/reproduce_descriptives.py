#!/usr/bin/env python3
"""Reproduce manuscript Tables 2, 3, 5 and Figure 1 from version-5 CSV."""
import argparse,csv,json,statistics,unicodedata,collections
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('csv_path',type=Path)
p.add_argument('--out-dir',type=Path,default=Path('descriptive_outputs'))
a=p.parse_args()
with a.csv_path.open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f);rows=list(reader);headers=reader.fieldnames
if len(rows)!=3011 or len(headers)!=13:raise ValueError('Expected 3,011 records and 13 fields')
out=a.out_dir;out.mkdir(parents=True,exist_ok=True)
labels={k:dict(collections.Counter(r[k] for r in rows)) for k in
        ('counterspeech_type_final','text_type_final')}
lengths={}
for key in ('offensive_text','counterspeech_text','offensive_text_en','counterspeech_text_en'):
    v=[len(unicodedata.normalize('NFC',r[key]).strip().split()) for r in rows]
    lengths[key]={'mean':round(statistics.mean(v),2),'median':statistics.median(v),'min':min(v),'max':max(v)}
result={'N':len(rows),'fields':headers,'unique_ids':len({r['id'] for r in rows}),
        'missing_cells':sum(not str(r[h]).strip() for r in rows for h in headers),
        'unique_offensive_texts':len({r['offensive_text'] for r in rows}),
        'unique_responses':len({r['counterspeech_text'] for r in rows}),
        'duplicate_pairs':len(rows)-len({(r['offensive_text'],r['counterspeech_text']) for r in rows}),
        'labels':labels,'word_lengths':lengths}
(out/'tables_2_3_5.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except ImportError:
    print('Matplotlib not available: JSON written; Figure 1 not generated')
else:
    orders=[('counterspeech_type_final',('discouraging_abuse','moral_appeal','fact_based','empathy','warning_of_consequences')),
            ('text_type_final',('gender_abuse','religious_hate','abusive_language','family_insult','political_abuse','personal_insult','threat'))]
    fig,axs=plt.subplots(1,2,figsize=(11.8,4.5),layout='constrained')
    for ax,(key,order),color,title in zip(axs,orders,('#286999','#ae4a39'),('Counterspeech strategies','Offensive-content categories')):
        vals=[labels[key][x] for x in order]
        bars=ax.barh([x.replace('_',' ').capitalize() for x in order],vals,color=color)
        ax.invert_yaxis();ax.set_title(title);ax.set_xlabel('Final-label count')
        ax.set_xlim(0,max(vals)*1.17)
        for b,v in zip(bars,vals):ax.text(v+5,b.get_y()+b.get_height()/2,str(v),va='center',fontsize=8)
        ax.spines[['top','right']].set_visible(False)
    fig.savefig(out/'Figure1_reproduced.png',dpi=300)
    plt.close(fig)
print(json.dumps(result,ensure_ascii=False,indent=2))
