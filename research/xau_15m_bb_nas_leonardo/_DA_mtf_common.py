#!/usr/bin/env python3
"""DA MTF 2026-07-04 — módulo comum: transcrição fiel do pipeline de
map_cris_trades_indicators_20260704.py, parametrizada para os ataques:
  • zone_mode: "orig" (born_t<=t0<=last_t — condição do mapa) vs
               "borncausal" (born_t<=t0 apenas — sem usar last_t, que só é conhecido depois)
  • shift_bars: desloca o t0 dos CONTROLES em +N barras de 15M (preço = close 15M na barra deslocada)
Fidelidade validada por _DA_mtf_attack4_repro.py (zone_mode=orig, shift=0 deve reproduzir
results/cris_trades_mtf_indicator_map_20260704.json byte-a-número).
PROIBIDO commit/push. Não toca chart/RAW/produção (leitura apenas)."""
import json, bisect, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SBX = Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/mtf_sandbox")
SCRATCH = SBX.parent / "da_mtf_cache"
SCRATCH.mkdir(exist_ok=True)

AN = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
TR = sorted([{"n": r["n"], "t": r["t"], "entry": r["entry"], "utc": r["utc"], "regime": r["regime"]} for r in AN], key=lambda x: x["t"])
CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]
W0, W1 = TR[0]["t"] - 86400, TR[-1]["t"] + 86400
tr_ts = [t["t"] for t in TR]
CTRL = [r for r in U if W0 <= r["cj_t"] <= W1 and min(abs(r["cj_t"] - t) for t in tr_ts) > 24 * 900]


def load_tf(tag, prim_paths, bub_paths, bar_s):
    series = {}; nas = []; smc = []; zones = []
    for p in prim_paths:
        d = json.load(open(p))
        for b in d["series"]: series[b["t"]] = b
        nas += d["nas_events"]; smc += d["smc_events"]
        zs = d["zones"].values() if isinstance(d["zones"], dict) else d["zones"]
        zones += list(zs)
    bubs = []
    for p in bub_paths:
        bubs += [json.loads(l) for l in open(p)]
    S = sorted(series.values(), key=lambda b: b["t"])
    bubs = sorted(bubs, key=lambda x: x["t"])
    # otimização exata: slice por t com margem = max lag (t - known_at); filtro original dentro do slice
    lag = max([x["t"] - (x.get("known_at") or x["t"]) for x in bubs] + [0])
    return {"tag": tag, "bar_s": bar_s, "S": S, "ts": [b["t"] for b in S],
            "nas": sorted(nas, key=lambda e: e["t"]), "smc": sorted(smc, key=lambda e: e["t"]),
            "zones": zones, "bubs": bubs, "bub_ts": [x["t"] for x in bubs], "bub_lag": lag}


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


def ctx(tf, t0, price, zone_mode="orig"):
    """transcrição fiel de ctx() do mapa; único delta paramétrico = atividade da zona."""
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
    vols = [x.get("v") or 0 for x in S[max(0, j - 96):j + 1]]
    v8 = sum(vols[-8:]) / 8
    o["vol8_pctile"] = round(100 * sum(1 for v in vols if v <= v8) / len(vols), 0)
    na = [e for e in tf["nas"] if e["t"] <= t0]
    o["nas_last_dir"] = na[-1]["dir"] if na else None
    o["nas_last_bars"] = (t0 - na[-1]["t"]) // bar_s if na else None
    w24 = t0 - 24 * 3600
    o["nas24_long"] = sum(1 for e in na if e["t"] > w24 and e["dir"] == "LONG")
    o["nas24_short"] = sum(1 for e in na if e["t"] > w24 and e["dir"] == "SHORT")
    sm = [e for e in tf["smc"] if e["t"] <= t0]
    ch = [e for e in sm if "CHOCH" in str(e.get("text", "")).upper()]
    bo = [e for e in sm if "BOS" in str(e.get("text", "")).upper()]
    o["choch_last_bars"] = (t0 - ch[-1]["t"]) // bar_s if ch else None
    o["bos_last_bars"] = (t0 - bo[-1]["t"]) // bar_s if bo else None
    dem = []; sup = []
    for z in tf["zones"]:
        if zone_mode == "orig":
            active = z["born_t"] <= t0 <= z.get("last_t", z["born_t"])
        elif zone_mode == "borncausal":
            active = z["born_t"] <= t0
        else:
            raise ValueError(zone_mode)
        if active:
            txt = str(z.get("text", "")).upper()
            (dem if "DEMAND" in txt else sup if "SUPPLY" in txt else []).append(z)
    o["n_demand_active"] = len(dem); o["n_supply_active"] = len(sup)
    below = [z for z in dem if z["high"] <= price]
    o["dist_demand_atr"] = round(min((price - z["high"]) / atr for z in below), 2) if below else None
    o["inside_demand"] = int(any(z["low"] <= price <= z["high"] for z in dem))
    sup_above = [z for z in sup if z["low"] >= price]
    o["dist_supply_atr"] = round(min((z["low"] - price) / atr for z in sup_above), 2) if sup_above else None
    # bubbles: slice por t via bisect com margem bub_lag + filtro ORIGINAL dentro do slice (equivalência exata)
    i0 = bisect.bisect_right(tf["bub_ts"], w24); i1 = bisect.bisect_right(tf["bub_ts"], t0 + tf["bub_lag"])
    bb = [x for x in tf["bubs"][i0:i1] if (x.get("known_at") or x["t"]) <= t0 and x["t"] > w24]
    for side in ("BUY", "SELL"):
        for size in ("S", "M", "L"):
            o[f"bub_{side}_{size}"] = sum(1 for x in bb if x["side"] == side and x["size"] == size)
    w6 = t0 - 6 * 3600
    o["absorb_sellML_6h"] = sum(1 for x in bb if x["side"] == "SELL" and x["size"] in ("M", "L") and x["t"] > w6)
    o["initiative_buyML_6h"] = sum(1 for x in bb if x["side"] == "BUY" and x["size"] in ("M", "L") and x["t"] > w6)
    wgt = {"S": 1, "M": 2, "L": 3}
    o["bub_net24"] = sum(wgt[x["size"]] * (1 if x["side"] == "BUY" else -1) for x in bb)
    return o


def full_ctx(t0, price, zone_mode="orig"):
    return {"15M": ctx(TF15, t0, price, zone_mode), "30M": ctx(TF30, t0, price, zone_mode), "1H": ctx(TF60, t0, price, zone_mode)}


def close15_at(t0):
    j = bisect.bisect_right(TF15["ts"], t0) - 1
    return (TF15["S"][j]["c"], TF15["ts"][j]) if j >= 0 else (None, None)


def trades_ctx(zone_mode="orig"):
    return [full_ctx(t["t"], t["entry"], zone_mode) for t in TR]


def controls_ctx(zone_mode="orig", shift_bars=0, price_mode="g_entry"):
    """price_mode: g_entry (original, só shift=0) | close15 (close da barra 15M em t0+shift)."""
    out = []
    for r in CTRL:
        t0 = r["cj_t"] + shift_bars * 900
        if price_mode == "g_entry":
            price = r["g_entry"]
        else:
            price, tb = close15_at(t0)
            if price is None or tb is None or t0 - tb > 4 * 900:  # barra 15M inexistente perto do t deslocado
                continue
        c = full_ctx(t0, price, zone_mode)
        if all(c.values()):
            c["_cj_t"] = r["cj_t"]
            out.append(c)
    return out


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


def conj(objs, terms):
    ok = 0; tot = 0
    for o in objs:
        if not all(o.get(tfk) for _, tfk in terms): continue
        tot += 1
        if all(LENSES[n](o[tfk]) for n, tfk in terms): ok += 1
    return ok / max(1, tot)


CHAMPION = [("supply_far3atr", "15M"), ("demand_near1atr", "1H")]


def pair_lift(trc, ct, terms=CHAMPION):
    a = conj(trc, terms); b = conj(ct, terms)
    return a, b, (a / b if b > 0 else float("inf"))


def pipeline(trc, ct):
    """réplica integral da seleção do mapa: lentes → cands (cov>=0.6, lift>=1.3) → top-6 → pares cov>=0.5."""
    lifts = {}
    for name in LENSES:
        for tfk in ("15M", "30M", "1H"):
            a = cov(trc, tfk, name); b = cov(ct, tfk, name)
            lifts[(name, tfk)] = (a, b, a / b if b > 0 else float("inf"))
    cands = [(n, tfk, *lifts[(n, tfk)]) for (n, tfk) in lifts if lifts[(n, tfk)][0] >= 0.6 and lifts[(n, tfk)][2] >= 1.3]
    cands.sort(key=lambda x: -x[4])
    top = [(n, tfk) for n, tfk, *_ in cands[:6]]
    best = []
    for i in range(len(top)):
        for j in range(i + 1, len(top)):
            a = conj(trc, [top[i], top[j]]); b = conj(ct, [top[i], top[j]])
            if a >= 0.5:
                best.append((f"{top[i][1]}:{top[i][0]} & {top[j][1]}:{top[j][0]}", a, b, a / b if b else float("inf")))
    best.sort(key=lambda x: -x[3])
    return lifts, cands, best
