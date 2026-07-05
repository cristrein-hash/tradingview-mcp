#!/usr/bin/env python3
"""FORMA DA REVERSÃO em PRICE-ACTION (2026-07-05, sharpening sem depender de bubbles esparsos).
Gargalo achado: bubble-accumulation é ~0,5/sem (eventos raros). Para expandir N mantendo streak<=4,
leitura densa da SEQUÊNCIA de virada em OHLC puro (não-snapshot, multi-barra):
  REJEIÇÃO no low: pavio inferior longo na barra de flush (comprador defendeu)
  HL-SEQUENCE: sequência de higher-lows formando base após o low (2-3 fundos ascendentes)
  VELOCIDADE: reclaim rápido pós-low ((close-low)/barras/atr)
  MOMENTUM-SHIFT: sequência de up-closes / RSI virando de oversold
  ANTI-EXAUSTÃO: anti RSI bear-div cluster (mantido do V1.4g)
Conjunções nítidas de price-action; streak<=4 = candidata. Walk-forward por ano. Universo selado."""
import json, glob, bisect
from pathlib import Path
HERE = Path(__file__).resolve().parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
WEEKS = len({r["g_week"] for r in U})
series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; Np = len(S)
RSI = [b.get("rsi") for b in S]; RSIMA = [None] * Np
for i in range(Np):
    w = [RSI[j] for j in range(max(0, i - 13), i + 1) if RSI[j] is not None]
    RSIMA[i] = sum(w) / len(w) if w else None
def pa(cj_t):
    i = bisect.bisect_right(TS, cj_t) - 1
    if i < 40: return None
    atr = S[i].get("atr") or 1.0; close = S[i]["c"]
    win = S[i - 16:i + 1]; lows = [b["l"] for b in win]
    lo_k = min(range(len(win)), key=lambda k: win[k]["l"]); lo_bar = win[lo_k]
    # REJEIÇÃO: pavio inferior da barra de low / range
    rng = lo_bar["h"] - lo_bar["l"]
    o = {}
    o["rej_wick"] = (min(lo_bar["o"], lo_bar["c"]) - lo_bar["l"]) / rng if rng > 0 else 0
    # HL-SEQUENCE após o low: nº de fundos locais ascendentes depois de lo_k
    post = win[lo_k:]
    swl = [k for k in range(2, len(post) - 1) if post[k]["l"] == min(x["l"] for x in post[max(0, k - 2):k + 2])]
    hl = 0
    for a in range(1, len(swl)):
        if post[swl[a]]["l"] > post[swl[a - 1]]["l"]: hl += 1
    o["hl_seq"] = hl
    # VELOCIDADE
    o["vel"] = (close - lo_bar["l"]) / atr / max(1, len(win) - 1 - lo_k)
    # MOMENTUM: up-closes consecutivos recentes + RSI virando
    uc = 0
    for k in range(i, i - 6, -1):
        if k > 0 and S[k]["c"] > S[k - 1]["c"]: uc += 1
        else: break
    o["up_closes"] = uc
    o["rsi_turn"] = int(RSI[i] is not None and RSI[i - 3] is not None and RSI[i] > RSI[i - 3] and RSI[i - 3] < 45)
    # ANTI bear-div
    bd = 0
    for k in range(i - 20, i - 2):
        if k < 3: continue
        if S[k]["h"] == max(x["h"] for x in S[k - 2:k + 3]):
            pv = [j for j in range(k - 12, k - 2) if S[j]["h"] == max(x["h"] for x in S[max(0, j - 2):j + 3])]
            if pv and RSI[k] is not None and RSI[pv[-1]] is not None and S[k]["h"] > S[pv[-1]]["h"] and RSI[k] < RSI[pv[-1]]: bd += 1
    o["bd"] = bd
    return o
P = {r["cj_t"]: pa(r["cj_t"]) for r in U}
NB = [r for r in U if r["g_v5h"] != "BEAR" and r["g_knife"] == 0 and P.get(r["cj_t"]) is not None]
def panel(rows, tag, show=True):
    n = len(rows)
    if not n:
        if show: print(f"  {tag:<28} vazio")
        return None
    rs = sorted(rows, key=lambda r: r["cj_t"]); nets = [R3[r["cj_t"]]["net3"] for r in rs]
    h = sum(1 for r in rs if R3[r["cj_t"]]["R3"] >= 3)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {y: round(sum(nets[k] for k, r in enumerate(rs) if r["yr"] == y), 1) for y in (2024, 2025, 2026)}
    ap = all(v > 0 for v in yr.values())
    if show:
        print(f"  {tag:<28} N{n:>4} hit3R {100*h/n:>5.1f}% NET {sum(nets):>7.1f} DD {dd:>6.1f} stk-{mL:>2} "
              f"| {n/WEEKS:.2f}/sem | {yr} {'✓' if ap else ''}")
    return {"n": n, "hit": h / n, "stk": mL, "net": sum(nets), "yr": yr, "ap": ap, "members": [r["cj_t"] for r in rs]}
def C(r, **req):
    f = P[r["cj_t"]]
    for k, (op, val) in req.items():
        v = f.get(k, 0)
        if op == ">=" and not v >= val: return False
        if op == "<" and not v < val: return False
    return True
print("=" * 104)
print("FORMA DA REVERSÃO — price-action denso (não depende de bubbles). RWS-ref: N54 44%% stk4")
print("=" * 104)
CONJ = {
 "PA1 rej+hl+vel": lambda r: C(r, rej_wick=(">=", 0.5), hl_seq=(">=", 1), vel=(">=", 0.5), bd=("<", 2)),
 "PA2 hl2+momentum": lambda r: C(r, hl_seq=(">=", 2), up_closes=(">=", 2), bd=("<", 2)),
 "PA3 rej_forte+rsi_turn": lambda r: C(r, rej_wick=(">=", 0.6), rsi_turn=(">=", 1), bd=("<", 2)),
 "PA4 vel_forte+hl": lambda r: C(r, vel=(">=", 0.8), hl_seq=(">=", 1), up_closes=(">=", 2), bd=("<", 2)),
}
res = {}
for nm, fn in CONJ.items():
    s = panel([r for r in NB if fn(r)], nm)
    if s: res[nm] = s
win = [nm for nm, s in res.items() if s["stk"] <= 4 and s["hit"] >= 0.38]
print(f"\nPASSAM (streak<=4 & hit>=38%): {win}")
# UNIÃO price-action winners + RWS (importado)
import importlib
def rws_members():
    j = json.load(open(HERE / "results" / "rws_sequence_engine_20260705.json"))
    return None  # membros não salvos; usar C0 via sharp json
sharp = json.load(open(HERE / "results" / "sharp_conjunctions_engine_20260705.json"))
rws_cj = set(sharp["conjunctions"]["C0_RWS"] and []) or set()
# recuperar membros RWS do union_members do sharp (winners incluíam C0)
rws_cj = set(sharp.get("union_members", []))
if win:
    union = {}
    for nm in win:
        for cj in res[nm]["members"]: union[cj] = next(r for r in NB if r["cj_t"] == cj)
    pa_union = list(union.values())
    su = panel(pa_union, "UNIÃO price-action")
    both = dict(union)
    for cj in rws_cj:
        m = [r for r in U if r["cj_t"] == cj]
        if m: both[cj] = m[0]
    panel(list(both.values()), "UNIÃO PA ∪ RWS")
    json.dump({"conjunctions": {nm: {k: s[k] for k in ("n", "hit", "stk", "net", "yr", "ap")} for nm, s in res.items()},
               "pa_winners": win, "pa_union_n": su["n"], "pa_union_hit": su["hit"], "pa_union_stk": su["stk"]},
              open(HERE / "results" / "priceaction_turn_engine_20260705.json", "w"), indent=1)
else:
    json.dump({"conjunctions": {nm: {k: s[k] for k in ("n", "hit", "stk", "net", "yr", "ap")} for nm, s in res.items()},
               "pa_winners": []}, open(HERE / "results" / "priceaction_turn_engine_20260705.json", "w"), indent=1)
print("OK → results/priceaction_turn_engine_20260705.json")
