#!/usr/bin/env python3
"""CRUZA tiers de potência das reversões (reversal_power.csv) com as ENTRADAS 5ATR (Cris 2026-06-27).
Pergunta: os losers 5ATR caem em fundos FRACOS / em TOPOS / sem reversão? E isso ajuda a limpar losers CAUSALMENTE?
- Mapeia cada entrada 5ATR ao M8 reversal mais proximo do seu ANCHOR (low_t), dentro de ±W barras.
- Grupos: BOT por tier (MONSTRO/FORTE/MEDIO/FRACO) · TOP (mal-direcionado) · UNMATCHED (ancora nao e reversao real).
- WR/sumR/avgR por grupo, em 2 universos: base A2 (dedup) e os 170 finais.
⚠️ tier/match usam dado FORWARD (a perna so se conhece depois) → DIAGNOSTICO, NAO filtro causal.
- TESTE CAUSAL separado: existe proxy DISPONIVEL NA ENTRADA que aproxime o grupo loser-denso sem look-ahead?
RAW. Sem promover regra."""
import json, csv, bisect, statistics as st
from pathlib import Path
from filter_harness import ROWS, dedup, stats
HERE=Path(__file__).parent; BAR=900; W=3   # ±3 barras (45min) p/ casar ancora com reversao
REV=[ {**r,"t":int(r["t"]),"leg_atr":float(r["leg_atr"])} for r in csv.DictReader(open(HERE/"reversal_power.csv")) ]
REVt=sorted(REV,key=lambda r:r["t"]); RT=[r["t"] for r in REVt]
def nearest_rev(t):
    k=bisect.bisect_left(RT,t)
    best=None
    for j in (k-1,k,k+1):
        if 0<=j<len(REVt):
            d=abs(REVt[j]["t"]-t)
            if best is None or d<best[0]: best=(d,REVt[j])
    return best  # (dt_seg, rev)
def group_of(r):
    nb=nearest_rev(r["low_t"])
    if nb is None or nb[0] > W*BAR: return "UNMATCHED"
    rev=nb[1]
    if rev["kind"]=="TOP": return "TOP(mal-dir)"
    return "BOT-"+rev["tier"]

def report(univ,name):
    from collections import defaultdict
    g=defaultdict(list)
    for r in univ: g[group_of(r)].append(r)
    base=stats(univ)
    print(f"\n### {name}  (N={base['n']} WR={base['wr']}% sumR={base['sumr']} avgR={base['sumr']/base['n']:+.2f})")
    print(f"{'grupo':<16}{'n':>5}{'WR%':>7}{'sumR':>8}{'avgR':>7}{'%dos n':>8}")
    order=["BOT-MONSTRO","BOT-FORTE","BOT-MEDIO","BOT-FRACO","TOP(mal-dir)","UNMATCHED"]
    for k in order:
        rs=g.get(k,[])
        if not rs: continue
        n=len(rs); w=sum(x["win"] for x in rs); sm=sum(x["R"] for x in rs)
        print(f"{k:<16}{n:>5}{100*w/n:>7.1f}{sm:>8.1f}{sm/n:>+7.2f}{100*n/base['n']:>7.0f}%")
    # quao bem a ancora casa com reversao real (validacao do match)
    dts=[nearest_rev(r["low_t"])[0]/BAR for r in univ if nearest_rev(r["low_t"])]
    print(f"   match: {sum(1 for d in dts if d<=W)}/{len(univ)} ancoras ≤{W} barras de uma reversao | mediana Δ {st.median(dts):.0f} barras")
    return g

baseA2=dedup(ROWS)
report(baseA2,"BASE A2 5ATR (dedup)")

ids170={int(r["entry_t"]) for r in csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv"))}
u170=[r for r in baseA2 if r["t"] in ids170]
g170=report(u170,"170 FINAIS (A2+h1_eff+regime)")

# ---- TESTE CAUSAL: o grupo loser-denso tem proxy disponivel na entrada? ----
print("\n=== TESTE CAUSAL (proxies JA disponiveis na entrada vs grupo) ===")
print("tier e' forward; checar se UNMATCHED/FRACO/TOP correlacionam com features CAUSAIS ja no dataset")
import statistics as st2
feats=["leg_ext_atr","disp4_atr","h1_pos","h1_eff","dist_demand_atr","room_above_atr","macro_bear","rsi"]
groups={}
for r in baseA2: groups.setdefault(group_of(r),[]).append(r)
hdr=f"{'grupo':<16}"+"".join(f"{f[:9]:>10}" for f in feats)+f"{'n':>5}{'WR':>6}"
print(hdr)
for k in ["BOT-MONSTRO","BOT-FORTE","BOT-MEDIO","BOT-FRACO","TOP(mal-dir)","UNMATCHED"]:
    rs=groups.get(k,[])
    if not rs: continue
    line=f"{k:<16}"
    for f in feats:
        vals=[r[f] for r in rs if r.get(f) is not None]
        line+=f"{(st2.median(vals) if vals else float('nan')):>10.2f}"
    line+=f"{len(rs):>5}{100*sum(x['win'] for x in rs)/len(rs):>6.1f}"
    print(line)
print("\n(se nenhuma feature causal separa o grupo loser-denso, NAO da pra limpar via tier — tier so vive no futuro)")
