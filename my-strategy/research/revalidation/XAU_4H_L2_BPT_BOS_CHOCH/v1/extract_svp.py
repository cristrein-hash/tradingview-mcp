import json,sys
import os
bars={}
for line in sys.stdin:
    try: d=json.loads(line)
    except: continue
    svp=d.get('session_vp') or {}
    for e in (svp.get('last3') or []):
        v=e.get('v') or []
        if len(v)>=4:
            t=int(v[0]); bars.setdefault(t,{})['vp']=[v[1],v[2],v[3]]  # POC,VAH,VAL
    # real volume + rsi per current bar
    ov=d.get('ohlcv') or []
    if ov:
        b=ov[-1]; t=int(b['time']); bars.setdefault(t,{})['vol']=b.get('volume'); bars[t]['close']=b.get('close')
    sv=d.get('study_values') or []
    rsi=next((s for s in sv if 'Strength' in (s.get('name') or '')),None)
    if rsi and ov:
        try: bars[int(ov[-1]['time'])]['rsi']=float((rsi.get('values') or {}).get('RSI'))
        except: pass
out=open(os.environ.get('L2_SVP','/tmp/svp_bars.jsonl'),'w'); nvp=0
for t in sorted(bars):
    r=bars[t]; r['time']=t
    if 'vp' in r: nvp+=1
    out.write(json.dumps(r)+"\n")
out.close()
print("bars:",len(bars),"with VP:",nvp)
# sanity: VAH>=POC>=VAL?
import random
ok=0;tot=0
for t in list(bars)[:500]:
    vp=bars[t].get('vp')
    if vp: tot+=1; ok+= 1 if (vp[1]>=vp[0]>=vp[2]) else 0
print(f"VAH>=POC>=VAL holds {ok}/{tot} (confirms v=[POC,VAH,VAL])")
