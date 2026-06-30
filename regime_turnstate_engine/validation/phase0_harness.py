#!/usr/bin/env python3
"""RTSE FASE 0 — HARNESS (determinístico, SEM agentes, SEM detector novo, SEM re-cabear estratégia).
Mede o que JÁ EXISTE (baselines triviais) contra as 2 RÉGUAS:
  (A) M8 true_reversals (15M, 2024+) — sanity de contagem (414/205/209)
  (B) bordas de REGIME do Cris (4H, 2020-2026) — a régua-alvo do RTSE
Produz a 1ª curva latência×FP, compara cada baseline com NULL, e roda red-team anti-look-ahead.
GATE Fase 0: harness reproduz M8; produz frontier; red-team passa; algum baseline regime-aware bate o MA-cross/null.
⚠️ Réguas = hindsight, NUNCA feature. n de bordas é pequeno (~19) — honestidade sobre n. Determinístico, py3.9."""
import json,csv,statistics as st,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
GT=ROOT/"regime_turnstate_engine/ground_truth"
def D(ts): return dt.datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d")

# ---------- RÉGUA A: M8 (sanity) ----------
m8=[]
with open(ROOT/"research/xau_15m_bb_nas_leonardo/true_reversals_M8.csv") as fh:
    for d in csv.DictReader(fh): m8.append((int(d["t"]),d["kind"]))
nbot=sum(1 for _,k in m8 if k=="BOT"); ntop=sum(1 for _,k in m8 if k=="TOP")
print("=== RÉGUA A — M8 sanity ===")
print(f"  total={len(m8)} BOT={nbot} TOP={ntop}  (esperado 414/205/209) -> {'OK' if (len(m8),nbot,ntop)==(414,205,209) else 'DIVERGE'}")

# ---------- RÉGUA B: bordas de regime do Cris (4H) ----------
macro=[]
with open(GT/"cris_regime_boxes.csv") as fh:
    for d in csv.DictReader(fh):
        if d["role"]=="MACRO": macro.append((int(d["start"]),d["family"]))
macro.sort()
DIRMAP={"BULL":"UP","BEAR":"DOWN"}
edges=[(ts,DIRMAP[f]) for ts,f in macro if f in DIRMAP]   # bordas UP/DOWN (RANGE fora p/ detectores de tendência)
print(f"\n=== RÉGUA B — bordas regime Cris: {len(macro)} macro -> {len(edges)} UP/DOWN edges (RANGE excluído dos baselines de tendência) ===")

# ---------- bars 4H ----------
raw=[json.loads(l) for l in (ROOT/"my-strategy/research/revalidation/raw_4h_ohlc.jsonl").read_text().splitlines()]
raw.sort(key=lambda b:b["t"])
T=[b["t"] for b in raw]; C=[b["c"] for b in raw]; Hh=[b["h"] for b in raw]; Ll=[b["l"] for b in raw]
N=len(raw)
def ema(series,length):
    a=2/(length+1); out=[series[0]]
    for x in series[1:]: out.append(a*x+(1-a)*out[-1])
    return out
def fires_from_state(state):
    """state: lista UP/DOWN por barra -> eventos (ts,dir) na MUDANÇA (causal)."""
    ev=[]
    for i in range(1,N):
        if state[i]!=state[i-1] and state[i] in ("UP","DOWN"):
            ev.append((T[i],state[i]))
    return ev
# ---- detectores causais (close-only) ----
def det_ma_cross(slow,fast=20):
    ef=ema(C,fast); es=ema(C,slow)
    return fires_from_state(["UP" if ef[i]>es[i] else "DOWN" for i in range(N)])
def det_ema_slope(length,k=6):
    e=ema(C,length); s=["UP"]*N
    for i in range(N): s[i]="UP" if (i>=k and e[i]>e[i-k]) else ("DOWN" if i>=k else "UP")
    return fires_from_state(s)
def det_swing_break(Nb):
    s=["UP"]*N; cur="UP"
    for i in range(N):
        if i>=Nb:
            hi=max(Hh[i-Nb:i]); lo=min(Ll[i-Nb:i])
            if C[i]>hi: cur="UP"
            elif C[i]<lo: cur="DOWN"
        s[i]=cur
    return fires_from_state(s)
def det_null(count,seed):
    # fires aleatórios casados por contagem/direção (determinístico via seed-LCG, sem Math.random)
    out=[]; x=seed
    for _ in range(count):
        x=(1103515245*x+12345)%(2**31); idx=x%N
        x=(1103515245*x+12345)%(2**31); dr="UP" if x%2 else "DOWN"
        out.append((T[idx],dr))
    return sorted(out)
# ---- métrica latência×FP vs régua B ----
def score(fires,edges,W_days=45):
    W=W_days*86400
    up_e=[t for t,d in edges if d=="UP"]; dn_e=[t for t,d in edges if d=="DOWN"]
    byd={"UP":sorted(up_e),"DOWN":sorted(dn_e)}
    # recall + latência: p/ cada edge, 1º fire mesma dir em [edge, edge+W]
    lat=[]; matched_edges=0
    for et,ed in edges:
        cand=[ft for ft,fd in fires if fd==ed and et<=ft<=et+W]
        if cand: matched_edges+=1; lat.append((min(cand)-et)/86400)
    recall=matched_edges/len(edges) if edges else 0
    # precisão: fire é TP se existe edge mesma dir em [fire-W, fire]
    tp=0
    for ft,fd in fires:
        if any(ft-W<=et<=ft for et in byd[fd]): tp+=1
    prec=tp/len(fires) if fires else 0
    fp=len(fires)-tp
    return prec,recall,(st.median(lat) if lat else None),len(fires),matched_edges,fp
# ---- rodar baselines ----
print("\n=== FRONTIER (régua B, W=45d) — baseline | param | prec | recall | lat_med(d) | nfires ===")
results={}
configs=[("ma_cross",det_ma_cross,[50,100,150,200]),
         ("ema_slope",det_ema_slope,[50,100,150]),
         ("swing_break",det_swing_break,[10,20,40])]
for name,fn,params in configs:
    for p in params:
        fr=fn(p); pr,rc,lm,nf,me,fp=score(fr,edges)
        fpy=fp/((T[-1]-T[0])/(365.25*86400))
        results[f"{name}({p})"]=(pr,rc,lm,nf,fpy)
        print(f"  {name:12} {p:>4} | prec {pr:.2f} | recall {rc:.2f} | lat {('%.0f'%lm) if lm else '—':>4} | nf {nf} | FP/ano {fpy:.0f}")
# null casado (média de K)
K=15; nf_ref=int(st.mean([v[3] for v in results.values()]))
nps=[];nrs=[]
for s in range(1,K+1):
    pr,rc,lm,nf,me,fp=score(det_null(nf_ref,s*7919),edges)
    nps.append(pr); nrs.append(rc)
print(f"  {'NULL':12} {'~'+str(nf_ref):>4} | prec {st.mean(nps):.2f} | recall {st.mean(nrs):.2f} | (média de {K} seeds)")
# ---- red-team anti-look-ahead ----
print("\n=== RED-TEAM anti-look-ahead (ema_slope) ===")
full=det_ema_slope(100)
# recomputa só com barras <= índice M, injetando barra futura sintética -> estados passados devem bater
M=N-50
Cm=C[:M]+[C[M-1]*1.5]  # barra futura absurda
def ema_sub(series,length):
    a=2/(length+1); out=[series[0]]
    for x in series[1:]: out.append(a*x+(1-a)*out[-1])
    return out
e_full=ema(C,100); e_sub=ema_sub(Cm,100)
identical=all(abs(e_full[i]-e_sub[i])<1e-9 for i in range(M))
print(f"  EMA passada idêntica com barra futura injetada (até M={M}): {'PASS (causal)' if identical else 'FAIL (vaza futuro)'}")
# ---- veredito ----
# 'bom' = alto recall com baixo FP/ano (lat ok)
best=min([(k,v) for k,v in results.items() if v[1]>=0.85],key=lambda kv:kv[1][4]) if any(v[1]>=0.85 for v in results.values()) else max(results.items(),key=lambda kv:kv[1][1])
print("\n=== VEREDITO FASE 0 ===")
print(f"  M8 sanity: {'OK' if (len(m8),nbot,ntop)==(414,205,209) else 'DIVERGE'}")
print(f"  frontier produzida: SIM ({len(results)} configs) | melhor recall>=0.85 c/ menor FP/ano: {best[0]} recall {best[1][1]:.2f}/FP-ano {best[1][4]:.0f}/lat {best[1][2]:.0f}d")
print(f"  bate NULL? recall {best[1][1]:.2f} vs null {st.mean(nrs):.2f} | prec {best[1][0]:.2f} vs null {st.mean(nps):.2f}")
print(f"  red-team: {'PASS' if identical else 'FAIL'}")
print(f"  ⚠️ n bordas={len(edges)} (pequeno; honestidade) — Fase 1+ adiciona v5 portado + M8 fine-grained + multi-M")
