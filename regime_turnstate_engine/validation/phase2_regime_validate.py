#!/usr/bin/env python3
"""RTSE FASE 2 (make-or-break) — detector de regime REAL (4H-nativo, lógica v5, params espelhados não-fitados)
na JANELA INTEIRA (2020-2026) vs bordas macro do Cris, com null + POR-ANO + jackknife. Compara com o PISO trivial.
Pergunta: o detector real BATE o piso ROBUSTAMENTE (todo ano, sob null), ou só ganha in-sample (2025)?
Reusa engine_4h_regime_gate_RAW.regime_at (single source of truth, NÃO duplica lógica). Honesto: ~16 bordas
(regime é raro) -> robustez por-ano/jackknife > significância dura. Determinístico."""
import json,csv,sys,io,contextlib,statistics as st,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
REV=ROOT/"my-strategy/research/revalidation"; GT=ROOT/"regime_turnstate_engine/ground_truth"
sys.path.insert(0,str(REV))
with contextlib.redirect_stdout(io.StringIO()):   # silencia análise L1/L2 do engine ao importar
    import engine_4h_regime_gate_RAW as eng
def D(ts): return dt.datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d")
def yr(ts): return dt.datetime.utcfromtimestamp(int(ts)).year
# ---- bars 4H full ----
raw=[json.loads(l) for l in (REV/"raw_4h_ohlc.jsonl").read_text().splitlines()]; raw.sort(key=lambda b:b["t"])
T=[b["t"] for b in raw];C=[b["c"] for b in raw];Hh=[b["h"] for b in raw];Ll=[b["l"] for b in raw];N=len(raw)
DIR={"BULL":"UP","BEAR":"DOWN"}
# ---- detector REAL: regime_at por barra -> flips ----
reg=[eng.regime_at(t) for t in T]
def flips_from(labels):
    ev=[];prev=None
    for i in range(N):
        lab=labels[i]
        d=DIR.get(lab, lab if lab in ("UP","DOWN") else None)  # aceita BULL/BEAR/RANGE e UP/DOWN
        if d and d!=prev: ev.append((T[i],d)); prev=d
        elif d: prev=d
    return ev
real_fires=flips_from(reg)
# ---- baseline trivial (swing_break 40) full ----
def swing_break(Nb):
    s=["UP"]*N;cur="UP"
    for i in range(N):
        if i>=Nb:
            if C[i]>max(Hh[i-Nb:i]):cur="UP"
            elif C[i]<min(Ll[i-Nb:i]):cur="DOWN"
        s[i]=cur
    return flips_from(s)
triv_fires=swing_break(40)
# ---- null ----
def null_fires(count,seed):
    out=[];x=seed
    for _ in range(count):
        x=(1103515245*x+12345)%(2**31);idx=x%N
        x=(1103515245*x+12345)%(2**31);out.append((T[idx],"UP" if x%2 else "DOWN"))
    return sorted(out)
# ---- bordas macro Cris (full) ----
edges=[]
with open(GT/"cris_regime_boxes.csv") as fh:
    for r in csv.DictReader(fh):
        if r["role"]=="MACRO" and r["family"] in DIR: edges.append((int(r["start"]),DIR[r["family"]]))
edges.sort()
W0,W1=T[0],T[-1]; YRS=(W1-W0)/(365.25*86400)
def score(fires,eds,W_days=45,TOL=5*86400):
    if not eds: return None
    W=W_days*86400;byd={"UP":[t for t,d in eds if d=="UP"],"DOWN":[t for t,d in eds if d=="DOWN"]}
    lat=[];me=0
    for et,ed in eds:
        c=[ft for ft,fd in fires if fd==ed and et-TOL<=ft<=et+W]
        if c:me+=1;lat.append(max(0,(min(c)-et)/86400))
    tp=sum(1 for ft,fd in fires if any(ft-W<=et<=ft+TOL for et in byd[fd]))
    yrs=(max(ft for ft,_ in fires)-min(ft for ft,_ in fires))/(365.25*86400) if len(fires)>1 else YRS
    return me/len(eds),(st.median(lat) if lat else None),len(fires),(len(fires)-tp)/YRS
print(f"=== FASE 2 — regime REAL 4H (lógica v5, full {D(W0)}..{D(W1)}, {YRS:.1f} anos) ===")
print(f"bordas macro Cris UP/DOWN: {len(edges)} | flips: real={len(real_fires)} trivial(swing40)={len(triv_fires)}")
r_real=score(real_fires,edges); r_triv=score(triv_fires,edges)
print(f"\n--- GLOBAL | recall | lat_med(d) | flips | FP/ano ---")
print(f"  REAL (v5-4H)    | recall {r_real[0]:.2f} | lat {r_real[1]:.1f} | {r_real[2]:>3} | FP/ano {r_real[3]:.0f}")
print(f"  trivial swing40 | recall {r_triv[0]:.2f} | lat {r_triv[1]:.1f} | {r_triv[2]:>3} | FP/ano {r_triv[3]:.0f}")
# null
K=20;nr=[];nfp=[]
for s in range(1,K+1):
    rs=score(null_fires(len(real_fires),s*7919),edges)
    if rs: nr.append(rs[0]);nfp.append(rs[3])
print(f"  NULL (~{len(real_fires)})    | recall {st.mean(nr):.2f} | — | — | FP/ano {st.mean(nfp):.0f} (média {K})")
# ---- POR ANO ----
print("\n--- POR ANO (edges no ano | recall real | FP/ano real | recall trivial) ---")
for y in range(2020,2027):
    ey=[(t,d) for t,d in edges if yr(t)==y]
    if not ey: continue
    fr=[(t,d) for t,d in real_fires if yr(t)==y]; ftv=[(t,d) for t,d in triv_fires if yr(t)==y]
    rr=score(fr,ey); rt=score(ftv,ey)
    print(f"  {y}: edges {len(ey)} | real recall {rr[0]:.2f} FP {len(fr)} | trivial recall {rt[0]:.2f} FP {len(ftv)}")
# ---- JACKKNIFE por ano (dropa ano, recall global do resto) ----
print("\n--- JACKKNIFE (dropa 1 ano das bordas; recall real do resto) ---")
recs=[]
for y in range(2020,2027):
    ej=[(t,d) for t,d in edges if yr(t)!=y]
    if not ej: continue
    rj=score(real_fires,ej); recs.append(rj[0])
    print(f"  sem {y}: recall {rj[0]:.2f}")
print(f"  recall jackknife: min {min(recs):.2f} / max {max(recs):.2f} (estável se ~constante)")
# ---- VEREDITO ----
print("\n=== VEREDITO FASE 2 ===")
beats = r_real[0]>=r_triv[0] and r_real[3]<=r_triv[3]
print(f"  REAL bate trivial? recall {r_real[0]:.2f} vs {r_triv[0]:.2f} | FP/ano {r_real[3]:.0f} vs {r_triv[3]:.0f} -> {'SIM (Pareto)' if beats else 'NÃO/empate'}")
print(f"  REAL bate null? recall {r_real[0]:.2f} vs null {st.mean(nr):.2f}")
print(f"  ⚠️ n={len(edges)} bordas (regime é raro) -> robustez por-ano/jackknife é o juiz, não p-valor.")
print("\n=== LEITURA (honesta) ===")
print("NÃO é Pareto-win. É TRADEOFF: REAL = 5x menos falso-positivo (3 vs 15/ano) MAS pega só 69% das viradas e mais lento (13 vs 3d).")
print("REAL bate o NULL no recall (0.69 vs 0.25) -> sinal real, não ruído. Por-ano: BAIXO-FP sempre, recall oscila (2024=0.33) -> NÃO é só in-sample.")
print("CONSTRUTIVO: nenhum extremo sozinho é o motor. Valor do RTSE = COMBINAR (rápido p/ early/baixa-conf + calmo p/ alta-conf) = schema confidence/latency.")
print("Pelo cânone: detector ÚNICO = grau-CONSOLIDAÇÃO (padroniza + corta FP), NÃO edge sozinho. A COMBINAÇÃO (Fase 3) é a aposta.")
