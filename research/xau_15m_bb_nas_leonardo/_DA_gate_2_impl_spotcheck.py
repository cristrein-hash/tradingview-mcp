#!/usr/bin/env python3
"""DA MTF SIGNATURE GATE — ATAQUE 2: implementação do gate vs mapeamento.
(a) Cross-check numérico: recomputa as duas pernas com as funções do gate em
    (t_dele, entry_dele) e compara com o ctx armazenado no JSON do mapeamento
    (dist_supply_atr/inside_demand/dist_demand_atr) — lentes verbatim?
(b) Fontes: mapeamento usa 4 blocos 15M; gate usa 9 — diferença de zonas ativas na janela?
(c) ATR asof: distribuição de (t0 − t_barra_1H_asof) nos cj (barra 1H parcial?) e
    sensibilidade: gate com ATR1H da barra anterior fechada (E2 N muda?).
(d) Spot-check manual de 5 candidatos: lista zonas relevantes e decisão.
Read-only; sem commit."""
import json, bisect, hashlib, random
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SBX = Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/mtf_sandbox")
random.seed(7)

CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = sorted([json.loads(l) for l in open(CANON)], key=lambda r: r["cj_t"])

def load_zones_series(paths):
    zones = []; series = {}
    for p in paths:
        d = json.load(open(p))
        zs = d["zones"].values() if isinstance(d["zones"], dict) else d["zones"]
        zones += list(zs)
        for b in d["series"]: series.setdefault(b["t"], b)
    S = sorted(series.values(), key=lambda b: b["t"])
    return zones, S, [b["t"] for b in S]

Z15, S15, T15 = load_zones_series(sorted((HERE / "primitives").glob("*.primitives.json")))
Z60, S60, T60 = load_zones_series(sorted(SBX.glob("prim60/*.primitives.json")))
# fontes do MAPEAMENTO (4 blocos 15M, mesmos 1H)
MAP15 = [HERE / "primitives" / f"XAUUSD_15m_replay_{k}.primitives.json" for k in
         ("2025-05-25_to_2025-08-25", "2025-08-25_to_2025-11-25", "2025-11-25_to_2026-02-25",
          "2026-02-25_to_2026-05-25_rerun_customOBbaseline")]
Z15m, S15m, T15m = load_zones_series(MAP15)
DEM60 = sorted([z for z in Z60 if "DEMAND" in str(z.get("text", "")).upper()], key=lambda z: z["born_t"])
SUP15 = sorted([z for z in Z15 if "SUPPLY" in str(z.get("text", "")).upper()], key=lambda z: z["born_t"])

def atr_asof(S, T, t0):
    j = bisect.bisect_right(T, t0) - 1
    return (S[j].get("atr") or 1.0) if j >= 0 else 1.0

def active(zs, t0):
    return [z for z in zs if z["born_t"] <= t0 <= z.get("last_t", z["born_t"])]

def legs(t0, price):
    a15 = atr_asof(S15, T15, t0); a60 = atr_asof(S60, T60, t0)
    sup = active(SUP15, t0); dem = active(DEM60, t0)
    sup_above = [(z["low"] - price) / a15 for z in sup if z["low"] >= price]
    ds = min(sup_above) if sup_above else None
    inside = any(z["low"] <= price <= z["high"] for z in dem)
    below = [(price - z["high"]) / a60 for z in dem if z["high"] <= price]
    dd = min(below) if below else None
    sup_ok = ds is None or ds >= 3.0
    dem_ok = inside or (dd is not None and dd <= 1.0)
    return ds, inside, dd, sup_ok, dem_ok

# (a) cross-check vs ctx do mapeamento
M = json.load(open(HERE / "results" / "cris_trades_mtf_indicator_map_20260704.json"))
mm = 0; diffs = []
for tr in M["trades"]:
    c15 = tr["ctx"]["15M"]; c60 = tr["ctx"]["1H"]
    ds, inside, dd, sup_ok, dem_ok = legs(tr["t"], tr["entry"])
    map_sup_ok = c15["dist_supply_atr"] is None or c15["dist_supply_atr"] >= 3.0
    map_dem_ok = c60["inside_demand"] == 1 or (c60["dist_demand_atr"] is not None and c60["dist_demand_atr"] <= 1.0)
    same = (sup_ok == map_sup_ok) and (dem_ok == map_dem_ok)
    mm += same
    d_ds = None
    if ds is not None and c15["dist_supply_atr"] is not None:
        d_ds = abs(ds - c15["dist_supply_atr"])
    if not same or (d_ds is not None and d_ds > 0.05):
        diffs.append((tr["n"], round(ds, 2) if ds is not None else None, c15["dist_supply_atr"],
                      inside, c60["inside_demand"], round(dd, 2) if dd is not None else None, c60["dist_demand_atr"]))
print(f"(a) cross-check lentes gate vs ctx mapeamento nos 35 (t_dele, entry_dele): {mm}/35 idênticos nas 2 pernas")
for d in diffs: print("   DIFF:", d)

# (b) zonas 15M: 9 blocos vs 4 blocos — impacto na perna supply na janela dos 35
SUP15m = sorted([z for z in Z15m if "SUPPLY" in str(z.get("text", "")).upper()], key=lambda z: z["born_t"])
w0 = min(tr["t"] for tr in M["trades"]); w1 = max(tr["t"] for tr in M["trades"])
extra = [z for z in SUP15 if z not in SUP15m and z.get("last_t", z["born_t"]) >= w0 and z["born_t"] <= w1]
print(f"(b) zonas SUPPLY 15M: 9-blocos {len(SUP15)} vs 4-blocos {len(SUP15m)}; ativas na janela dos 35 só nos 9-blocos: {len(extra)}")

# (c) ATR 1H asof: barra parcial?
lags = []
for r in U:
    if r["cj_t"] > T60[-1]: continue
    j = bisect.bisect_right(T60, r["cj_t"]) - 1
    lags.append(r["cj_t"] - T60[j])
from collections import Counter
print(f"(c) lag cj→barra 1H asof (s): {Counter(lags).most_common(6)} — se <3600, barra 1H possivelmente parcial no cj")
def atr_prev(t0):
    j = bisect.bisect_right(T60, t0) - 1
    return (S60[max(0, j - 1)].get("atr") or 1.0)
def demand_near_v(t0, price, a):
    for z in DEM60:
        if z["born_t"] > t0: break
        if z["born_t"] <= t0 <= z.get("last_t", z["born_t"]):
            if z["low"] <= price <= z["high"]: return True
            if z["high"] <= price and (price - z["high"]) / a <= 1.0: return True
    return False
n1 = n2 = 0
for r in U:
    if r["cj_t"] > T60[-1]: continue
    ds, inside, dd, sup_ok, dem_ok = legs(r["cj_t"], r["g_entry"])
    if sup_ok and demand_near_v(r["cj_t"], r["g_entry"], atr_asof(S60, T60, r["cj_t"])): n1 += 1
    if sup_ok and demand_near_v(r["cj_t"], r["g_entry"], atr_prev(r["cj_t"])): n2 += 1
print(f"    E2 pass com ATR1H asof (como no teste): {n1} · com ATR1H da barra ANTERIOR fechada: {n2}")

# (d) spot-check manual: 5 candidatos (3 pass, 2 fail) com zonas listadas
cov = [r for r in U if r["cj_t"] <= T60[-1]]
passes = [r for r in cov if legs(r["cj_t"], r["g_entry"])[3] and legs(r["cj_t"], r["g_entry"])[4]]
fails = [r for r in cov if not (legs(r["cj_t"], r["g_entry"])[3] and legs(r["cj_t"], r["g_entry"])[4])]
picks = random.sample(passes, 3) + random.sample(fails, 2)
print("(d) spot-checks:")
for r in picks:
    t0, px = r["cj_t"], r["g_entry"]
    a15 = atr_asof(S15, T15, t0); a60 = atr_asof(S60, T60, t0)
    ds, inside, dd, sup_ok, dem_ok = legs(t0, px)
    print(f"  cj {dt.datetime.utcfromtimestamp(t0)} px {px} ATR15 {a15:.2f} ATR60 {a60:.2f} → sup_ok {sup_ok} dem_ok {dem_ok}")
    sa = sorted([z for z in active(SUP15, t0) if z["low"] >= px], key=lambda z: z["low"])[:3]
    for z in sa:
        print(f"     SUP15 low {z['low']} high {z['high']} born {dt.datetime.utcfromtimestamp(z['born_t'])} dist {(z['low']-px)/a15:.2f} ATR")
    da_ = sorted(active(DEM60, t0), key=lambda z: abs(px - z["high"]))[:3]
    for z in da_:
        rel = "INSIDE" if z["low"] <= px <= z["high"] else ("below" if z["high"] <= px else "ABOVE_price")
        dist = (px - z["high"]) / a60 if z["high"] <= px else (z["low"] - px) / a60 if z["low"] >= px else 0
        print(f"     DEM60 low {z['low']} high {z['high']} born {dt.datetime.utcfromtimestamp(z['born_t'])} {rel} dist {dist:.2f} ATR60")
