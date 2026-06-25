#!/usr/bin/env python3
"""Aplica os loser-cuts da L2/BPT, UM A UM, sobre os 34 trades aprovados da L1 EMA21. Features L2 computadas no RAW nos
bars de entrada L1. Restrição DURA: usável só se WINNERS cortados = 0. Reporta por filtro: flagged, losers, winners,
runners cortados, WR/sumR resultantes. Causal as-of. Verified 2026-06-25."""
import json, gzip, bisect, datetime as dt
from pathlib import Path
V1 = Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1")
L1DIR = Path(__file__).parent
appr = json.load(open(L1DIR / "l1_approved34.json"))
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
N = len(F); H = [r["high"] for r in F]; L = [r["low"] for r in F]; C = [r["close"] for r in F]; TS = [int(r["ts_epoch"]) for r in F]; RSI = [r.get("rsi") for r in F]
ATR = [None] * N; trs = []
for i in range(1, N):
    trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    if i >= 14: ATR[i] = sum(trs[i - 14:i]) / 14
# regime v3 asof
REG = V1 / "../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl"
def toep(s):
    try: return int(dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp())
    except Exception: return int(dt.datetime.strptime(str(s)[:10], "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
rb = [json.loads(l) for l in open(REG) if json.loads(l).get("ts")]
for r in rb: r["_e"] = toep(r["ts"])
rb.sort(key=lambda r: r["_e"]); rbt = [r["_e"] for r in rb]
def reg_asof(et): k = bisect.bisect_right(rbt, et) - 1; return rb[k].get("raw_state") if k >= 0 else None
def l1_epoch(ts): return int(dt.datetime.fromisoformat(ts).replace(tzinfo=dt.timezone.utc).timestamp())
# map L1 ts -> bar_idx (nearest)
def bar_of(et):
    k = bisect.bisect_left(TS, et)
    cands = [j for j in (k - 1, k, k + 1) if 0 <= j < N]
    return min(cands, key=lambda j: abs(TS[j] - et)) if cands else None
# RAW gz para os bars L1 (bubbles/OB/svp)
SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
def to_ep(t): t = float(t); return int(t / 1000) if t > 1e11 else int(t)
def pv(s):
    if s is None: return 0
    s = str(s).replace(" ", "").replace(",", "").strip(); m = 1.0
    if s[-1:] in ("K", "M", "B"): m = {"K": 1e3, "M": 1e6, "B": 1e9}[s[-1]]; s = s[:-1]
    try: return float(s) * m
    except Exception: return 0
D = {}
with gzip.open(SVP, "rt") as fh:
    for line in fh:
        if '"ohlcv"' not in line: continue
        rec = json.loads(line); oh = rec.get("ohlcv"); last = oh[-1] if isinstance(oh, list) and oh else None
        if not isinstance(last, dict): continue
        at = to_ep(last.get("time"))
        if at is None or at in D: continue
        g = next((x for x in (rec.get("pine_boxes") or []) if "Custom OB" in str(x.get("name", ""))), {})
        zones = [(z["high"], z["low"]) for z in (g.get("zones") or []) if z.get("high") is not None]
        bg = next((x for x in (rec.get("pine_shapes_bubbles") or []) if "Bubble" in str(x.get("name", ""))), {})
        a = bg.get("activations_per_plot") or {}
        sv = rec.get("session_vp", {}); l3 = (sv.get("last3") or []) if isinstance(sv, dict) else []; val = None
        if l3 and isinstance(l3[-1], dict):
            v = l3[-1].get("v") or []
            if len(v) >= 4: val = v[3]
        D[at] = dict(zones=zones, sell=sum(pv(a.get(f"plot_{k}")) for k in (6, 8, 10)), large=pv(a.get("plot_10")), val=val)
DT = sorted(D)
def asof(et): k = bisect.bisect_right(DT, et) - 1; return D[DT[k]] if k >= 0 else {}
def sell10(et): return sum(D[t]["sell"] for t in [t for t in DT if t <= et][-10:])

# features L2 por trade L1
T = []
for a in appr:
    et = l1_epoch(a["ts"]); i = bar_of(et)
    if i is None or not ATR[i]: continue
    entry = C[i]; d = asof(TS[i]); zones = d.get("zones", [])
    below = [(hi, lo) for hi, lo in zones if hi <= entry]; above = [(hi, lo) for hi, lo in zones if lo >= entry]
    drop20 = (C[i - 20] - C[i]) / ATR[i] if i >= 20 else 0
    v3 = reg_asof(TS[i])
    # vozes conv
    near_dem = bool(below) and (entry - max(below, key=lambda z: z[0])[0]) <= 0.5 * ATR[i]
    swept = i >= 25 and min(L[max(0, i - 5):i + 1]) < min(L[max(0, i - 25):max(1, i - 5)]) and C[i] > min(L[max(0, i - 25):max(1, i - 5)])
    svp_acc = d.get("val") is not None and entry > d["val"]
    absorb = sell10(TS[i]) >= 2 or d.get("large", 0) >= 1
    conv = sum([absorb, (v3 != "BEAR"), svp_acc, swept])
    T.append(dict(win=a["win"], R=a["R"], mfe=a["mfe"], runner=a["mfe"] >= 5, rsi=RSI[i],
                  regime_BEAR=(v3 == "BEAR"), rsi_ge70=(RSI[i] is not None and RSI[i] >= 70),
                  conv_le1=(conv <= 1), not_clean=bool(above), svp_below=(not svp_acc),
                  no_demand=(not below), bearleg_proxy=(v3 == "BEAR" and drop20 >= 2)))
n = len(T); W = sum(1 for t in T if t["win"]); base = sum(t["R"] for t in T)
print(f"L1 aprovado: n={n} winners={W} losers={n-W} runners={sum(1 for t in T if t['runner'])} | WR={100*W/n:.0f}% sumR={base:+.1f}\n")
print("=== loser-cuts L2 aplicados UM A UM (cortar = remover flagged). RESTRIÇÃO: winners cortados deve ser 0 ===")
print(f"{'filtro':>14} | {'flag':>4} | {'losers_cut':>10} | {'WIN_cut':>7} | {'run_cut':>7} | {'WR após':>7} | {'sumR após':>9} | usável?")
FILT = ["regime_BEAR", "rsi_ge70", "conv_le1", "not_clean", "svp_below", "no_demand", "bearleg_proxy"]
for f in FILT:
    cut = [t for t in T if t[f]]; kept = [t for t in T if not t[f]]
    lc = sum(1 for t in cut if not t["win"]); wc = sum(1 for t in cut if t["win"]); rc = sum(1 for t in cut if t["runner"])
    if kept:
        wr = 100 * sum(1 for t in kept if t["win"]) / len(kept); sr = sum(t["R"] for t in kept)
    else: wr = sr = 0
    ok = "✅" if (wc == 0 and lc > 0) else ("—" if lc == 0 else "❌(corta winner)")
    print(f"{f:>14} | {len(cut):>4} | {lc:>10} | {wc:>7} | {rc:>7} | {wr:>6.0f}% | {sr:>+9.1f} | {ok}")
print("\nRestrição dura: PROIBIDO perder winner. Causal. n=34 (poder baixo).")
