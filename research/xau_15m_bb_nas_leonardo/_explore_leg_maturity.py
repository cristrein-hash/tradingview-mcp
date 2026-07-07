#!/usr/bin/env python3
"""Exploracao CAUSAL: maturidade da perna macro (exaustao). So barras <= j."""
import sys; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto

def leg_origin(j):
    """Origem da perna de alta corrente = ultimo higher-low CONFIRMADO ate j.
    Usa SO swings com conf_bar<=j (causal). Devolve (origin_low, n_swings_since_origin, origin_idx)."""
    sw=causal_swings_upto(j)   # (tp,idx,price,conf_bar)
    lows=[(idx,pr) for tp,idx,pr,ci in sw if tp=="L"]
    if not lows: return None
    # ultimo higher-low: percorre lows do fim; encontra o mais recente L que e' > L anterior
    # se so ha um low, e' a origem
    origin_idx, origin_pr = lows[-1]
    # procurar o inicio da sequencia de higher-lows (a perna): recua enquanto lows sobem
    # origem macro = o low mais antigo da cadeia ascendente corrente
    k=len(lows)-1
    while k-1>=0 and lows[k-1][1] < lows[k][1]:
        k-=1
    origin_idx, origin_pr = lows[k]
    # n_swings desde origem = pivos confirmados apos origin_idx
    n_sw=sum(1 for tp,idx,pr,ci in sw if idx>=origin_idx)
    return origin_pr, n_sw, origin_idx

rows=[]
for e in ENTRIES:
    j=e["j"]; lo=leg_origin(j)
    cl=CL[j]; a=ATR[j] or 5.0
    if lo is None:
        ext=None; n_sw=None
    else:
        origin_pr,n_sw,oidx=lo
        ext=(cl-origin_pr)/a
    rows.append((e["n"],e["out"],ext,n_sw))

# distribuicao winners vs losers
import statistics as st
def summ(vals):
    vals=[v for v in vals if v is not None]
    if not vals: return "n/a"
    return f"n={len(vals)} min={min(vals):.2f} q25={st.quantiles(vals,n=4)[0]:.2f} med={st.median(vals):.2f} q75={st.quantiles(vals,n=4)[2]:.2f} max={max(vals):.2f}"

win_ext=[r[2] for r in rows if r[1]==1]
los_ext=[r[2] for r in rows if r[1]==0]
print("EXTENSION (CL-origin)/ATR:")
print("  winners:",summ(win_ext))
print("  losers :",summ(los_ext))
win_sw=[r[3] for r in rows if r[1]==1]
los_sw=[r[3] for r in rows if r[1]==0]
print("N_SWINGS since origin:")
print("  winners:",summ(win_sw))
print("  losers :",summ(los_sw))

# quantos None
print("None ext:",sum(1 for r in rows if r[2] is None))

# sweep thresholds: keep se ext <= thr (rejeita esticado)
print("\n=== SWEEP ext<=thr (rejeita perna esticada) ===")
for thr in [4,5,6,7,8,10,12,15,20,25,30]:
    keep=[r[0] for r in rows if r[2] is not None and r[2]<=thr]
    # incluir None? Nao rejeitar por falta de dados -> keep
    keepN=[r[0] for r in rows if r[2] is None]
    ks=set(keep)|set(keepN)
    sc=score(ks)
    print(f"thr={thr:>3}: N={sc['N_kept']:>2} hit={sc['hit3r_kept']:.3f} pois={sc['poison_ratio']:.2f} wc={sc['winners_cut']} lc={sc['losers_cut']} y25={sc['y2025']} y26={sc['y2026']}")

print("\n=== SWEEP n_swings<=thr ===")
for thr in [2,3,4,5,6,7,8,10]:
    keep=[r[0] for r in rows if r[3] is not None and r[3]<=thr]
    keepN=[r[0] for r in rows if r[3] is None]
    ks=set(keep)|set(keepN)
    sc=score(ks)
    print(f"sw<={thr}: N={sc['N_kept']:>2} hit={sc['hit3r_kept']:.3f} pois={sc['poison_ratio']:.2f} wc={sc['winners_cut']} lc={sc['losers_cut']} y25={sc['y2025']} y26={sc['y2026']}")

print("\n=== INVERSE: keep se ext>=thr (rejeita FRESH) ===")
for thr in [4,5,6,7,8,10,12,15]:
    keep=[r[0] for r in rows if r[2] is not None and r[2]>=thr]
    sc=score(set(keep))
    print(f"ext>={thr:>3}: N={sc['N_kept']:>2} hit={sc['hit3r_kept']:.3f} pois={sc['poison_ratio']:.2f} wc={sc['winners_cut']} lc={sc['losers_cut']} y25={sc['y2025']} y26={sc['y2026']}")

print("\n=== MID-BAND: lo<=ext<=hi ===")
for lo_t,hi_t in [(5,20),(6,25),(8,25),(5,25),(4,20),(6,20),(8,30),(5,30),(4,25),(10,30)]:
    keep=[r[0] for r in rows if r[2] is not None and lo_t<=r[2]<=hi_t]
    sc=score(set(keep))
    print(f"[{lo_t},{hi_t}]: N={sc['N_kept']:>2} hit={sc['hit3r_kept']:.3f} pois={sc['poison_ratio']:.2f} wc={sc['winners_cut']} lc={sc['losers_cut']} y25={sc['y2025']} y26={sc['y2026']}")
