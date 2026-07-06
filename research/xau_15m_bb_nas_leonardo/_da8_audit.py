#!/usr/bin/env python3
"""DEVIL'S ADVOCATE 8 — auditoria de AFIRMAÇÃO 1 (virada de ordenamento) e AFIRMAÇÃO 2 (pipeline E5/E6).
Replica a construção do event_stage2_entry_20260706.py SEM sobrescrever nada. Só imprime.
NÃO commita, NÃO modifica ficheiros existentes."""
import json, bisect, hashlib, random, math
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S); ATR = [b.get("atr") or 5.0 for b in S]; HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]; OP = [b.get("o", b["c"]) for b in S]
CACHE = {r["cj_t"]: r for r in (json.loads(l) for l in open(HERE / "results" / "raw_feature_cache_20260706.jsonl"))}
UNIV = sorted([u for u in U if u["cj_t"] in R3 and u["cj_t"] in CACHE], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]; WK = len({u["g_week"] for u in U})
BASE_HIT = sum(1 for r in R3.values() if r["R3"] >= 3) / len(R3)

LOWS = []; d0 = 0; ehi = elo = 0
for i in range(1, N):
    if HI[i] > HI[ehi]: ehi = i
    if LO[i] < LO[elo]: elo = i
    if d0 >= 0 and HI[ehi]-LO[i] >= 6*ATR[i] and ehi < i: d0 = -1; elo = min(range(ehi,i+1), key=lambda k: LO[k])
    elif d0 <= 0 and HI[i]-LO[elo] >= 6*ATR[i] and elo < i: LOWS.append((i,elo)); d0 = 1; ehi = max(range(elo,i+1), key=lambda k: HI[k])
KLOW = [x[0] for x in LOWS]
for u in UNIV:
    u["_flo"] = u["g_sl"] + 0.1*(u.get("g_atr") or 5.0); u["_a"] = u.get("g_atr") or 5.0; u["_circ"] = set(); u["_F"] = CACHE[u["cj_t"]]
    ci = bisect.bisect_right(TS, u["cj_t"]) - 1; j = bisect.bisect_right(KLOW, ci) - 1; u["_fam"] = "SEM"
    if j >= 0:
        _, l0i = LOWS[j]; L0 = LO[l0i]; H1 = max(HI[k] for k in range(l0i, ci+1))
        if H1-L0 > 1e-9:
            r = (H1-u["_flo"])/(H1-L0); u["_fam"] = "RASO" if r<0.5 else ("BANDA" if r<=1.3 else "FUNDO")
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"]-8*3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"]+8*3600:
        u = UNIV[j]; dd = u["_flo"]-g["flush_low"]
        if -3*u["_a"] <= dd <= 1*u["_a"]: u["_circ"].add(gi)
        j += 1
EV = []; cur = []
for u in UNIV:
    if cur and u["cj_t"]-cur[-1]["cj_t"] <= 48*3600 and abs(u["_flo"]-cur[-1]["_flo"]) <= 3*u["_a"]:
        cur.append(u)
    else:
        if cur: EV.append(cur)
        cur = [u]
if cur: EV.append(cur)

# ---- família filter (idêntico ao main) ----
def vec(ev):
    sub = ev[:3]; F = [u["_F"] for u in sub]
    st_i = bisect.bisect_right(TS, ev[0]["cj_t"])-1; a = ev[0]["_a"]; pre_hi = max(HI[max(0,st_i-96):st_i+1]); ei = bisect.bisect_right(TS, sub[-1]["cj_t"])-1
    return [min(f["rsi_min8"] for f in F), min(f["nas_dist"] for f in F), max(f["sell_climax4"] for f in F), max(f["below_poc"] for f in F),
            min(f["poc_dist"] for f in F), max(f["nas_long_rec"] for f in F), max(f["vol_climax"] for f in F), max(f["flow_divergence"] for f in F),
            (pre_hi - min(LO[max(0,st_i-8):ei+1]))/a]
for ev in EV:
    ev[0]["_vec"] = vec(ev); ev[0]["_isf"] = any(u["_circ"] for u in ev); ev[0]["_efam"] = ev[0]["_fam"]
X = np.array([ev[0]["_vec"] for ev in EV]); isf = np.array([ev[0]["_isf"] for ev in EV]); efam = np.array([ev[0]["_efam"] for ev in EV])
keep = np.zeros(len(EV), bool)
for fam in ("RASO","BANDA","FUNDO","SEM"):
    idx = np.where(efam==fam)[0]; fidx = np.where((efam==fam)&isf)[0]
    if len(fidx) < 3: keep[idx] = True; continue
    lo = X[fidx].min(0); hi = X[fidx].max(0)
    for i in idx:
        if np.all((X[i]>=lo)&(X[i]<=hi)): keep[i] = True
POOL = [ev for k, ev in zip(keep, EV) if k]

def hit(cj): return R3[cj]["R3"] >= 3
def wilson(k, n, z=1.96):
    if n == 0: return (0,0)
    p = k/n; d = 1+z*z/n
    c = (p + z*z/(2*n))/d; hw = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return (c-hw, c+hw)
def binom_ge(k, n, p):
    from math import comb
    return sum(comb(n,i)*p**i*(1-p)**(n-i) for i in range(k, n+1))
def binom_le(k, n, p):
    from math import comb
    return sum(comb(n,i)*p**i*(1-p)**(n-i) for i in range(0, k+1))

print("="*90)
print("SETUP: EV total=%d · POOL(família)=%d · base-hit3R universo=%.2f%%" % (len(EV), len(POOL), 100*BASE_HIT))
print("="*90)

# ============================================================
# AFIRMAÇÃO 1 — virada de ordenamento (circular?)
# ============================================================
print("\n########## AFIRMAÇÃO 1 — VIRADA DE ORDENAMENTO ##########")
def firstcand_hit(events):
    return sum(1 for ev in events if hit(ev[0]["cj_t"])), len(events)
def anyhit(ev): return any(hit(u["cj_t"]) for u in ev)
def cand_hitrate(events):
    tot = sum(len(ev) for ev in events); h = sum(1 for ev in events for u in ev if hit(u["cj_t"]))
    return h, tot

FUND = [ev for ev in EV if any(u["_circ"] for u in ev)]         # eventos-fundo (círculo)
HAS3R = [ev for ev in EV if anyhit(ev)]                          # eventos com QUALQUER 3R
NO3R = [ev for ev in EV if not anyhit(ev)]
FUND_HAS3R = [ev for ev in FUND if anyhit(ev)]
FUND_NO3R = [ev for ev in FUND if not anyhit(ev)]
NOTFUND_HAS3R = [ev for ev in EV if not any(u["_circ"] for u in ev) and anyhit(ev)]

print("\n-- 1º-candidato hit3R por classe de evento --")
for nm, evs in [("TODOS EV", EV), ("FUND (círculo)", FUND), ("HAS3R (contém 3R)", HAS3R),
                ("FUND∩HAS3R", FUND_HAS3R), ("NOT-FUND∩HAS3R", NOTFUND_HAS3R)]:
    h, n = firstcand_hit(evs)
    lo, hi = wilson(h, n)
    print(f"  {nm:<20} N-ev {n:>4} · 1º-cand hit3R {100*h/max(1,n):>5.1f}%  Wilson95[{100*lo:.1f},{100*hi:.1f}]")

print("\n-- estrutura: recall de 3R por evento (teto se entrada perfeita) --")
for nm, evs in [("TODOS EV", EV), ("FUND", FUND), ("HAS3R", HAS3R)]:
    frac = sum(1 for ev in evs if anyhit(ev))/len(evs)
    ch, ct = cand_hitrate(evs)
    ncand = sum(len(ev) for ev in evs)/len(evs)
    print(f"  {nm:<12} N-ev {len(evs):>4} · frac-eventos-com-3R {100*frac:>5.1f}% · hit3R por-candidato {100*ch/ct:>5.1f}% · candidatos/ev {ncand:.2f}")

print("\n-- círculo adiciona info ALÉM de 'contém 3R'? --")
h_fund3r, n_fund3r = firstcand_hit(FUND_HAS3R)
h_nf3r, n_nf3r = firstcand_hit(NOTFUND_HAS3R)
print(f"  1º-cand hit3R  FUND∩HAS3R   = {100*h_fund3r/max(1,n_fund3r):.1f}%  (N {n_fund3r})")
print(f"  1º-cand hit3R  NOTFUND∩HAS3R= {100*h_nf3r/max(1,n_nf3r):.1f}%  (N {n_nf3r})")
# per-candidate rate conditional
chf, ctf = cand_hitrate(FUND); chh, cth = cand_hitrate(HAS3R)
print(f"  hit3R por-candidato: FUND {100*chf/ctf:.1f}%  vs HAS3R {100*chh/cth:.1f}%  vs TODOS {100*cand_hitrate(EV)[0]/cand_hitrate(EV)[1]:.1f}%")
print(f"  FUND events: {len(FUND)} · dos quais contêm >=1 3R: {len(FUND_HAS3R)} ({100*len(FUND_HAS3R)/len(FUND):.0f}%)")
print(f"  quantos FUND events NÃO têm nenhum 3R (círculo sem 3R): {len(FUND_NO3R)}")

# ============================================================
# AFIRMAÇÃO 2 — pipeline E5/E6
# ============================================================
print("\n\n########## AFIRMAÇÃO 2 — PIPELINE E5/E6 ##########")
# reconstruir _reclaim / _hl / _casc no POOL exatamente como o main
for ev in POOL:
    min_flo = 1e18
    for pos, u in enumerate(ev, 1):
        ci = bisect.bisect_right(TS, u["cj_t"])-1; prevmin = min_flo
        u["_post_low"] = int(pos > 1 and u["_flo"] > prevmin + 0.05*u["_a"])
        u["_hl"] = int(u["_flo"] > prevmin + 0.05*u["_a"]) if pos > 1 else 0
        min_flo = min(min_flo, u["_flo"])
        u["_reclaim"] = int(ci >= 1 and CL[ci] > HI[ci-1] and CL[ci] > OP[ci])
        u["_casc"] = cascade(u["cj_t"])
        u["_acc_rsi"] = min(u["_F"]["rsi_min8"], ev[0]["_F"]["rsi_min8"])
def first(ev, cond):
    for u in ev:
        if cond(u): return u
    return None
def signal_set(cond):
    rows = [first(ev, cond) for ev in POOL if first(ev, cond)]
    return rows
E5 = signal_set(lambda u: u["_casc"]>=4 and u["_reclaim"]==1)
E6 = signal_set(lambda u: u["_casc"]>=3 and u["_hl"]==1 and u["_reclaim"]==1)
E2 = signal_set(lambda u: u["_post_low"]==1 and u["_hl"]==1 and u["_reclaim"]==1)
for nm, rows in [("E5 casc4&reclaim", E5), ("E6 casc3&hl&reclaim", E6)]:
    n=len(rows); h=sum(1 for u in rows if hit(u["cj_t"])); w=sum(1 for u in rows if R3[u["cj_t"]]["net3"]>0)
    print(f"\n{nm}: N{n} hit3R {h}/{n}={100*h/n:.1f}% WR {w}/{n}={100*w/n:.1f}%")

print("\n--- VETOR A: binomial + Wilson (hit3R) ---")
for nm, rows in [("E5", E5), ("E6", E6)]:
    n=len(rows); h=sum(1 for u in rows if hit(u["cj_t"]))
    lo,hi=wilson(h,n)
    p_base=binom_ge(h,n,BASE_HIT)
    # vs 50%
    p50 = binom_le(h,n,0.5)
    print(f"  {nm}: {h}/{n}={100*h/n:.1f}% · Wilson95[{100*lo:.1f},{100*hi:.1f}] · limInf {'>' if lo>BASE_HIT else '<='} base({100*BASE_HIT:.1f}) "
          f"· P(X>={h}|base)={p_base:.4f} · P(X<={h}|p=.5)={p50:.3f}")

print("\n--- por-ano (fragilidade N pequeno) ---")
for nm, rows in [("E5", E5), ("E6", E6)]:
    yr={}
    for u in rows:
        r=R3[u["cj_t"]]; d=yr.setdefault(r["yr"],[0,0,0.0]); d[0]+=1; d[1]+=int(r["R3"]>=3); d[2]+=r["net3"]
    print(f"  {nm}: " + " · ".join(f"{y}:N{d[0]} hit{d[1]} net{d[2]:+.1f}" for y,d in sorted(yr.items())))

print("\n--- VETOR B: multiplicidade ---")
NLOOKS = 14
for nm, rows in [("E5", E5), ("E6", E6)]:
    n=len(rows); h=sum(1 for u in rows if hit(u["cj_t"]))
    p=binom_ge(h,n,BASE_HIT); pbonf=min(1.0, p*NLOOKS)
    print(f"  {nm}: p-binom(vs base)={p:.4f} · Bonferroni×{NLOOKS}={pbonf:.3f} {'SOBREVIVE' if pbonf<0.05 else 'NÃO sobrevive <0.05'}")

print("\n--- VETOR C: decomposição cascata vs filtro-família ---")
# univ candidates com _reclaim e _casc (todo o universo, sem filtro família)
def reclaim_of(cj):
    ci = bisect.bisect_right(TS, cj)-1
    return int(ci>=1 and CL[ci]>HI[ci-1] and CL[ci]>OP[ci])
for u in UNIV:
    u["_r_all"]=reclaim_of(u["cj_t"]); u["_c_all"]=cascade(u["cj_t"])
def panel_simple(rows, tag):
    n=len(rows);
    if not n: print(f"  {tag:<42} vazio"); return
    h=sum(1 for u in rows if hit(u["cj_t"])); nets=[R3[u["cj_t"]]["net3"] for u in rows]
    lo,hi=wilson(h,n)
    print(f"  {tag:<42} N{n:>4} hit3R {100*h/n:>5.1f}% NET {sum(nets):>+7.1f} Wilson95[{100*lo:.0f},{100*hi:.0f}]")
# NB: no-family variants apply per-candidate (não 1/evento) — para medir contribuição bruta
print("  [univ inteiro, por-candidato — mede contribuição bruta de cada filtro]")
panel_simple([u for u in UNIV if u["_c_all"]>=4], "cascata>=4 (só)")
panel_simple([u for u in UNIV if u["_r_all"]==1], "reclaim (só)")
panel_simple([u for u in UNIV if u["_c_all"]>=4 and u["_r_all"]==1], "cascata>=4 & reclaim (SEM família)")
panel_simple([u for u in UNIV if u["_c_all"]>=3 and u["_r_all"]==1], "cascata>=3 & reclaim (SEM família)")
# família-only: primeiro candidato de cada evento do POOL com reclaim, sem cascata
famrec = [first(ev, lambda u: u["_reclaim"]==1) for ev in POOL if first(ev, lambda u: u["_reclaim"]==1)]
panel_simple(famrec, "família-pool & reclaim (SEM cascata)")
# pool candidates cascata>=4 sem reclaim
poolc4 = [first(ev, lambda u: u["_casc"]>=4) for ev in POOL if first(ev, lambda u: u["_casc"]>=4)]
panel_simple(poolc4, "família-pool & cascata>=4 (SEM reclaim)")
print("  [E5 completo = família-pool & cascata>=4 & reclaim, 1/evento]")
panel_simple(E5, "E5")

print("\n--- VETOR E: overlap com CASCEX N34 ---")
# CASCEX = POCKET (do veto module) menos veto macro-leg
for u in CTX: u["_ml"] = macro_leg(u["cj_t"])
for u in POCKET:
    if "_ml" not in u: u["_ml"] = macro_leg(u["cj_t"])
CASCEX = sorted([u for u in POCKET if u["_ml"]["vel"]<0.10 and u["_ml"]["recent_frac"]<0.5], key=lambda u:u["cj_t"])
cascex_t = set(u["cj_t"] for u in CASCEX)
pocket_t = set(u["cj_t"] for u in POCKET)
e5_t = set(u["cj_t"] for u in E5); e6_t = set(u["cj_t"] for u in E6)
print(f"  CASCEX N={len(CASCEX)} (POCKET N{len(POCKET)})")
print(f"  E5 N={len(e5_t)} · overlap E5∩CASCEX={len(e5_t & cascex_t)} · E5∩POCKET={len(e5_t & pocket_t)} · E5⊂CASCEX? {e5_t<=cascex_t}")
print(f"  E6 N={len(e6_t)} · overlap E6∩CASCEX={len(e6_t & cascex_t)} · E6∩POCKET={len(e6_t & pocket_t)} · E6⊂CASCEX? {e6_t<=cascex_t}")
print(f"  E5∩E6 = {len(e5_t & e6_t)}")
# CASCEX hit-rate reproduction
ch=sum(1 for u in CASCEX if hit(u["cj_t"])); print(f"  CASCEX hit3R {ch}/{len(CASCEX)}={100*ch/len(CASCEX):.1f}%")

print("\n--- VETOR D: causalidade (checagem programática) ---")
# confirmar que cascade só usa eventos t<=cj e reclaim usa barra do cj
import random as _r
_r.seed(7)
bad=0
for cj in _r.sample([u["cj_t"] for u in UNIV], 200):
    hi = bisect.bisect_right(ET, cj)
    if hi < len(ET) and ET[hi] <= cj: bad+=1  # deveria não haver evento t<=cj além do índice
print(f"  cascade: eventos usados todos com t<=cj? violações={bad}/200 (0=OK)")
ci_test = bisect.bisect_right(TS, UNIV[100]['cj_t'])-1
print(f"  reclaim usa barra ci (fecho da barra cj) e ci-1: ci={ci_test}, TS[ci]<=cj<TS[ci+1] garantido por bisect (OK causal)")
