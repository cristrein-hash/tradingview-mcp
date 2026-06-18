import json,sys
import os
BUY={'plot_0','plot_2','plot_4'}
nas_by_bar={}; buy_by_bar={}; prev=None
for line in sys.stdin:
    try: d=json.loads(line)
    except: continue
    ov=d.get('ohlcv') or []
    if not ov: continue
    bt=int(ov[-1]['time'])  # CURRENT bar time = aligns with dt
    pl=d.get('pine_labels') or []
    nas=next((s for s in pl if 'NAS' in (s.get('name') or '')),None)
    labs=(nas.get('all_labels') or nas.get('labels') or []) if nas else []
    nlong=sum(1 for l in labs if (l.get('text') or '').upper()=='LONG')
    nas_by_bar[bt]=1 if (prev is not None and nlong>prev) else 0; prev=nlong
    mob=next((s for s in (d.get('pine_shapes_bubbles') or []) if 'Order' in (s.get('name') or '')),None)
    nbuy=0
    for a in (mob.get('activations') or []) if mob else []:
        if any(p in BUY for p in (a.get('shapes') or {})): nbuy+=1  # total BUY activations visible
    buy_by_bar[bt]=nbuy
json.dump({'nas':nas_by_bar,'buy':buy_by_bar},open(os.environ.get('L2_D1_SIG','/tmp/d1_sig_v3.json'),'w'))
print("bars:",len(nas_by_bar),"nas_long_new:",sum(nas_by_bar.values()),"max buy/bar:",max(buy_by_bar.values()))
