import sys, csv, gzip, json, pickle
from pathlib import Path
from datetime import datetime, timezone
L1=Path("my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0,str(L1)); sys.path.insert(0,"my-strategy/core")
import scanner
S=scanner.build_series()
recs,surv,MONU=pickle.load(open('/tmp/v2recs.pkl','rb'))
def to_u(ts): return int(datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp())
def _f(x):
    try: return float(str(x).replace(' ','').replace('−','-'))
    except: return None
cand_i={x["id"]:(S.idx[to_u(x["ts"])]) for x in recs if to_u(x["ts"]) in S.idx}
want={S.T[cand_i[x["id"]]-1] for x in surv}
snap={}
with gzip.open(scanner.RAW,'rt') as f:
    for line in f:
        if '"replay_current_date"' not in line: continue
        r=json.loads(line); ov=r.get('ohlcv') or []
        if not ov: continue
        cur=max(b['time'] for b in ov)
        if cur not in want: continue
        for s in (r.get('study_values') or []):
            if 'NAS' in s.get('name',''): snap[cur]=_f((s.get('values') or {}).get('NAS_DISTANCE_FROM_EMA_ATR'))
for x in surv: x["nas_shift1"]=snap.get(S.T[cand_i[x["id"]]-1])
def metr(g):
    t=sum(1 for x in g if x["res"]=="TARGET");s=sum(1 for x in g if x["res"]=="STOP")
    sr=round(sum(x["R"] for x in g),1);pos=sum(x["R"] for x in g if x["R"]>0);neg=abs(sum(x["R"] for x in g if x["R"]<0))
    return f"n={len(g)} T={t} S={s} TM={len(g)-t-s} sumR={sr} avgR={round(sr/len(g),2)} PF={round(pos/neg,2) if neg else None} hit={round(100*t/len(g))}%"
# cenários (SHIFT1 causal p/ NAS; price/time causais)
SCEN={
 "STACK_v1(base)": lambda x: True,
 "A_ultra(atr_ratio<=0.0081 & dow<=4)": lambda x: x["atr_ratio"]<=0.0081 and x["dow"]<=4,
 "B_monu_safe(nas_dist_shift1>=1.29)": lambda x: x.get("nas_shift1") is not None and x["nas_shift1"]>=1.29,
 "C_expmax(nas_dist_shift1>=1.31)": lambda x: x.get("nas_shift1") is not None and x["nas_shift1"]>=1.31,
 "D_simple(atr_ratio<=0.0081)": lambda x: x["atr_ratio"]<=0.0081,
}
print("BASELINE 63:", metr(recs))
for nm,pred in SCEN.items():
    g=[x for x in surv if pred(x)]
    lw=sorted([(x["id"],x["mfe"]) for x in surv if x["res"]=="TARGET" and not pred(x)],key=lambda a:int(a[0]))
    ml=sorted(MONU-{x["id"] for x in g},key=int)
    rem=sorted([x["id"] for x in surv if not pred(x)],key=int)
    print(f"{nm}: {metr(g)} | winners_perdidos={lw} | monumentais_perdidos={ml} | removidos={rem}")
# CSV: 49 survivors com features + membership
fields=["id","ts","status","res","R","mfe","ret5","ext_ema","zone_w","dist_zone","rsi_vs_ma","atr_ratio","dow","hour","nas_shift1"]+["in_A","in_B","in_C","in_D"]
with open(L1/"reports/l1_discriminator_filter_v2.csv","w",newline="") as fo:
    w=csv.DictWriter(fo,fieldnames=fields,lineterminator="\n");w.writeheader()
    for x in sorted(surv,key=lambda z:z["ts"]):
        row={k:x.get(k) for k in fields if k in x}
        row["in_A"]=SCEN["A_ultra(atr_ratio<=0.0081 & dow<=4)"](x)
        row["in_B"]=SCEN["B_monu_safe(nas_dist_shift1>=1.29)"](x)
        row["in_C"]=SCEN["C_expmax(nas_dist_shift1>=1.31)"](x)
        row["in_D"]=SCEN["D_simple(atr_ratio<=0.0081)"](x)
        w.writerow(row)
print("\nCSV escrito:", L1/"reports/l1_discriminator_filter_v2.csv")
