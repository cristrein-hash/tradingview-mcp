#!/usr/bin/env python3
"""APROFUNDAMENTO 3 — testar o condicionamento de SESSÃO na base AMPLA (universo sweep n=728, grande). NY (13-18 UTC)
eleva WR robustamente à frequência? Por bloco + leave-one-out + NULL de hora embaralhada (o lift de NY sobrevive vs
hora aleatória?). Diagnóstico/produtivo, não-gate-final. Verified 2026-06-26."""
import csv, datetime as dt, random, statistics as st
from pathlib import Path
random.seed(7)
HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "candidates_sweep.csv")))
for r in rows: r["hr"] = dt.datetime.utcfromtimestamp(int(r["t"])).hour; r["R"] = float(r["R"]); r["w"] = r["win"] == "True"
span = (max(int(r["t"]) for r in rows) - min(int(r["t"]) for r in rows)) / (7*86400)
def agg(sub, label):
    if not sub: print(f"  [{label}] vazio"); return None
    n=len(sub); w=sum(1 for r in sub if r["w"]); sm=sum(r["R"] for r in sub)
    print(f"  [{label:>16}] n={n} WR={100*w/n:.0f}% avgR={sm/n:+.2f} sumR={sm:+.1f} freq={n/span:.2f}/sem")
    return 100*w/n
print(f"universo sweep n={len(rows)} (base AMPLA). Buckets de hora UTC:")
agg([r for r in rows if 0<=r["hr"]<7],"Asia 00-06"); agg([r for r in rows if 7<=r["hr"]<13],"Londres 07-12")
ny_wr=agg([r for r in rows if 13<=r["hr"]<19],"NY 13-18"); agg([r for r in rows if 19<=r["hr"]<24],"Tarde 19-23")
base_wr=agg(rows,"TODOS (base)")
ny=[r for r in rows if 13<=r["hr"]<19]
# por bloco
print("\n NY-only por bloco:")
import collections; byb=collections.defaultdict(list)
for r in ny: byb[r["block"][:16]].append(r)
pos=0
for b in sorted(byb):
    s=byb[b]; w=sum(1 for r in s if r["w"]); sm=sum(r["R"] for r in s)
    if sm>0: pos+=1
    print(f"   {b}: n={len(s)} WR={100*w/len(s):.0f}% sumR={sm:+.1f}")
print(f"  blocos NY net+ : {pos}/{len(byb)}")
# leave-one-out no NY
cap=lambda r: max(-1.0,min(15.0,r["R"]))
drop=set(sorted(byb,key=lambda b:sum(cap(r) for r in byb[b]),reverse=True)[:2])
rem=[r for r in ny if r["block"][:16] not in drop]
print(f"  NY leave−top2bloc: sumR {sum(cap(r) for r in ny):+.0f} → {sum(cap(r) for r in rem):+.0f} (n{len(rem)}, WR {100*sum(1 for r in rem if r['w'])/max(1,len(rem)):.0f}%)")
# NULL: WR de uma janela de 6h ALEATÓRIA vs NY (lift real ou qualquer janela serve?)
hrs=[r["hr"] for r in rows]; wins=[r["w"] for r in rows]
nulls=[]
for _ in range(2000):
    start=random.randint(0,18); sub=[wins[i] for i in range(len(hrs)) if start<=hrs[i]<start+6]
    if sub: nulls.append(100*sum(sub)/len(sub))
ge=sum(1 for x in nulls if x>=ny_wr)/len(nulls)
print(f"\n NULL (janela 6h aleatória, 2000x): WR médio={st.mean(nulls):.0f}% max={max(nulls):.0f}% | P(janela aleatória WR≥NY {ny_wr:.0f}%)={ge:.3f}")
print(" → se P baixo, NY é janela REALMENTE melhor; se alto, qualquer janela de 6h dá WR parecido (efeito nulo).")
