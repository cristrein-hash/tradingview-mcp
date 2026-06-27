#!/usr/bin/env python3
"""VALIDAÇÃO LIMPA (DA-recommended) do lead NY-sessão na base AMPLA sweep (n728). Reporta por ANO em R (não só WR),
por bloco net+, leave-one-out, streak/maxDD, e MEDIANA-por-bloco (não só sumR — base tem cauda direita). Bonferroni-aware:
NY é 1 de ~4 sessões testadas → tratar como LEAD, não gate. Causal. SEM grab de positivo. Verified 2026-06-26."""
import csv, datetime as dt, statistics as st
from pathlib import Path
HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "candidates_sweep.csv")))
for r in rows:
    d=dt.datetime.utcfromtimestamp(int(r["t"])); r["hr"]=d.hour; r["yr"]=d.year; r["R"]=float(r["R"]); r["w"]=r["win"]=="True"
ny=[r for r in rows if 13<=r["hr"]<19]
def full(sub,label):
    if not sub: print(f"  [{label}] vazio"); return
    n=len(sub);w=sum(1 for x in sub if x["w"]);sm=sum(x["R"] for x in sub)
    ts=sorted(sub,key=lambda x:int(x["t"]));eq=0;pk=0;dd=0;stk=0;mstk=0
    for x in ts:
        eq+=x["R"];pk=max(pk,eq);dd=min(dd,eq-pk)
        if x["R"]<=0:stk+=1;mstk=max(mstk,stk)
        else:stk=0
    span=(int(ts[-1]["t"])-int(ts[0]["t"]))/(7*86400) or 1
    print(f"  [{label:>16}] n={n} WR={100*w/n:.0f}% avgR={sm/n:+.2f} sumR={sm:+.1f} medR={st.median([x['R'] for x in sub]):+.2f} DD={dd:.1f}R streakL={mstk} freq={n/span:.2f}/sem")
print(f"NY 13-18 base ampla sweep n={len(ny)} (lead, Bonferroni-aware):")
full(ny,"NY total")
print("\n por ANO (R, não só WR):")
for yr in (2024,2025,2026): full([x for x in ny if x["yr"]==yr],f"NY {yr}")
print("\n por bloco (net+? mediana-por-bloco):")
import collections; byb=collections.defaultdict(list)
for x in ny: byb[x["block"][:16]].append(x)
blocksum=[]
for b in sorted(byb):
    s=byb[b]; sm=sum(x["R"] for x in s); blocksum.append(sm); w=sum(1 for x in s if x["w"])
    print(f"   {b}: n={len(s)} WR={100*w/len(s):.0f}% sumR={sm:+.1f}")
pos=sum(1 for x in blocksum if x>0)
print(f"  blocos net+ {pos}/{len(byb)} | MEDIANA-por-bloco sumR={st.median(blocksum):+.1f} (≈edge típico por bloco; sumR total infla por cauda)")
cap=lambda x:max(-1.0,min(15.0,x["R"])); drop=set(sorted(byb,key=lambda b:sum(cap(x) for x in byb[b]),reverse=True)[:2])
rem=[x for x in ny if x["block"][:16] not in drop]
print(f"  leave−top2bloc: sumR {sum(cap(x) for x in ny):+.0f} → {sum(cap(x) for x in rem):+.0f}(n{len(rem)},WR{100*sum(1 for x in rem if x['w'])/max(1,len(rem)):.0f}%)")
# quanto da soma vem dos top-5 trades (concentração)
allr=sorted([cap(x) for x in ny],reverse=True)
print(f"  top5 trades = {sum(allr[:5]):+.0f}R de {sum(allr):+.0f}R ({100*sum(allr[:5])/sum(allr):.0f}%) | top10={sum(allr[:10]):+.0f}R")
