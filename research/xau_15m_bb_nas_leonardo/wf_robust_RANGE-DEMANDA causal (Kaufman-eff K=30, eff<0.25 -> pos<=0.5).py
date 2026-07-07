#!/usr/bin/env python3
"""ROBUSTEZ audit: RANGE-DEMANDA causal (Kaufman-eff K=30, eff<0.25 -> pos<=0.5).
Filtro CAUSAL (features so usam barras <=j). keep_ns reconstruido e verificado vs strict_metrics.
Null de multiplicidade/winner-curse: permuta/roda os outcomes dos 96, aplica o MESMO filtro
(tamanho fixo N_kept), mede com que frequencia hit3r_kept >= observado."""
import sys, random
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import CL,HI,LO,ENTRIES,score
import datetime as dt

def eff(j,K=30):
    if j-K<0: return None
    net=abs(CL[j]-CL[j-K]); vol=sum(abs(CL[k]-CL[k-1]) for k in range(j-K+1,j+1))
    return net/vol if vol>0 else None
def pos_range(e,K=30):  # posicao causal do ent dentro do range hi-lo das ultimas K barras (<=j)
    j=e["j"]; lo=min(LO[j-K:j+1]); hi=max(HI[j-K:j+1])
    return (e["ent"]-lo)/(hi-lo) if hi>lo else 0.5

# --- filtro estrito-causal: eff<0.25 (range) => exige pos<=0.5 (demanda no fundo do range) ---
keep_ns=[]
for e in ENTRIES:
    er=eff(e["j"]); p=pos_range(e)
    if er is not None and er<0.25 and p>0.5:   # ranging + entrada no topo -> CORTA
        continue
    keep_ns.append(e["n"])
keep_set=set(keep_ns)
s=score(keep_ns)
print("VERIFY keep_ns:",s)

sel=[e for e in ENTRIES if e["n"] in keep_set]
N_kept=len(sel)
obs_w=sum(e["out"] for e in sel)
obs_hit=obs_w/N_kept
TOTW=sum(e["out"] for e in ENTRIES); TOTN=len(ENTRIES)
print(f"N_kept={N_kept} obs_hit={obs_hit:.4f} obs_winners={obs_w} totalW={TOTW}/{TOTN}")

# --- NULL 1: permutacao aleatoria dos outcomes (filtro fixo) ---
outs=[e["out"] for e in ENTRIES]
idx_kept=[k for k,e in enumerate(ENTRIES) if e["n"] in keep_set]
random.seed(42); TR=20000; ge=0
for _ in range(TR):
    random.shuffle(outs)
    w=sum(outs[k] for k in idx_kept)
    if w/N_kept >= obs_hit-1e-9: ge+=1
null_p_perm=ge/TR

# --- NULL 2: rotacoes do vetor de outcomes (preserva autocorrelacao temporal) ---
base=[e["out"] for e in ENTRIES]; ge_r=0; tot_r=0
for shift in range(1,TOTN):
    rot=base[shift:]+base[:shift]
    w=sum(rot[k] for k in idx_kept); tot_r+=1
    if w/N_kept >= obs_hit-1e-9: ge_r+=1
null_p_rot=ge_r/tot_r

print(f"NULL perm  P(null>=obs)={null_p_perm:.4f} ({ge}/{TR})")
print(f"NULL rot   P(null>=obs)={null_p_rot:.4f} ({ge_r}/{tot_r})")

# --- gates ---
poison_ok = s["winners_cut"] < s["losers_cut"]
def hit(sub):
    return (sum(e["out"] for e in sub), len(sub))
y25=[e for e in sel if dt.datetime.utcfromtimestamp(int(e["t"])).year==2025]
y26=[e for e in sel if dt.datetime.utcfromtimestamp(int(e["t"])).year==2026]
base_rate=TOTW/TOTN
w25,n25=hit(y25); w26,n26=hit(y26)
h25=w25/n25 if n25 else 0; h26=w26/n26 if n26 else 0
both_years_ok = (h25>base_rate) and (h26>base_rate)
null_p=null_p_perm
survives = (null_p<0.1) and poison_ok and both_years_ok and (N_kept>=20)
print(f"poison_ok={poison_ok} (wc {s['winners_cut']} < lc {s['losers_cut']})")
print(f"y2025 {w25}/{n25}={h25:.3f}  y2026 {w26}/{n26}={h26:.3f}  base={base_rate:.3f}  both_years_ok={both_years_ok}")
print(f"null_p={null_p:.4f}  N_kept={N_kept}  SURVIVES={survives}")
