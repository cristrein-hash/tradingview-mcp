#!/usr/bin/env python3
"""DEVIL'S ADVOCATE — COMPOSITE MINING NULL (winner's-curse) para FaseD∩FSM4 (XAU 15M LONG 3R).

Ataca a multiplicidade COMPOSTA. As masks das 7 familias de features sao TODAS outcome-independent
(features causais estruturais; nenhuma usa e['out']). Logo, sob H0 (outcomes aleatorios) as masks
sao FIXAS e so a SELECAO muda. Reconstruo o menu inteiro de masks realmente avaliadas e re-executo
a pipeline two-stage (best-per-familia + set-ops dos top-3) sobre outcomes embaralhados.
Se o hit-3R observado (0.682) cai perto/abaixo da mediana do null -> artefato de mineracao.
"""
import sys, io, contextlib, random, statistics as st
HERE="/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo"
sys.path.insert(0, HERE)
from agent_ctx_kit import ENTRIES
import datetime as dt
def _pc(x):
    return bin(x).count('1')

# import geradores de mask das familias (suprime prints de top-level)
with contextlib.redirect_stdout(io.StringIO()):
    import wf_ph_bear_active as BA
    import wf_ph_choch_up_fresh as CH
    import wf_ph_combined_4state as CM
    import wf_ph_distribution_top as DT
    import wf_ph_flush_reclaim_init as FR
    import wf_ph_flush_velocity_asym as FV
    import wf_ph_leg_cycle_pos as LC

# ---- posicoes / bitmasks ----
NS   = [e["n"] for e in ENTRIES]
POS  = {n:p for p,n in enumerate(NS)}
NTOT = len(NS)
def _yr(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y")
YEAR = [_yr(e["t"]) for e in ENTRIES]
y25_bits = sum(1<<p for p in range(NTOT) if YEAR[p]=="2025")
y26_bits = sum(1<<p for p in range(NTOT) if YEAR[p]=="2026")
n25 = _pc(y25_bits); n26 = _pc(y26_bits)
WTOT = sum(e["out"] for e in ENTRIES)
OBS_WIN_BITS = sum(1<<p for p,e in enumerate(ENTRIES) if e["out"]==1)

def to_bits(keep_ns):
    b=0
    for n in keep_ns:
        if n in POS: b |= (1<<POS[n])
    return b

# ---- reconstruir o MENU de masks por familia ----
fam = {}

# 1) FaseD (bear_active): 10 variantes
fam["FaseD"] = [to_bits(BA.keep_set(**kw)) for _,kw in BA.VARIANTS]

# 2) CHoCH (choch_up_fresh): 6 variantes
fam["CHoCH"] = [to_bits(CH.keep_variant(v)) for v in CH.VARIANTS]

# 3) FSM4 (combined_4state): grid sobre P (b_reclaim x a_push x a_entpos)
fsm=[]
for br in (3,4,5,6):
    for ap in (1,2,3):
        for ep in (-2.0,-3.0,-4.0,-5.0):
            CM.P = dict(b_reclaim=br, a_push=ap, a_entpos=ep)
            ks = {e["n"] for e in ENTRIES if CM.classify(e) in ("A","B")}
            fsm.append(to_bits(ks))
fam["FSM4"] = fsm

# 4) DistTop (distribution_top): grid C-sweep + D-sweep
dt_masks=[]
for W in (48,72,96):
    for frac in (0.45,0.55,0.65):
        for touch in (3,5,8):
            for dec in (False,True):
                for be in (False,True):
                    ks=[e["n"] for e in ENTRIES if not DT.phase_cut(e,W,frac,touch,dec,be)]
                    dt_masks.append(to_bits(ks))
for W in (48,72,96):
    for pos_thr in (0.3,0.4,0.5,0.6):
        ks=[e["n"] for e in ENTRIES if not DT.phaseD_cut(e,W,pos_thr)]
        dt_masks.append(to_bits(ks))
fam["DistTop"]=dt_masks

# 5) FlushRec (flush_reclaim_init): grid 768
fr_masks=[]
for DR in (0.0,1.5,2.0,2.5):
    for RL in (3,4,5,6):
        for SDmax in (0.6,0.9,9.9):
            for SDmin in (-9.9,):
                for req in (False,):
                    for spd in (99,):
                        for vsl in (99.0,-0.4,-0.55,-0.7):
                            for vrp in (0.6,0.65,0.7,0.75):
                                ks=FR.classify(DR,RL,SDmax,SDmin,req,spd,vsl,vrp)
                                if len(ks)>=1: fr_masks.append(to_bits(ks))
fam["FlushRec"]=fr_masks

# 6) FlushVel (flush_velocity_asym): 5 variantes
fam["FlushVel"]=[to_bits(FV.classify(rule)) for rule in FV.VARIANTS.values()]

# 7) LegCyc (leg_cycle_pos): grid 300
lc_masks=[]
for P in (4,5,6,7,8):
    for R in (0.35,0.40,0.45,0.50,0.55,0.60):
        for Phi in (99,8,9,10,12):
            for be in (False,True):
                lc_masks.append(to_bits(LC.classify(P,R,be,Phi)))
fam["LegCyc"]=lc_masks

total_masks=sum(len(v) for v in fam.values())
uniq=len({m for v in fam.values() for m in v})
print("MENU DE MASKS (looks reais na maquina de mineracao):")
for k,v in fam.items(): print(f"  {k:9s}: {len(v):4d} variantes")
print(f"  TOTAL       : {total_masks} avaliacoes de mask  ({uniq} masks distintas)")
print(f"  + camada synth: 13 set-ops sobre 3 survivors  => looks compostos >> {total_masks}")
print("="*78)

# ---- scorer sob um outcome bitmask ----
def evalmask(mb, win_bits):
    Nk = _pc(mb)
    if Nk < 20: return None
    wk = _pc(mb & win_bits)
    wc = WTOT - wk                      # winners cortados
    cut = NTOT - Nk
    lc  = cut - wc                      # losers cortados
    if lc <= 0: return None
    if wc >= lc: return None            # poison_ok: corta mais loser que winner
    if wc/lc >= 0.9: return None        # poison<0.9
    # both-years > base-do-ano (base recalculada sob o shuffle)
    k25=_pc(mb&y25_bits); w25=_pc(mb&y25_bits&win_bits)
    k26=_pc(mb&y26_bits); w26=_pc(mb&y26_bits&win_bits)
    if k25==0 or k26==0: return None
    b25=_pc(y25_bits&win_bits)/n25
    b26=_pc(y26_bits&win_bits)/n26
    if not (w25/k25 > b25 and w26/k26 > b26): return None
    return wk/Nk

def best_of_menu(win_bits):
    """Pipeline two-stage: campeao por familia (max hit gate-passing) + set-ops dos top-3."""
    champs=[]   # (hit, mask, family)
    for k,masks in fam.items():
        best=None
        for m in masks:
            h=evalmask(m, win_bits)
            if h is not None and (best is None or h>best[0]): best=(h,m)
        if best is not None: champs.append((best[0],best[1],k))
    if not champs: return None
    champs.sort(reverse=True)
    best_hit=champs[0][0]
    # set-ops sobre os top-3 campeoes (espelha o synthesizer)
    top=[c[1] for c in champs[:3]]
    combos=[]
    import itertools
    for a,b in itertools.combinations(top,2):
        combos.append(a|b); combos.append(a&b)
    if len(top)==3:
        a,b,c=top
        combos += [a|b|c, a&b&c, (a&b)|(a&c)|(b&c)]
    for m in combos:
        h=evalmask(m, win_bits)
        if h is not None and h>best_hit: best_hit=h
    return best_hit

# ---- sanity: pipeline no outcome REAL deve alcancar >= 0.682 ----
real=best_of_menu(OBS_WIN_BITS)
print(f"Pipeline sobre outcomes REAIS: melhor hit gate-passing = {real:.4f}  (FINAL reportado=0.682)")

# ---- MINING NULL ----
OBS=0.682
rng=random.Random(20260707)
base_positions=list(range(NTOT))
ITERS=1500
ge=0; dist=[]; nfail=0
onevec=[1]*WTOT+[0]*(NTOT-WTOT)
for it in range(ITERS):
    rng.shuffle(onevec)
    wb=0
    for p,o in enumerate(onevec):
        if o: wb|=(1<<p)
    bh=best_of_menu(wb)
    if bh is None: nfail+=1; continue
    dist.append(bh)
    if bh >= OBS - 1e-9: ge+=1
p_comp=(ge+1)/(ITERS+1)
dist.sort()
def q(x): return dist[min(len(dist)-1,int(x*len(dist)))]
print("="*78)
print(f"COMPOSITE MINING NULL ({ITERS} shuffles; menu={total_masks} masks + set-ops top-3):")
print(f"  best-hit sob H0: median={st.median(dist):.4f}  q75={q(.75):.4f}  q90={q(.90):.4f}  max={dist[-1]:.4f}")
print(f"  shuffles sem nenhum gate-passer: {nfail}")
print(f"  P(best-hit_null >= {OBS}) = {p_comp:.4f}   [{ge}/{ITERS}]")
print("="*78)
verdict = ("ARTEFATO DE MINERACAO" if p_comp>0.10 or st.median(dist)>=OBS-0.02
           else "sobrevive o composite null")
print("VEREDICTO composite-null:", verdict)
