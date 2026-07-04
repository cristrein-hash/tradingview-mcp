#!/usr/bin/env python3
"""MAPEAMENTO COMPLETO indicadores × MTF das 35 operações manuais do Cris (2026-07-04).
Mandato: contextualizar com NAS, Bubbles (nº/tamanhos), OB/demandas, SMC, Volume, em 15M + 30M + 1H
(estrutura e indicadores), e procurar PADRÕES POSITIVOS para filtro de entry — sem lookahead.
STATUS: EXPLORATORY_CALIBRATION (alvo = HINDSIGHT_TARGET_SET; lifts vs controles do universo).
SVP: indisponível no RAW da janela (blocos 5-8 não capturaram SVP) — declarado.
SMC: eventos sem direção no builder (bug conhecido) — usadas recência/contagem, declarado.
Fontes: primitives 15M oficiais + bubbles 15M · sandbox 30M/1H (builder canônico re-alvo, mapping
de bubbles auditado BUY-up% >> SELL-up%) · universo SELADO como controles (mesma janela)."""
import json, bisect, hashlib, statistics as st
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SBX = Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/mtf_sandbox")

# ---- trades + universo ----
AN = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
TR = sorted([{"n": r["n"], "t": r["t"], "entry": r["entry"], "utc": r["utc"], "regime": r["regime"]} for r in AN], key=lambda x: x["t"])
CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]
W0, W1 = TR[0]["t"] - 86400, TR[-1]["t"] + 86400
tr_ts = [t["t"] for t in TR]
CTRL = [r for r in U if W0 <= r["cj_t"] <= W1 and min(abs(r["cj_t"] - t) for t in tr_ts) > 24 * 900]
print(f"trades 35 · controles do universo na janela (>24 barras de distância): {len(CTRL)}")

# ---- carregar TFs ----
def load_tf(tag, prim_paths, bub_paths, bar_s):
    series = {}; nas = []; smc = []; zones = []
    for p in prim_paths:
        d = json.load(open(p))
        for b in d["series"]: series[b["t"]] = b
        nas += d["nas_events"]; smc += d["smc_events"]
        zs = d["zones"].values() if isinstance(d["zones"], dict) else d["zones"]
        zones += list(zs)
    bубs = []
    bubs = []
    for p in bub_paths:
        bubs += [json.loads(l) for l in open(p)]
    S = sorted(series.values(), key=lambda b: b["t"])
    return {"tag": tag, "bar_s": bar_s, "S": S, "ts": [b["t"] for b in S],
            "nas": sorted(nas, key=lambda e: e["t"]), "smc": sorted(smc, key=lambda e: e["t"]),
            "zones": zones, "bubs": sorted(bubs, key=lambda x: x["t"])}

TF15 = load_tf("15M", [HERE / "primitives" / f"XAUUSD_15m_replay_{k}.primitives.json" for k in
                       ("2025-05-25_to_2025-08-25", "2025-08-25_to_2025-11-25", "2025-11-25_to_2026-02-25", "2026-02-25_to_2026-05-25_rerun_customOBbaseline")],
               [HERE / "bubbles" / f"{k}.bubbles.jsonl" for k in
                ("2025-05-25_to_2025-08-25", "2025-08-25_to_2025-11-25", "2025-11-25_to_2026-02-25", "2026-02-25_to_2026-05-25_rerun_customOBbaseline")], 900)
TF30 = load_tf("30M", [SBX / "prim30" / f"XAUUSD_30m_replay_{k}.primitives.json" for k in
                       ("2025-05-25_to_2025-11-25", "2025-11-25_to_2026-05-25")],
               [SBX / "bub30" / f"{k}.bubbles.jsonl" for k in ("2025-05-25_to_2025-11-25", "2025-11-25_to_2026-05-25")], 1800)
TF60 = load_tf("1H", [SBX / "prim60" / f"XAUUSD_60m_replay_{k}.primitives.json" for k in
                      ("2025-05-25_to_2025-11-25", "2025-11-25_to_2026-05-25")],
               [SBX / "bub60" / f"{k}.bubbles.jsonl" for k in ("2025-05-25_to_2025-11-25", "2025-11-25_to_2026-05-25")], 3600)

def ctx(tf, t0, price):
    """contexto causal (<= t0) num TF: estrutura + NAS + SMC + zonas OB + bubbles + volume."""
    S, ts, bar_s = tf["S"], tf["ts"], tf["bar_s"]
    j = bisect.bisect_right(ts, t0) - 1
    if j < 100: return None
    b = S[j]; atr = b.get("atr") or 1.0
    o = {}
    o["rsi"] = b.get("rsi")
    e21 = b.get("ema21")
    o["ema21_dist"] = round((b["c"] - e21) / atr, 2) if e21 else None
    lo96 = min(x["l"] for x in S[max(0, j - 96):j + 1]); hi96 = max(x["h"] for x in S[max(0, j - 96):j + 1])
    o["box96"] = round((b["c"] - lo96) / ((hi96 - lo96) or atr), 3)
    # volume: percentil do vol médio das últimas 8 barras vs trailing 96
    vols = [x.get("v") or 0 for x in S[max(0, j - 96):j + 1]]
    v8 = sum(vols[-8:]) / 8
    o["vol8_pctile"] = round(100 * sum(1 for v in vols if v <= v8) / len(vols), 0)
    # NAS: última direção + recência + counts 24h
    na = [e for e in tf["nas"] if e["t"] <= t0]
    o["nas_last_dir"] = na[-1]["dir"] if na else None
    o["nas_last_bars"] = (t0 - na[-1]["t"]) // bar_s if na else None
    w24 = t0 - 24 * 3600
    o["nas24_long"] = sum(1 for e in na if e["t"] > w24 and e["dir"] == "LONG")
    o["nas24_short"] = sum(1 for e in na if e["t"] > w24 and e["dir"] == "SHORT")
    # SMC: recência CHoCH/BOS (sem direção — declarado)
    sm = [e for e in tf["smc"] if e["t"] <= t0]
    ch = [e for e in sm if "CHOCH" in str(e.get("text", "")).upper()]
    bo = [e for e in sm if "BOS" in str(e.get("text", "")).upper()]
    o["choch_last_bars"] = (t0 - ch[-1]["t"]) // bar_s if ch else None
    o["bos_last_bars"] = (t0 - bo[-1]["t"]) // bar_s if bo else None
    # OB zones ativas em t0
    dem = []; sup = []
    for z in tf["zones"]:
        if z["born_t"] <= t0 <= z.get("last_t", z["born_t"]):
            txt = str(z.get("text", "")).upper()
            (dem if "DEMAND" in txt else sup if "SUPPLY" in txt else []).append(z)
    o["n_demand_active"] = len(dem); o["n_supply_active"] = len(sup)
    below = [z for z in dem if z["high"] <= price]
    o["dist_demand_atr"] = round(min((price - z["high"]) / atr for z in below), 2) if below else None
    o["inside_demand"] = int(any(z["low"] <= price <= z["high"] for z in dem))
    sup_above = [z for z in sup if z["low"] >= price]
    o["dist_supply_atr"] = round(min((z["low"] - price) / atr for z in sup_above), 2) if sup_above else None
    # bubbles 24h por lado/tamanho + absorção (SELL M/L nas últimas 6h) + iniciativa (BUY M/L 6h)
    bb = [x for x in tf["bubs"] if (x.get("known_at") or x["t"]) <= t0 and x["t"] > w24]
    for side in ("BUY", "SELL"):
        for size in ("S", "M", "L"):
            o[f"bub_{side}_{size}"] = sum(1 for x in bb if x["side"] == side and x["size"] == size)
    w6 = t0 - 6 * 3600
    o["absorb_sellML_6h"] = sum(1 for x in bb if x["side"] == "SELL" and x["size"] in ("M", "L") and x["t"] > w6)
    o["initiative_buyML_6h"] = sum(1 for x in bb if x["side"] == "BUY" and x["size"] in ("M", "L") and x["t"] > w6)
    wgt = {"S": 1, "M": 2, "L": 3}
    o["bub_net24"] = sum(wgt[x["size"]] * (1 if x["side"] == "BUY" else -1) for x in bb)
    return o

def full_ctx(t0, price):
    return {"15M": ctx(TF15, t0, price), "30M": ctx(TF30, t0, price), "1H": ctx(TF60, t0, price)}

print("mapeando 35 trades…")
for tr in TR: tr["ctx"] = full_ctx(tr["t"], tr["entry"])
print(f"mapeando {len(CTRL)} controles…")
CT = []
for r in CTRL:
    c = full_ctx(r["cj_t"], r["g_entry"])
    if all(c.values()): CT.append(c)
print(f"controles com contexto completo: {len(CT)}")

# ---- lentes binárias pré-declaradas (LEDGER: 22 lentes × 3 TFs; zero re-tuning) ----
LENSES = {
    "nas_last_LONG": lambda o: o["nas_last_dir"] == "LONG",
    "nas_LONG_rec12": lambda o: o["nas_last_dir"] == "LONG" and (o["nas_last_bars"] or 999) <= 12,
    "nas24_long_ge2": lambda o: o["nas24_long"] >= 2,
    "nas24_short_zero": lambda o: o["nas24_short"] == 0,
    "choch_rec24": lambda o: (o["choch_last_bars"] or 999) <= 24,
    "bos_rec24": lambda o: (o["bos_last_bars"] or 999) <= 24,
    "inside_demand": lambda o: o["inside_demand"] == 1,
    "demand_near1atr": lambda o: o["inside_demand"] == 1 or (o["dist_demand_atr"] is not None and o["dist_demand_atr"] <= 1.0),
    "supply_far3atr": lambda o: o["dist_supply_atr"] is None or o["dist_supply_atr"] >= 3.0,
    "absorb_sellML": lambda o: o["absorb_sellML_6h"] >= 1,
    "initiative_buyML": lambda o: o["initiative_buyML_6h"] >= 1,
    "bubnet24_pos": lambda o: o["bub_net24"] > 0,
    "bub_sellL_ge1_24h": lambda o: o["bub_SELL_L"] >= 1,
    "bub_buyL_ge1_24h": lambda o: o["bub_BUY_L"] >= 1,
    "rsi_40_60": lambda o: o["rsi"] is not None and 40 <= o["rsi"] <= 60,
    "ema21_pull_le0.5": lambda o: o["ema21_dist"] is not None and -0.5 <= o["ema21_dist"] <= 0.5,
    "box96_medial": lambda o: 0.25 <= o["box96"] <= 0.75,
    "vol8_low_le40": lambda o: o["vol8_pctile"] <= 40,
    "vol8_high_ge70": lambda o: o["vol8_pctile"] >= 70,
}
def cov(objs, tfk, name):
    fn = LENSES[name]
    ok = [o for o in objs if o.get(tfk)]
    return sum(1 for o in ok if fn(o[tfk])) / max(1, len(ok))

print("\n" + "=" * 108)
print(f"{'LENTE':<22} | {'15M cris/ctrl lift':>22} | {'30M cris/ctrl lift':>22} | {'1H cris/ctrl lift':>22}")
print("-" * 108)
TRC = [{"15M": t["ctx"]["15M"], "30M": t["ctx"]["30M"], "1H": t["ctx"]["1H"]} for t in TR]
LIFTS = {}
for name in LENSES:
    row = []
    for tfk in ("15M", "30M", "1H"):
        a = cov(TRC, tfk, name); b = cov(CT, tfk, name)
        lift = a / b if b > 0 else float("inf")
        LIFTS[(name, tfk)] = (a, b, lift)
        row.append(f"{100*a:>4.0f}%/{100*b:>4.0f}% {lift:>4.1f}x")
    print(f"{name:<22} | {row[0]:>22} | {row[1]:>22} | {row[2]:>22}")

# medianas contínuas
print("\nMEDIANAS (cris vs ctrl):")
for tfk in ("15M", "30M", "1H"):
    for k in ("rsi", "ema21_dist", "box96", "vol8_pctile", "bub_net24", "nas24_long", "n_demand_active"):
        a = st.median([o[tfk][k] for o in TRC if o.get(tfk) and o[tfk][k] is not None])
        b = st.median([o[tfk][k] for o in CT if o.get(tfk) and o[tfk][k] is not None])
        print(f"  {tfk} {k:<16} cris={a}  ctrl={b}")

# top lifts com cobertura >= 60% nos 35
print("\nPADRÕES POSITIVOS (cobertura>=60% nos 35 E lift>=1.3):")
cands = [(n, tfk, *LIFTS[(n, tfk)]) for (n, tfk) in LIFTS if LIFTS[(n, tfk)][0] >= 0.6 and LIFTS[(n, tfk)][2] >= 1.3]
cands.sort(key=lambda x: -x[4])
for n, tfk, a, b, l in cands:
    print(f"  {tfk:<4} {n:<22} cris {100*a:.0f}% vs ctrl {100*b:.0f}% → lift {l:.2f}x")

# conjunções exploratórias (2-3 lentes dos tops; LEDGER declarado — sem otimização além desta lista)
def conj(objs, terms):
    ok = 0; tot = 0
    for o in objs:
        if not all(o.get(tfk) for _, tfk in [(LENSES[n], tfk) for n, tfk in terms]): continue
        tot += 1
        if all(LENSES[n](o[tfk]) for n, tfk in terms): ok += 1
    return ok / max(1, tot)
top = [(n, tfk) for n, tfk, *_ in cands[:6]]
print("\nCONJUNÇÕES EXPLORATÓRIAS (pares dos top-6; ledger integral impresso):")
best = []
for i in range(len(top)):
    for j in range(i + 1, len(top)):
        a = conj(TRC, [top[i], top[j]]); b = conj(CT, [top[i], top[j]])
        if a >= 0.5:
            best.append((f"{top[i][1]}:{top[i][0]} & {top[j][1]}:{top[j][0]}", a, b, a / b if b else float("inf")))
best.sort(key=lambda x: -x[3])
for nm, a, b, l in best[:10]:
    print(f"  {nm:<58} cris {100*a:.0f}% ctrl {100*b:.0f}% lift {l:.2f}x")

json.dump({"trades": TR, "n_controls": len(CT),
           "lifts": {f"{n}|{tf}": LIFTS[(n, tf)] for (n, tf) in LIFTS},
           "top_patterns": [(n, tfk, a, b, l) for n, tfk, a, b, l in cands],
           "conjunctions": best[:15],
           "note": "EXPLORATORY_CALIBRATION sobre HINDSIGHT_TARGET_SET; SVP indisponível; SMC sem direção"},
          open(HERE / "results" / "cris_trades_mtf_indicator_map_20260704.json", "w"), indent=1, ensure_ascii=False, default=str)
print("\nOK → results/cris_trades_mtf_indicator_map_20260704.json")
