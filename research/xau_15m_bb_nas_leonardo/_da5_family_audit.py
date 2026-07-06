#!/usr/bin/env python3
"""DA5 audit — verifica ALEGAÇÃO A (arquétipos reais?) e ALEGAÇÃO B (negativos corretos?).
Reusa o pipeline do family_feature_map ate WINNERS. NAO commita, NAO modifica nada."""
import json, bisect, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "family_feature_map_20260706.py").read_text().split('WINNERS = [')[0])
WINNERS = [u for u in UNIV if u["_circ"] and R3[u["cj_t"]]["R3"] >= 3]
FAMS = ("BANDA", "FUNDO", "RASO")
SOSIA = {f: [u for u in UNIV if u["_fam"] == f and not u["_circ"]] for f in FAMS}

def med(rows, k):
    v = sorted(fv(u, k) for u in rows if fv(u, k) is not None)
    return v[len(v)//2] if v else None
def vals(rows, k):
    return [fv(u, k) for u in rows if fv(u, k) is not None]
def mwu(a, b):
    """Mann-Whitney U com aproximacao normal. Retorna (U, z, p_two, dir)."""
    if len(a) < 3 or len(b) < 3: return None
    comb = sorted([(x, 0) for x in a] + [(x, 1) for x in b])
    # ranks com ties medios
    ranks = [0.0]*len(comb); i = 0
    while i < len(comb):
        j = i
        while j < len(comb) and comb[j][0] == comb[i][0]: j += 1
        r = (i + j + 1) / 2.0
        for k in range(i, j): ranks[k] = r
        i = j
    Ra = sum(ranks[k] for k in range(len(comb)) if comb[k][1] == 0)
    na, nb = len(a), len(b)
    Ua = Ra - na*(na+1)/2.0
    mu = na*nb/2.0; sd = math.sqrt(na*nb*(na+nb+1)/12.0)
    if sd == 0: return None
    z = (Ua - mu)/sd
    from math import erf
    p = 2*(1 - 0.5*(1+erf(abs(z)/math.sqrt(2))))
    return (Ua, z, p)

ALL = UNIV
CENTRAL = ["h1_trend", "sell_bub_w", "h4n_dist_demand_atr"]
print("="*90)
print("VETOR A1+A3 — winner-in-fam vs SÓSIA-in-fam vs POP-GERAL (medianas) + MWU winner-vs-sósia")
print("="*90)
for f in ("BANDA", "FUNDO", "RASO"):
    W = [u for u in WINNERS if u["_fam"] == f]
    Sx = SOSIA.get(f, [])
    print(f"\n--- {f} (winners {len(W)} · sósias {len(Sx)} · pop-geral {len(ALL)}) ---")
    for k in CENTRAL:
        mw, ms, mg = med(W, k), med(Sx, k), med(ALL, k)
        res = mwu(vals(W, k), vals(Sx, k))
        tag = ""
        if res:
            _, z, p = res
            tag = f"MWU z={z:+.2f} p={p:.4f} {'SIG' if p < 0.05 else 'ns'}"
        # base-rate check: sósia-da-familia == pop-geral?  se sim -> feature nao e' da familia
        print(f"  {k:<22} win {str(round(mw,2)) if mw is not None else '—':>7} | "
              f"sósia-fam {str(round(ms,2)) if ms is not None else '—':>7} | "
              f"pop-geral {str(round(mg,2)) if mg is not None else '—':>7} | {tag}")

print("\n" + "="*90)
print("VETOR A2 — features sep=1.00: BINÁRIAS/degeneradas (IQR real ~0) vs CONTÍNUAS?")
print("="*90)
SEP1 = ["killzone", "h1n_in_demand", "htf_demand_confluence", "h1_trend",
        "swept_prior_low", "reclaim_ema_bars", "htf_demand_any", "h4n_in_demand",
        "g_box480"] + CENTRAL + ["g_atr", "g_atr_spike", "g_sweep_depth", "h1n_clean_sky_atr"]
for k in sorted(set(SEP1)):
    v = vals(ALL, k)
    if not v: continue
    uniq = sorted(set(v))
    sv = sorted(v)
    q1 = sv[len(sv)//4]; q3 = sv[3*len(sv)//4]
    iqr = q3 - q1
    kind = "BINÁRIA/degenerada (IQR=0, floor 0.01 infla sep)" if iqr == 0 else "CONTÍNUA"
    nu = len(uniq)
    ushow = uniq[:6]
    print(f"  {k:<22} nuniq={nu:<4} IQR={iqr:>7.3f} {kind}  vals~{ushow}")

print("\n" + "="*90)
print("VETOR B3 — DENSIDADE sósia:winner por família (pool-ctx e whole-family)")
print("="*90)
# whole family
for f in ("BANDA", "FUNDO", "RASO"):
    W = [u for u in WINNERS if u["_fam"] == f]
    Sx = SOSIA.get(f, [])
    allf = [u for u in UNIV if u["_fam"] == f]
    r = len(Sx)/len(W) if W else float('nan')
    # winners como fracao de toda a familia = teto de precisao bruto
    prec_ceiling = len(W)/len(allf)*100 if allf else 0
    print(f"  {f:<7} winners {len(W):>4} · sósias {len(Sx):>5} · fam-total {len(allf):>5} "
          f"| ratio sósia:win {r:>6.1f}:1 | winners = {prec_ceiling:4.1f}% da família (teto precisão bruto)")
print("\nOK DA5")
