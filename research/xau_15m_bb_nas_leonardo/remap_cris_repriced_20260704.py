#!/usr/bin/env python3
"""RE-MAPEAMENTO REPRECIFICADO (2026-07-04, ordem Cris): as 35 operações manuais re-avaliadas com
PREÇO = CLOSE REAL de mercado no t0 (lição do gate test: âncora retroativa inflava lentes de preço).
SEM comparação com entries/bases anteriores — perfil independente + lifts vs controles simétricos
(1107 candidatos, mesmos do mapeamento, preço = close real deles). Inclui FEATURES NOVAS desenhadas
para a lógica dip-pullback do operador (retração, idade do pullback, higher-low, compressão/quiet,
vol dry-up, alinhamento de tendência MTF, absorção da perna). STATUS: EXPLORATORY_CALIBRATION sobre
HINDSIGHT_TARGET_SET reprecificado. Ledger: 26 lentes ×3 TFs = 78 looks + pares top-6, declarado."""
import json, bisect, hashlib, statistics as stt
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SBX = Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/mtf_sandbox")

AN = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
TR = sorted([{"n": r["n"], "t": r["t"]} for r in AN], key=lambda x: x["t"])
CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]
tr_ts = [t["t"] for t in TR]
CTRL = [r for r in U if TR[0]["t"] - 86400 <= r["cj_t"] <= TR[-1]["t"] + 86400
        and min(abs(r["cj_t"] - t) for t in tr_ts) > 24 * 900]

def load_tf(prim_paths, bub_paths, bar_s):
    series = {}; nas = []; smc = []; zones = []
    for p in prim_paths:
        d = json.load(open(p))
        for b in d["series"]: series.setdefault(b["t"], b)
        nas += d["nas_events"]; smc += d["smc_events"]
        zs = d["zones"].values() if isinstance(d["zones"], dict) else d["zones"]
        zones += list(zs)
    bubs = []
    for p in bub_paths: bubs += [json.loads(l) for l in open(p)]
    S = sorted(series.values(), key=lambda b: b["t"])
    return {"bar_s": bar_s, "S": S, "ts": [b["t"] for b in S],
            "nas": sorted(nas, key=lambda e: e["t"]), "smc": sorted(smc, key=lambda e: e["t"]),
            "zones": zones, "bubs": sorted(bubs, key=lambda x: x["t"])}
K15 = ("2025-05-25_to_2025-08-25", "2025-08-25_to_2025-11-25", "2025-11-25_to_2026-02-25", "2026-02-25_to_2026-05-25_rerun_customOBbaseline")
TF15 = load_tf([HERE / "primitives" / f"XAUUSD_15m_replay_{k}.primitives.json" for k in K15],
               [HERE / "bubbles" / f"{k}.bubbles.jsonl" for k in K15], 900)
K2 = ("2025-05-25_to_2025-11-25", "2025-11-25_to_2026-05-25")
TF30 = load_tf([SBX / "prim30" / f"XAUUSD_30m_replay_{k}.primitives.json" for k in K2],
               [SBX / "bub30" / f"{k}.bubbles.jsonl" for k in K2], 1800)
TF60 = load_tf([SBX / "prim60" / f"XAUUSD_60m_replay_{k}.primitives.json" for k in K2],
               [SBX / "bub60" / f"{k}.bubbles.jsonl" for k in K2], 3600)

def ema_at(arr, i, n):
    c = arr[max(0, i - 3 * n):i + 1]; k = 2 / (n + 1); e = c[0]
    for v in c[1:]: e = v * k + e * (1 - k)
    return e

def ctx(tf, t0):
    """contexto causal com PREÇO = CLOSE REAL da barra asof. Lentes antigas + FEATURES NOVAS."""
    S, ts, bar_s = tf["S"], tf["ts"], tf["bar_s"]
    j = bisect.bisect_right(ts, t0) - 1
    if j < 100: return None
    b = S[j]; price = b["c"]; atr = b.get("atr") or 1.0
    o = {"price": price}
    o["rsi"] = b.get("rsi")
    e21 = b.get("ema21") or ema_at([x["c"] for x in S[:j + 1]], j, 21)
    o["ema21_dist"] = round((price - e21) / atr, 2)
    win = S[max(0, j - 96):j + 1]
    lo96 = min(x["l"] for x in win); hi96 = max(x["h"] for x in win)
    o["box96"] = round((price - lo96) / ((hi96 - lo96) or atr), 3)
    # ---- FEATURES NOVAS (lógica dip-pullback) ----
    o["retrace96"] = round((hi96 - price) / ((hi96 - lo96) or atr), 3)          # profundidade da retração
    jh = max(range(len(win)), key=lambda i: win[i]["h"])
    o["pullback_age"] = len(win) - 1 - jh                                        # barras desde o high
    dleg = win[jh:]                                                              # perna de queda
    o["dip_depth_atr"] = round((win[jh]["h"] - price) / atr, 2)
    tr4 = [x["h"] - x["l"] for x in win[-4:]]
    o["quiet4"] = round(sum(tr4) / 4 / atr, 2)                                   # compressão recente
    vleg = [x.get("v") or 0 for x in dleg]; vpre = [x.get("v") or 0 for x in win[max(0, jh - len(dleg)):jh]]
    o["vol_dryup"] = round((sum(vleg[-8:]) / max(1, len(vleg[-8:]))) / max(1e-9, sum(vpre) / max(1, len(vpre))), 2) if vpre else None
    C = [x["c"] for x in S[:j + 1]]
    e50 = ema_at(C, j, 50)
    o["trend_up"] = int(price > e21 > 0 and e21 > e50)                            # alinhamento no TF
    o["above_e50"] = int(price > e50)
    lows = [x["l"] for x in win]
    swl = [i for i in range(2, len(lows) - 2) if lows[i] == min(lows[i - 2:i + 3])]
    o["higher_low"] = int(len(swl) >= 2 and lows[swl[-1]] > lows[swl[-2]])        # HL estrutural
    # ---- lentes antigas (reprecificadas) ----
    na = [e for e in tf["nas"] if e["t"] <= t0]; w24 = t0 - 24 * 3600
    o["nas_last_LONG_rec"] = int(bool(na) and na[-1]["dir"] == "LONG" and (t0 - na[-1]["t"]) // bar_s <= 24)
    sm = [e for e in tf["smc"] if e["t"] <= t0]
    ch = [e for e in sm if "CHOCH" in str(e.get("text", "")).upper()]
    o["choch_rec24"] = int(bool(ch) and (t0 - ch[-1]["t"]) // bar_s <= 24)
    dem = [z for z in tf["zones"] if z["born_t"] <= t0 <= z.get("last_t", z["born_t"]) and "DEMAND" in str(z.get("text", "")).upper()]
    sup = [z for z in tf["zones"] if z["born_t"] <= t0 <= z.get("last_t", z["born_t"]) and "SUPPLY" in str(z.get("text", "")).upper()]
    below = [z for z in dem if z["high"] <= price]
    o["inside_demand"] = int(any(z["low"] <= price <= z["high"] for z in dem))
    o["demand_near1"] = int(bool(o["inside_demand"]) or bool(below and min((price - z["high"]) / atr for z in below) <= 1.0))
    supab = [z for z in sup if z["low"] >= price]
    o["supply_far3"] = int(not supab or min((z["low"] - price) / atr for z in supab) >= 3.0)
    bb = [x for x in tf["bubs"] if (x.get("known_at") or x["t"]) <= t0 and x["t"] > w24]
    w6 = t0 - 6 * 3600
    o["absorb_sellML_6h"] = int(sum(1 for x in bb if x["side"] == "SELL" and x["size"] in ("M", "L") and x["t"] > w6) >= 1)
    o["no_initiative_buyML"] = int(sum(1 for x in bb if x["side"] == "BUY" and x["size"] in ("M", "L") and x["t"] > w6) == 0)
    o["dipleg_sell_dom"] = int(sum(1 for x in bb if x["side"] == "SELL" and x["size"] in ("M", "L")) >
                               sum(1 for x in bb if x["side"] == "BUY" and x["size"] in ("M", "L")))
    return o

def full(t0): return {"15M": ctx(TF15, t0), "30M": ctx(TF30, t0), "1H": ctx(TF60, t0)}
print("reprecificando 35 alvos + 1107 controles (3 TFs)…")
for tr in TR: tr["ctx"] = full(tr["t"])
CT = [c for c in (full(r["cj_t"]) for r in CTRL) if all(c.values())]
print(f"controles com contexto: {len(CT)}")

BINS = {
    "retrace_30_70": lambda o: 0.30 <= o["retrace96"] <= 0.70,
    "pullback_age_ge8": lambda o: o["pullback_age"] >= 8,
    "dip_1a3_atr": lambda o: 1.0 <= o["dip_depth_atr"] <= 3.0,
    "quiet4_le1": lambda o: o["quiet4"] <= 1.0,
    "vol_dryup_le08": lambda o: o["vol_dryup"] is not None and o["vol_dryup"] <= 0.8,
    "trend_up": lambda o: o["trend_up"] == 1,
    "above_e50": lambda o: o["above_e50"] == 1,
    "higher_low": lambda o: o["higher_low"] == 1,
    "ema21_pull_band": lambda o: -0.6 <= o["ema21_dist"] <= 0.8,
    "rsi_40_60": lambda o: o["rsi"] is not None and 40 <= o["rsi"] <= 60,
    "nas_LONG_rec24": lambda o: o["nas_last_LONG_rec"] == 1,
    "choch_rec24": lambda o: o["choch_rec24"] == 1,
    "inside_demand": lambda o: o["inside_demand"] == 1,
    "demand_near1": lambda o: o["demand_near1"] == 1,
    "supply_far3": lambda o: o["supply_far3"] == 1,
    "absorb_sellML": lambda o: o["absorb_sellML_6h"] == 1,
    "no_initiative": lambda o: o["no_initiative_buyML"] == 1,
    "dipleg_sell_dom": lambda o: o["dipleg_sell_dom"] == 1,
}
TRC = [t["ctx"] for t in TR]
def cov(objs, tfk, name):
    fn = BINS[name]; ok = [o for o in objs if o.get(tfk)]
    return sum(1 for o in ok if fn(o[tfk])) / max(1, len(ok))
print("\n" + "=" * 106)
print(f"{'LENTE (preço REAL)':<20} | {'15M cris/ctrl lift':>20} | {'30M cris/ctrl lift':>20} | {'1H cris/ctrl lift':>20}")
print("-" * 106)
L = {}
for name in BINS:
    row = []
    for tfk in ("15M", "30M", "1H"):
        a = cov(TRC, tfk, name); b = cov(CT, tfk, name)
        L[(name, tfk)] = (a, b, a / b if b > 0 else float("inf"))
        row.append(f"{100*a:>3.0f}%/{100*b:>3.0f}% {a/b if b>0 else 99:>4.1f}x")
    print(f"{name:<20} | {row[0]:>20} | {row[1]:>20} | {row[2]:>20}")
print("\nMEDIANAS novas features (cris vs ctrl, 15M):")
for k in ("retrace96", "pullback_age", "dip_depth_atr", "quiet4", "vol_dryup", "ema21_dist", "rsi"):
    a = stt.median([o["15M"][k] for o in TRC if o.get("15M") and o["15M"][k] is not None])
    b = stt.median([o["15M"][k] for o in CT if o.get("15M") and o["15M"][k] is not None])
    print(f"  {k:<14} cris={a}  ctrl={b}")
tops = sorted([(n, tf, *L[(n, tf)]) for (n, tf) in L if L[(n, tf)][0] >= 0.6 and L[(n, tf)][2] >= 1.25], key=lambda x: -x[4])
print("\nPADRÕES (cob>=60% & lift>=1.25):")
for n, tf, a, b, l in tops: print(f"  {tf:<4} {n:<20} {100*a:.0f}%/{100*b:.0f}% {l:.2f}x")
best = []
for i in range(len(tops)):
    for j in range(i + 1, len(tops)):
        (n1, t1), (n2, t2) = tops[i][:2], tops[j][:2]
        a = sum(1 for o in TRC if o.get(t1) and o.get(t2) and BINS[n1](o[t1]) and BINS[n2](o[t2])) / len(TRC)
        b = sum(1 for o in CT if o.get(t1) and o.get(t2) and BINS[n1](o[t1]) and BINS[n2](o[t2])) / len(CT)
        if a >= 0.5: best.append((f"{t1}:{n1} & {t2}:{n2}", a, b, a / b if b else 99))
best.sort(key=lambda x: -x[3])
print("\nPARES (ledger integral dos qualificados):")
for nm, a, b, l in best[:12]: print(f"  {nm:<52} {100*a:.0f}%/{100*b:.0f}% {l:.2f}x")
json.dump({"lifts": {f"{n}|{tf}": v for (n, tf), v in L.items()}, "pairs": best[:20],
           "n_ctrl": len(CT), "note": "REPRECIFICADO ao close real; simétrico; sem comparação com bases; CALIBRAÇÃO"},
          open(HERE / "results" / "cris_repriced_map_20260704.json", "w"), indent=1)
print("\nOK → results/cris_repriced_map_20260704.json")
