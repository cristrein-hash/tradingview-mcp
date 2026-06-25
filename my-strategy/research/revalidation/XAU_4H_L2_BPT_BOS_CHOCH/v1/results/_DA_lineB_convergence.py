#!/usr/bin/env python3
"""LINHA B — fundo por CONVERGÊNCIA multi-fatorial (tudo RAW). Para os 123 fundos candidatos (causais), extrai do RAW
SVP gz: absorção(bubble SELL plot_6/8/10), demanda(Custom OB), NAS(pine_labels), CHoCH(SMC), aceitação-de-volume(session_vp
POC/VAL). + sweep/reclaim de OHLC. Mede outcome (SL=demanda−0.1ATR, let-run, custo 0.35R) POR NÍVEL DE CONVERGÊNCIA.
Hipótese: alta convergência = fundo real (net+), baixa = faca caindo (net−). Causal as-of-bar. Verified 2026-06-25."""
import json, gzip, bisect, datetime as dt
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
N = len(F); H = [r["high"] for r in F]; L = [r["low"] for r in F]; C = [r["close"] for r in F]; TS = [int(r["ts_epoch"]) for r in F]
ATR = [None] * N; trs = []
for i in range(1, N):
    trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    if i >= 14: ATR[i] = sum(trs[i - 14:i]) / 14
cand = json.load(open(V1 / "results/l2_bpt_lineB_distinct_bottoms.json"))
SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
def to_ep(t):
    t = float(t); return int(t / 1000) if t > 1e11 else int(t)
def pv(s):
    if s is None: return None
    s = str(s).replace(" ", "").replace(",", "").replace("−", "-").strip()
    m = 1.0
    if s[-1:] in ("K", "M", "B"): m = {"K": 1e3, "M": 1e6, "B": 1e9}[s[-1]]; s = s[:-1]
    try: return float(s) * m
    except Exception: return None
# RAW gz: 1 passada → por asof_t: sell, large, OB zones, NAS last text, SMC last text, POC, VAL
D = {}
with gzip.open(SVP, "rt") as fh:
    for line in fh:
        if '"ohlcv"' not in line: continue
        rec = json.loads(line); oh = rec.get("ohlcv"); last = oh[-1] if isinstance(oh, list) and oh else None
        if not isinstance(last, dict): continue
        at = to_ep(last.get("time"))
        if at is None or at in D: continue
        pb = rec.get("pine_boxes") or []
        ob = next((g for g in pb if "Custom OB" in str(g.get("name", ""))), {})
        zones = [(z["high"], z["low"]) for z in (ob.get("zones") or []) if z.get("high") is not None]
        bg = next((g for g in (rec.get("pine_shapes_bubbles") or []) if "Bubble" in str(g.get("name", ""))), {})
        a = bg.get("activations_per_plot") or {}
        sell = sum(pv(a.get(f"plot_{k}")) or 0 for k in (6, 8, 10)); large = pv(a.get("plot_10")) or 0
        def lastlabel(key):
            g = next((x for x in (rec.get("pine_labels") or []) if key in str(x.get("name", ""))), {})
            ls = g.get("labels") or []
            return ls[-1].get("text") if ls else None
        nas = lastlabel("NAS"); smc = lastlabel("Smart Money")
        vp = next((s.get("values", {}) for s in (rec.get("study_values") or []) if "Session Volume Profile" in str(s.get("name", ""))), {})
        sv = rec.get("session_vp", {})
        poc = val = None
        l3 = (sv.get("last3") or []) if isinstance(sv, dict) else []
        if l3 and isinstance(l3[-1], dict):
            v = l3[-1].get("v") or []
            if len(v) >= 4: poc, val = v[1], v[3]
        D[at] = dict(sell=sell, large=large, zones=zones, nas=nas, smc=smc, poc=poc, val=val)
DT = sorted(D)
print(f"asof_t no RAW gz = {len(DT)}")

def asof(et):
    k = bisect.bisect_right(DT, et) - 1
    return D[DT[k]] if k >= 0 else {}
def sell10(et):  # cluster SELL nas 10 barras <= et
    ts = [t for t in DT if t <= et][-10:]
    return sum(D[t]["sell"] for t in ts)

def feats(i):
    if not ATR[i]: return None
    et = TS[i]; entry = C[i]; d = asof(et)
    # demanda (SL + touched)
    below = [(hi, lo) for hi, lo in d.get("zones", []) if hi <= entry]
    if below:
        hi, lo = max(below, key=lambda z: z[0]); sl = lo - 0.1 * ATR[i]; demand_touched = (entry - hi) <= 0.5 * ATR[i]
    else:
        lo6 = min(L[max(0, i - 5):i + 1]); sl = lo6 - 0.1 * ATR[i]; demand_touched = False
    risk = entry - sl
    if risk <= 0: return None
    # convergência (6 vozes de qualidade, causais)
    absorb = (sell10(et) >= 3 or d.get("large", 0) >= 1)
    prior_low = min(L[max(0, i - 25):max(1, i - 5)]); swept = min(L[max(0, i - 5):i + 1]) < prior_low and C[i] > prior_low
    nas_long = str(d.get("nas")).upper() == "LONG"
    choch = "CHoCH" in str(d.get("smc") or "")
    svp_acc = (d.get("val") is not None and entry > d["val"])
    conv = sum([absorb, demand_touched, swept, nas_long, choch, svp_acc])
    # outcome let-run
    end = min(i + 120, N - 1)
    stopped = any(L[j] <= sl for j in range(i + 1, end + 1))
    lr = -1.0 if stopped else (C[end] - entry) / risk
    return dict(i=i, conv=conv, net=lr - 0.35, lr=lr, absorb=int(absorb), demand=int(demand_touched),
                swept=int(swept), nas=int(nas_long), choch=int(choch), svp=int(svp_acc), risk_atr=risk / ATR[i])

res = [r for i in cand if (r := feats(i))]
n = len(res)
print(f"fundos medidos = {n}\n")
print("=== outcome POR NÍVEL DE CONVERGÊNCIA (let-run, custo 0.35R) ===")
print(f"{'conv':>4} | {'n':>3} | {'WR':>4} | {'sumR':>7} | {'avgR':>6} | {'runners≥5':>9}")
for cv in range(7):
    g = [r for r in res if r["conv"] == cv]
    if not g: continue
    w = sum(1 for r in g if r["net"] > 0); s = sum(r["net"] for r in g); run = sum(1 for r in g if r["lr"] >= 5)
    print(f"{cv:>4} | {len(g):>3} | {100*w/len(g):>3.0f}% | {s:>+7.1f} | {s/len(g):>+6.2f} | {run:>9}")
hi = [r for r in res if r["conv"] >= 3]; lo = [r for r in res if r["conv"] <= 1]
print(f"\nCONV≥3: n={len(hi)} WR={100*sum(1 for r in hi if r['net']>0)/max(1,len(hi)):.0f}% sumR={sum(r['net'] for r in hi):+.1f}")
print(f"CONV≤1: n={len(lo)} WR={100*sum(1 for r in lo if r['net']>0)/max(1,len(lo)):.0f}% sumR={sum(r['net'] for r in lo):+.1f}")
print("\n=== cada voz isolada (WR | sumR quando ON) ===")
for v in ("absorb", "demand", "swept", "nas", "choch", "svp"):
    on = [r for r in res if r[v]]
    if on: print(f"  {v:>8} ON: n={len(on)} WR={100*sum(1 for r in on if r['net']>0)/len(on):.0f}% sumR={sum(r['net'] for r in on):+.1f}")
json.dump(res, open(V1 / "results/l2_bpt_lineB_convergence.json", "w"))
print("\nCalibração 276 (canon). Causal. Próximo: significância/sub-janela/beta-strip se conv≥X for net+.")
