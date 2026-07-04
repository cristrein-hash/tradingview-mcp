#!/usr/bin/env python3
"""DA MTF SIGNATURE GATE — ATAQUES 3/4/5:
(3) reprodução independente dos painéis E1 (BASE∩GATE) e E2 (UNIVERSE∩GATE),
    runner-kill, células por regime — implementação de painel própria.
(4) autópsia dos runners: QUAL perna mata (sup_far vs dem_near) e geometria
    (preço vs demanda 1H: inside / near / abaixo-da-zona / longe).
(5) os 21 fora-da-base do Sistema A sob as duas pernas no cj deles.
Read-only; sem commit."""
import json, bisect, hashlib
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SBX = Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/mtf_sandbox")
SB = 0.80

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
DEM60 = sorted([z for z in Z60 if "DEMAND" in str(z.get("text", "")).upper()], key=lambda z: z["born_t"])
SUP15 = sorted([z for z in Z15 if "SUPPLY" in str(z.get("text", "")).upper()], key=lambda z: z["born_t"])
H_END = T60[-1]

def atr_asof(S, T, t0):
    j = bisect.bisect_right(T, t0) - 1
    return (S[j].get("atr") or 1.0) if j >= 0 else 1.0

def geom(t0, price):
    """retorna (sup_ok, dem_ok, dist_sup_atr, dem_state, dist_dem_atr)
    dem_state: INSIDE / NEAR(<=1) / BELOW_FAR(>1) / UNDER_ZONE (preço abaixo do low da demanda mais próxima) / NO_DEMAND"""
    a15 = atr_asof(S15, T15, t0); a60 = atr_asof(S60, T60, t0)
    ds = None
    for z in SUP15:
        if z["born_t"] > t0: break
        if z["born_t"] <= t0 <= z.get("last_t", z["born_t"]) and z["low"] >= price:
            d = (z["low"] - price) / a15
            ds = d if ds is None else min(ds, d)
    act = [z for z in DEM60 if z["born_t"] <= t0 <= z.get("last_t", z["born_t"])]
    inside = any(z["low"] <= price <= z["high"] for z in act)
    below = [(price - z["high"]) / a60 for z in act if z["high"] <= price]
    above = [(z["low"] - price) / a60 for z in act if z["low"] > price and z["high"] > price]
    dd = min(below) if below else None
    if inside: state = "INSIDE"
    elif dd is not None and dd <= 1.0: state = "NEAR"
    elif above and (not below or min(above) < dd): state = "UNDER_ZONE"
    elif dd is not None: state = "BELOW_FAR"
    else: state = "NO_DEMAND"
    sup_ok = ds is None or ds >= 3.0
    dem_ok = inside or (dd is not None and dd <= 1.0)
    return sup_ok, dem_ok, ds, state, dd

def net(r): return r["g_R"] - SB / r["g_risk"]
def panel(rows):
    rows = sorted(rows, key=lambda r: r["cj_t"]); n = len(rows)
    if not n: return None
    R = [net(r) for r in rows]
    eq = pk = dd = 0.0; mL = cl = 0
    for x in R:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    return dict(N=n, NET=round(sum(R), 1), bruto=round(sum(r["g_R"] for r in rows), 1),
                WR=round(100 * sum(1 for x in R if x > 0) / n, 1), DD=round(dd, 1), stk=mL,
                run=sum(1 for r in rows if r["g_R"] >= 3))

G = {}
for r in U:
    if r["cj_t"] > H_END: G[id(r)] = None; continue
    s, d, *_ = geom(r["cj_t"], r["g_entry"])
    G[id(r)] = (s, d)

BASE = [r for r in U if r["g_in_base435"] == 1 and r["g_v5h"] != "BEAR"]
print("(3) REPRODUÇÃO INDEPENDENTE")
print("  baseline:", panel(BASE))
g1 = [r for r in BASE if G[id(r)] and all(G[id(r)])]
print("  E1 BASE∩GATE:", panel(g1))
cut = [r for r in BASE if not (G[id(r)] and all(G[id(r)]))]
print(f"  runner-kill: {sum(1 for r in cut if r['g_R'] >= 3)}/{sum(1 for r in BASE if r['g_R'] >= 3)}")
g2 = [r for r in U if G[id(r)] and all(G[id(r)])]
print("  E2 UNIVERSE∩GATE:", panel(g2))
for rg in ("BULL", "RANGE", "BEAR"):
    print(f"    célula {rg}:", panel([r for r in g2 if r["g_v5h"] == rg]))

print("\n(4) AUTÓPSIA DOS RUNNERS (base435, g_R>=3) — qual perna mata no cj:")
runners = [r for r in BASE if r["g_R"] >= 3]
from collections import Counter
legc = Counter(); states = Counter(); dsl = []; ddl = []
for r in runners:
    s, d, ds, state, dd = geom(r["cj_t"], r["g_entry"])
    legc[("sup" if not s else "") + ("+" if (not s and not d) else "") + ("dem" if not d else "") or "PASS"] += 1
    states[state] += 1
    if ds is not None: dsl.append(ds)
    if dd is not None: ddl.append(dd)
print(f"  pernas que falham: {dict(legc)}")
print(f"  estado vs demanda 1H no cj: {dict(states)}")
dsl.sort(); ddl.sort()
print(f"  dist supply 15M acima (mediana): {dsl[len(dsl)//2]:.2f} ATR (n={len(dsl)})"
      f" · dist acima da demanda 1H (mediana, quando abaixo do preço): {ddl[len(ddl)//2]:.2f} ATR (n={len(ddl)})")
# comparação: mesmos números para os NÃO-runners da base
nonr = [r for r in BASE if r["g_R"] < 3]
legn = Counter(); statn = Counter()
for r in nonr:
    s, d, ds, state, dd = geom(r["cj_t"], r["g_entry"])
    legn[("sup" if not s else "") + ("+" if (not s and not d) else "") + ("dem" if not d else "") or "PASS"] += 1
    statn[state] += 1
print(f"  [controle interno] não-runners base: pernas {dict(legn)} · estados {dict(statn)}")

print("\n(5) OS 21 DO SISTEMA A (fora-da-base) sob as pernas, no cj deles:")
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def sysA(r):
    return (r["g_v5h"] == "BULL" and fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33
            and (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3)
            and (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3)
            and (fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1)
            and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0) and r["g_knife"] == 0)
A21 = [r for r in U if sysA(r) and not r["g_in_base435"]]
print(f"  N={len(A21)} · painel: {panel(A21)}")
lega = Counter(); stata = Counter()
for r in A21:
    s, d, ds, state, dd = geom(r["cj_t"], r["g_entry"])
    lega[f"sup{'OK' if s else 'X'}/dem{'OK' if d else 'X'}"] += 1
    stata[state] += 1
    print(f"    {dt.datetime.utcfromtimestamp(r['cj_t'])} supOK={s} (ds={None if ds is None else round(ds,2)}) "
          f"demOK={d} state={state} dd={None if dd is None else round(dd,2)} R={r['g_R']}")
print(f"  resumo pernas: {dict(lega)} · estados: {dict(stata)}")
