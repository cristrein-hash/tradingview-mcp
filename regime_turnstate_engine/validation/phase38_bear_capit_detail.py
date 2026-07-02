#!/usr/bin/env python3
"""Cris: nas 11 BEAR-capitulação (dist<=-2 ao bottom do regime anterior), o que FALHA nos 55% (6 losers)?
Caracterizar cada uma, estrutural + flexível. Hipóteses: (a) há OUTRO nível estrutural mais abaixo (lo de regime
ainda anterior) que o preço vai buscar = capitulou no nível errado; (b) exaustão (RSI) insuficiente; (c) furou fundo
demais (queda-livre) vs pouco; (d) making-new-low (ainda a cair) vs bounce. Níveis causais (lo de regimes já detectados).
raw_features p/ rsi. let-run−0.35. Deixar o padrão emergir."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C
def atrb(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
Dr=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1")
raw={int(json.loads(l)["ts_epoch"]):json.loads(l) for l in open(Dr/"repro_recovery/raw_features_2020_2026.jsonl")}
def seg_idx(t):
    for i in range(len(segs)):
        if segs[i]['start']<=t<=segs[i]['end']: return i
    return None
D=Dr/"results"
rows=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0: continue
    s=segs[idx]
    if s['regime']!='BEAR': continue
    prev=segs[idx-1];a=atrb(bi);entry=float(r["entry"])
    dist=(entry-prev['lo'])/a
    if dist>-2: continue    # só capitulação-profunda
    # níveis estruturais ABAIXO do entry (lo de regimes anteriores < entry) = espaço p/ cair
    los_below=[segs[j]['lo'] for j in range(idx) if segs[j]['lo']<entry]
    n_below=len(los_below);nearest_below=(entry-max(los_below))/a if los_below else None
    lowest=min(segs[j]['lo'] for j in range(idx))
    room_to_floor=(entry-lowest)/a    # quanto acima do piso estrutural mais baixo
    # profundidade no bear + making-new-low
    i0=bisect.bisect_left(T,s['start'])
    drop_from_top=(s['hi']-entry)/a
    min_so_far=min(L[i0:bi+1]);making_low=entry<=min_so_far*1.003  # entry perto do low-so-far do bear
    d_i=raw.get(int(t)) or {};rsi=d_i.get("rsi")
    R=round(float(r["letrun_struct"])-0.35,2)
    rows.append({"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"dist":round(dist,1),"R":R,"win":R>0,
                 "n_below":n_below,"room_floor":round(room_to_floor,1),
                 "nearest_below":round(nearest_below,1) if nearest_below else None,
                 "drop_top":round(drop_from_top,1),"new_low":making_low,"rsi":rsi})
rows.sort(key=lambda x:x['date'])
print(f"BEAR-capitulação (dist<=-2): {len(rows)} trades ({sum(1 for x in rows if x['win'])}W/{sum(1 for x in rows if not x['win'])}L)\n")
print(f"{'date':11} {'R':>5} {'dist':>5} {'nBelow':>6} {'roomFloor':>9} {'nearBelow':>9} {'dropTop':>7} {'newLow':>6} {'rsi':>5}")
for x in rows:
    tag='WIN ' if x['win'] else 'loss'
    print(f"{x['date']:11} {x['R']:+5.1f} {x['dist']:5.1f} {x['n_below']:6} {x['room_floor']:9.1f} {str(x['nearest_below']):>9} {x['drop_top']:7.1f} {str(x['new_low']):>6} {str(round(x['rsi'],0) if x['rsi'] else None):>5}  {tag}")
# médias W vs L
import statistics as st
W=[x for x in rows if x['win']];Lz=[x for x in rows if not x['win']]
print("\n### média WIN vs LOSS (o que separa) ###")
for k in ('n_below','room_floor','drop_top','rsi'):
    wv=[x[k] for x in W if x[k] is not None];lv=[x[k] for x in Lz if x[k] is not None]
    if wv and lv: print(f"  {k:12} WIN {st.mean(wv):+7.2f}  vs LOSS {st.mean(lv):+7.2f}")
print(f"  making_new_low  WIN {100*sum(1 for x in W if x['new_low'])/len(W):.0f}%  vs LOSS {100*sum(1 for x in Lz if x['new_low'])/len(Lz):.0f}%")
