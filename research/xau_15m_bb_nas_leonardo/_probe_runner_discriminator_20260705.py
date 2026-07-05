#!/usr/bin/env python3
"""SANITY_PROBE — screening de lentes candidatas para hit-3R (não análise final; alimenta desenho
convergente/trajetória). Busca do 'positivo descartado': o que separa fractais que ATINGEM 3R dos que
não, no universo NAO-BEAR, priorizando TRAJETORIA/CONTEXTO. Ranqueia ~18 lentes; reporta TODAS."""
import json, hashlib, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
NB = [r for r in U if r["g_v5h"] != "BEAR"]
WEEKS = len({r["g_week"] for r in U})
def h3(rows): return (sum(1 for r in rows if R3[r["cj_t"]]["R3"] >= 3), len(rows))
base_h, base_n = h3(NB)
print(f"NAO-BEAR N={base_n} hit3R base {100*base_h/base_n:.1f}% · breakeven 25% · {base_n/WEEKS:.1f}/sem")
L = {
 "HTF 4H&1D up": lambda r: fv(r, "h4n_trend") == 1 and fv(r, "h1n_trend") == 1,
 "h4n_trend up": lambda r: fv(r, "h4n_trend") == 1,
 "clean_sky<=0.3": lambda r: fv(r, "clean_sky_atr", 9) <= 0.3,
 "h1n_clean_sky<=0.3": lambda r: fv(r, "h1n_clean_sky_atr", 99) <= 0.3,
 "n_supply<=20": lambda r: fv(r, "n_supply_overhead", 99) <= 20,
 "reclaim_atr>=2": lambda r: fv(r, "reclaim_atr", 0) >= 2.0,
 "confirm_body>=0.6": lambda r: fv(r, "confirm_body_atr", 0) >= 0.6,
 "up_closes>=3": lambda r: fv(r, "up_closes_pc", 0) >= 3,
 "swept_prior_low": lambda r: fv(r, "swept_prior_low") == 1,
 "is_monforte": lambda r: fv(r, "is_monforte") == 1,
 "micro_hl": lambda r: fv(r, "micro_hl") == 1,
 "h1n_choch_up_rec": lambda r: fv(r, "h1n_choch_up_rec") == 1,
 "h4n_choch_up_rec": lambda r: fv(r, "h4n_choch_up_rec") == 1,
 "nas_long_16": lambda r: fv(r, "nas_long_16", 0) >= 1,
 "htf_demand_confl": lambda r: fv(r, "htf_demand_confluence") == 1,
 "downleg_eff>=0.6": lambda r: fv(r, "downleg_eff", 0) >= 0.6,
 "pullback 0.4-0.7": lambda r: 0.4 <= fv(r, "pullback_depth", 0) <= 0.7,
 "reclaim_ema<=3": lambda r: fv(r, "reclaim_ema_bars", 99) <= 3,
}
rows = []
for nm, fn in L.items():
    hh, nn = h3([r for r in NB if fn(r)])
    rows.append((nm, hh, nn, hh / nn if nn else 0))
rows.sort(key=lambda x: -x[3])
print("\nLENTES por hit-3R (ordenado; ledger integral):")
for nm, hh, nn, rt in rows:
    fl = " <<<" if rt >= 0.35 and nn >= 100 else ""
    print(f"  {100*rt:>5.1f}%  N{nn:>4}  {nn/WEEKS:>4.1f}/sem  {nm}{fl}")
top = [nm for nm, hh, nn, rt in rows if rt >= 0.33 and nn >= 100][:4]
print(f"\nCONVERGENCIA das top ({top}):")
for k in (2, 3):
    sub = [r for r in NB if sum(1 for nm in top if L[nm](r)) >= k]
    hh, nn = h3(sub)
    print(f"  >=%d de %d: N%d hit3R %.1f%% %.2f/sem" % (k, len(top), nn, 100 * hh / nn if nn else 0, nn / WEEKS))
