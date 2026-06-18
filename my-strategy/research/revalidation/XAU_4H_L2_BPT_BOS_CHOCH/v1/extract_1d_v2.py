import json,sys
BUY={'plot_0','plot_2','plot_4'}
buy_times=set(); nas_long_days={}; prev=None
for line in sys.stdin:
    try: d=json.loads(line)
    except: continue
    t=d.get('replay_current_date')
    if t is None: continue
    # NAS long count
    pl=d.get('pine_labels') or []
    nas=next((s for s in pl if 'NAS' in (s.get('name') or '')),None)
    labs=(nas.get('all_labels') or nas.get('labels') or []) if nas else []
    nlong=sum(1 for l in labs if (l.get('text') or '').upper()=='LONG')
    nas_long_days[int(t)]=1 if (prev is not None and nlong>prev) else 0; prev=nlong
    # BUY bubble activations (collect global timeline)
    mob=next((s for s in (d.get('pine_shapes_bubbles') or []) if 'Order' in (s.get('name') or '')),None)
    for a in (mob.get('activations') or []) if mob else []:
        sh=a.get('shapes') or {}
        if any(p in BUY for p in sh): buy_times.add(int(a.get('time')))
json.dump({'nas_long_days':nas_long_days,'buy_times':sorted(buy_times)},open('/tmp/d1_signals_v2.json','w'))
print("nas_long_new days:",sum(nas_long_days.values()),"| BUY bubble distinct times:",len(buy_times))
