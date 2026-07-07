#!/usr/bin/env python3
"""DEVIL'S ADVOCATE — ataques 3/4/5 ao FaseD∩FSM4 (XAU 15M LONG 3R)."""
import sys, itertools, random, datetime as dt, statistics as st
HERE="/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo"
sys.path.insert(0, HERE)
from agent_ctx_kit import ENTRIES, score

FaseD = {2,3,4,5,7,8,9,10,11,12,13,14,15,16,17,20,21,22,23,25,27,28,29,30,31,34,35,36,37,38,39,40,41,42,43,44,45,46,48,51,52,53,54,55,57,58,59,60,61,62,63,64,67,69,71,72,73,74,75,76,77,78,82,83,84,87,88,90,91,92,93,94,96}
CHoCH = {1,6,10,11,12,15,17,20,22,28,30,32,33,34,35,38,42,43,46,47,54,59,60,61,62,63,64,66,70,73,74,75,76,77,78,79,81,82,83,84,88,90,91,94,95}
FSM4  = {1,2,3,4,6,7,8,9,10,12,13,14,15,16,18,20,23,26,27,30,33,35,36,37,39,40,44,45,46,48,50,51,52,53,55,61,62,64,68,71,74,75,76,77,78,80,82,84,87,88,89,90,93,95}
FINAL = FaseD & FSM4
LOSER_TARGETS = {21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94}
WINNER_KEYS   = {1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96}
E = {e["n"]:e for e in ENTRIES}
def _yr(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y")

print("FINAL == FaseD∩FSM4 ?", sorted(FINAL)== [2,3,4,7,8,9,10,12,13,14,15,16,20,23,27,30,35,36,37,39,40,44,45,46,48,51,52,53,55,61,62,64,71,74,75,76,77,78,82,84,87,88,90,93])
print("score(FINAL):", score(FINAL))
print("="*80)

# ---------- ATAQUE 3: perfil dos winners genuinos CORTADOS vs losers cortados vs winners mantidos ----------
cut = set(E) - FINAL
win_cut = sorted(n for n in cut if E[n]["out"]==1)
los_cut = sorted(n for n in cut if E[n]["out"]==0)
win_kept= sorted(n for n in FINAL if E[n]["out"]==1)
def prof(ns):
    rl=[E[n]["reclaim_lag"] for n in ns]
    depth=[(E[n]["leg_top"]-E[n]["demand_low"])/5.0 for n in ns]  # proxy leg size
    return dict(n=len(ns), rl_med=round(st.median(rl),2), rl_mean=round(st.mean(rl),2),
                rl_dist=dict(sorted(__import__("collections").Counter(rl).items())))
print("ATAQUE 3 — reclaim_lag (o proxy mecanico central dos classificadores):")
print("  winners CORTADOS :", prof(win_cut), win_cut)
print("  losers  CORTADOS :", prof(los_cut))
print("  winners MANTIDOS :", prof(win_kept))
# foco nos genuinos citados
for n in (1,29,95,96):
    e=E.get(n)
    if e: print(f"  #{n:>2} out={e['out']} reclaim_lag={e['reclaim_lag']} inFaseD={n in FaseD} inFSM4={n in FSM4} inCHoCH={n in CHoCH} year={_yr(e['t'])}")
# quantos dos winners cortados sao cortados por reclaim_lag alto (o mesmo motivo que corta losers)?
print("  reclaim_lag>4 entre winners cortados:", sum(1 for n in win_cut if E[n]['reclaim_lag']>4),"/",len(win_cut))
print("  reclaim_lag>4 entre losers cortados :", sum(1 for n in los_cut if E[n]['reclaim_lag']>4),"/",len(los_cut))
print("="*80)

# ---------- ATAQUE 4: fragilidade 2026 (virar cada trade mantido de 2026) ----------
kept26=[n for n in FINAL if _yr(E[n]["t"])=="2026"]
w26=sum(E[n]["out"] for n in kept26); n26=len(kept26)
print(f"ATAQUE 4 — 2026 kept: {w26}/{n26}={w26/n26:.3f}. base 2026={sum(e['out'] for e in ENTRIES if _yr(e['t'])=='2026')}/{sum(1 for e in ENTRIES if _yr(e['t'])=='2026')}")
# virar 1 winner->loser
print(f"  se 1 winner 2026 vira loser: {w26-1}/{n26}={(w26-1)/n26:.3f}  (base26={23/50:.3f})")
print(f"  se 2 viram: {w26-2}/{n26}={(w26-2)/n26:.3f}")
# quantos winners 2026 tem margem minima? (nao temos R aqui, so out) -> conta
print(f"  winners 2026 mantidos (n): {[n for n in kept26 if E[n]['out']==1]}")
print("="*80)

# ---------- ATAQUE 5: interseccao vs uniao — efeito mecanico ----------
print("ATAQUE 5 — hit por operacao de conjunto (FaseD hit=%.3f FSM4 hit=%.3f):"%(
    score(FaseD)["hit3r_kept"], score(FSM4)["hit3r_kept"]))
for nm,mask in [("FaseD",FaseD),("FSM4",FSM4),("FaseD|FSM4",FaseD|FSM4),("FaseD&FSM4",FaseD&FSM4)]:
    m=score(mask); print(f"  {nm:12s} N={m['N_kept']:>2} hit={m['hit3r_kept']:.3f} poison={m['poison_ratio']} y25={m['y2025']} y26={m['y2026']}")
# teste mecanico: intersectar DUAS masks ALEATORIAS do MESMO tamanho sobe o hit por acaso?
random.seed(20260707)
alln=list(E); base_hit=52/96
sizes=(len(FaseD),len(FSM4))
sims=[]
for _ in range(20000):
    a=set(random.sample(alln,sizes[0])); b=set(random.sample(alln,sizes[1]))
    inter=a&b
    if len(inter)>=20:
        w=sum(E[n]["out"] for n in inter)
        sims.append(w/len(inter))
print(f"  NULL mecanico interseccao (2 masks aleatorias N={sizes}): "
      f"N>=20 em {len(sims)}/20000; hit median={st.median(sims):.3f} q90={sorted(sims)[int(.9*len(sims))]:.3f} "
      f"max={max(sims):.3f}; P(hit>=0.682)={sum(1 for x in sims if x>=0.682)/len(sims):.4f}")
print("  -> se a interseccao aleatoria ja sobe o hit, parte do +14pp e mecanico (menor N).")
