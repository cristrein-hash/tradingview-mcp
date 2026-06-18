#!/usr/bin/env python3
"""FIDELITY GATE — compara o frozen reconstruído vs referência (SHA 9fac96b9), field-by-field.
PASS = byte-identical OU field-equivalent nos campos CRÍTICOS (ts, OHLC, volume, rsi, bubbles_recent, nas_recent).
smc_recent = não-crítico (não usado downstream). Reporta diffs."""
import json, sys, hashlib

REF=sys.argv[1] if len(sys.argv)>1 else '/tmp/raw_features_2020_2026.jsonl'
REB=sys.argv[2] if len(sys.argv)>2 else '/tmp/rebuilt_raw_features.jsonl'
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''):h.update(c)
    return h.hexdigest()
rf={json.loads(l)['ts_epoch']:json.loads(l) for l in open(REF)}
rb={json.loads(l)['ts_epoch']:json.loads(l) for l in open(REB)}
print(f"REF bars={len(rf)} sha={sha(REF)[:12]}")
print(f"REB bars={len(rb)} sha={sha(REB)[:12]}")
print("BYTE-IDENTICAL:", "YES" if sha(REF)==sha(REB) else "NO")
common=sorted(set(rf)&set(rb)); only_ref=set(rf)-set(rb); only_reb=set(rb)-set(rf)
print(f"bars comuns={len(common)} | só-ref={len(only_ref)} | só-reb={len(only_reb)}")
def fl(x): return round(x,6) if isinstance(x,(int,float)) else x
CRIT=['open','high','low','close','volume','rsi']
diffs={k:0 for k in CRIT+['bubbles_recent','nas_recent','smc_recent']}
ex={}
for t in common:
    a,b=rf[t],rb[t]
    for k in CRIT:
        va,vb=a.get(k),b.get(k)
        if isinstance(va,float) or isinstance(vb,float):
            if va is None or vb is None:
                if va!=vb: diffs[k]+=1; ex.setdefault(k,(t,va,vb))
            elif abs(va-vb)>1e-6: diffs[k]+=1; ex.setdefault(k,(t,va,vb))
        elif va!=vb: diffs[k]+=1; ex.setdefault(k,(t,va,vb))
    # bubbles_recent: comparar conjunto (plot_id,bars_ago,time)
    sa=sorted((x['plot_id'],x['bars_ago'],x['time']) for x in (a.get('bubbles_recent') or []))
    sb=sorted((x['plot_id'],x['bars_ago'],x['time']) for x in (b.get('bubbles_recent') or []))
    if sa!=sb: diffs['bubbles_recent']+=1; ex.setdefault('bubbles_recent',(t,len(sa),len(sb)))
    # nas_recent: comparar (text,x) multiset
    na=sorted((x['text'],x['x']) for x in (a.get('nas_recent') or []))
    nb=sorted((x['text'],x['x']) for x in (b.get('nas_recent') or []))
    if na!=nb: diffs['nas_recent']+=1; ex.setdefault('nas_recent',(t,len(na),len(nb)))
    sc_a=sorted((x['text'],x['x']) for x in (a.get('smc_recent') or []))
    sc_b=sorted((x['text'],x['x']) for x in (b.get('smc_recent') or []))
    if sc_a!=sc_b: diffs['smc_recent']+=1; ex.setdefault('smc_recent',(t,len(sc_a),len(sc_b)))
print("\n=== DIFFS por campo (de",len(common),"bars comuns) ===")
for k in CRIT+['bubbles_recent','nas_recent','smc_recent']:
    crit='CRIT' if k in CRIT or k in('bubbles_recent','nas_recent') else 'noncrit'
    mm=100*(len(common)-diffs[k])/len(common) if common else 0
    print(f"  {k:<16} {crit:<8} match={mm:6.2f}%  diffs={diffs[k]}  ex={ex.get(k)}")
crit_fields=CRIT+['bubbles_recent','nas_recent']
crit_ok=all(diffs[k]==0 for k in crit_fields) and not only_ref and not only_reb
print("\nGATE (campos críticos field-equivalent + mesmo bar-set):", "PASS" if crit_ok else "FAIL")
