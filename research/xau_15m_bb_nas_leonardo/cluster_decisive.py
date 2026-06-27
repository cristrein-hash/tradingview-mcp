#!/usr/bin/env python3
"""CONTROLE DECISIVO: o COMBO (SELL-cluster+NAS-LONG) prediz o RALI PRA FRENTE — ou só reflete a perna-de-queda
anterior (mecânico)? Para cada mínima fractal: combo(causal janela atrás) + fwd_rev (excursão pra frente, alvo real)
+ down_leg (queda que entrou no fundo). Compara combo vs não-combo DENTRO de buckets de down_leg. Se combo não bate
não-combo no mesmo bucket → mecânico (é a queda, não o bubble). RAW-causal. 2026-06-26."""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
SZ={"S":1,"M":2,"L":3}; PRE=16*900; K=4; HOR=192; BUF=0.25
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}
NAS={k:sorted([e for e in PRIM[k]["nas_events"] if e.get("t") and e.get("dir")],key=lambda x:x["t"]) for k in PRIM}
def win(key,t):
    bb=BUB[key]; ts=[x["t"] for x in bb]; a=bisect.bisect_left(ts,t-PRE); b=bisect.bisect_right(ts,t)
    sw=bw=0
    for x in bb[a:b]:
        w=SZ[x["size"]]; sw+=w if x["side"]=="SELL" else 0; bw+=w if x["side"]=="BUY" else 0
    cor=(sw/(sw+bw)) if (sw+bw)>0 else None
    ne=NAS[key]; nt=[x["t"] for x in ne]; c=bisect.bisect_left(nt,t-PRE); e=bisect.bisect_right(nt,t)
    nl=sum(1 for x in ne[c:e] if x["dir"]=="LONG")
    return cor,(sw+bw),nl
def fwd_rev(s,p):
    Lp=s[p]["l"]; a=s[p]["atr"] or 1.0; ext=Lp; end=min(p+HOR,len(s)-1)
    for i in range(p+1,end+1):
        if s[i]["l"]<Lp-BUF*a: break
        ext=max(ext,s[i]["h"])
    return (ext-Lp)/a
def fractal_lows(s):
    L=[x["l"] for x in s]; return [p for p in range(max(K,PRE//900),len(s)-K) if L[p]==min(L[p-K:p+K+1])]
blk_med={}
for k in PRIM:
    s=PRIM[k]["series"]; v=[win(k,s[i]["t"])[1] for i in range(60,len(s),50)]; v=[x for x in v if x>0]; blk_med[k]=st.median(v) if v else 1
rows=[]
for k,pr in PRIM.items():
    s=pr["series"]
    for p in fractal_lows(s):
        cor,tot,nl=win(k,s[p]["t"]); a=s[p]["atr"] or 1.0
        if cor is None: continue
        combo=(cor>0.5 and nl>=1 and tot/blk_med[k]>=1.0)
        dl=(s[p-PRE//900]["c"]-s[p]["l"])/a   # queda que entrou (positivo = caiu no fundo)
        rows.append({"combo":combo,"fwd":fwd_rev(s,p),"dl":dl})
def mean(v): return st.mean(v) if v else 0
print(f"candidatos fractais: {len(rows)} | COMBO: {sum(1 for r in rows if r['combo'])}")
cb=[r for r in rows if r["combo"]]; nc=[r for r in rows if not r["combo"]]
print(f"\nGERAL  fwd_rev médio: COMBO={mean([r['fwd'] for r in cb]):.1f}ATR | não-COMBO={mean([r['fwd'] for r in nc]):.1f}ATR")
print(f"       %que viram true (fwd>=8): COMBO={100*sum(1 for r in cb if r['fwd']>=8)/len(cb):.0f}% | não-COMBO={100*sum(1 for r in nc if r['fwd']>=8)/len(nc):.0f}%")
print("\nCONTROLADO por perna-de-queda anterior (down_leg em ATR):")
print("  bucket dl |  n_combo  fwd_combo | n_nc  fwd_nc | Δ(combo-nc)")
for lo,hi in [(-99,1),(1,3),(3,6),(6,99)]:
    cbb=[r for r in cb if lo<=r["dl"]<hi]; ncb=[r for r in nc if lo<=r["dl"]<hi]
    if cbb and ncb:
        d=mean([r['fwd'] for r in cbb])-mean([r['fwd'] for r in ncb])
        print(f"   {lo:>3}..{hi:<3} |  {len(cbb):>4}    {mean([r['fwd'] for r in cbb]):>5.1f}  | {len(ncb):>4} {mean([r['fwd'] for r in ncb]):>5.1f} | {d:+.1f}")
print("\n  → se Δ≈0 em cada bucket de queda = COMBO NÃO prediz rali além da queda (MECÂNICO). Δ>0 consistente = REAL.")
