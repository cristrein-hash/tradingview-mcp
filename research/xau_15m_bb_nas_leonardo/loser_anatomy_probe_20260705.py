#!/usr/bin/env python3
"""ANATOMIA DOS LOSERS PLOTADOS (2026-07-05) — verificação da leitura visual do Cris nos dados.
Hipótese dele (prints): losers = entradas em PERNA INACABADA (mercado ainda faz lows novos depois;
o fundo real vem abaixo/depois), não necessariamente 'faca vertical'. Para os 20 plotados (#37-56):
  a) leg_unfinished: low novo abaixo do low da barra de entrada nas 32 barras seguintes ANTES do 3R
  b) new_low_depth: quão abaixo (ATR) esse low novo foi
  c) bars_since_bearbreak: barras desde a última QUEBRA bear por PREÇO (close cruza swing-low 12b)
     — proxy ex-ante de 'perna ainda ativa' (independente de labels; sem lag de indicador)
  d) choch_up_price: houve virada bull por preço (close > último swing-high 12b) antes da entrada?
Compara losers vs winners. SANITY_PROBE de leitura (N20) — clareza, não inferência."""
import json, glob, bisect
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
series = {}; EV = []
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]:
        series.setdefault(b["t"], b)
    EV += d["smc_events"]
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]

def close_at(t):
    i = bisect.bisect_right(TS, t) - 1
    return S[i]["c"] if i >= 0 else None

seen = set(); events = []
for e in sorted(EV, key=lambda x: x["t"]):
    key = (e["t"], e["text"], round(e["price"], 2))
    if key in seen or e["text"] not in ("BOS", "CHoCH"):
        continue
    seen.add(key)
    c = close_at(e["t"])
    if c is None:
        continue
    events.append({"t": e["t"], "tok": e["text"] + ("+" if c > e["price"] else "-")})
ET = [e["t"] for e in events]

def cascade(cj):
    hi = bisect.bisect_right(ET, cj)
    dirs = [events[i]["tok"] for i in range(hi) if events[i]["t"] >= cj - 192 * 900]
    n = 0
    for tok in reversed(dirs):
        if tok in ("BOS-", "CHoCH-"):
            n += 1
        else:
            break
    return n

def fv(u, k, d=None):
    v = u.get(k)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d

POCKET = sorted([u for u in U if u["cj_t"] in R3 and cascade(u["cj_t"]) >= 4
                 and fv(u, "reclaim_atr", 0) >= 1.5
                 and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)
                 and fv(u, "h1_rsi", 99) <= 42], key=lambda u: u["cj_t"])
CUT = int(dt.datetime(2025, 8, 1, tzinfo=dt.timezone.utc).timestamp())
plot = [(gid, u) for gid, u in enumerate(POCKET, 1) if u["cj_t"] >= CUT]

def price_breaks(i):
    """última quebra bear por preço e virada bull por preço antes da barra i (swings 12b)."""
    last_bear = None; choch_up = False
    lows = []; highs = []
    for k in range(max(0, i - 192), i + 1):
        # swing low/high 12b (fechado: usa só barras <= k)
        j0 = max(0, k - 12)
        swl = min(S[j]["l"] for j in range(j0, k)) if k > j0 else None
        swh = max(S[j]["h"] for j in range(j0, k)) if k > j0 else None
        if swl is not None and S[k]["c"] < swl:
            last_bear = k; choch_up = False
        if swh is not None and S[k]["c"] > swh and last_bear is not None and k > last_bear:
            choch_up = True
    return last_bear, choch_up

print(f"{'#':>3} {'data':>16} {'res':>4} {'legUnfin?':>9} {'newLowATR':>9} {'brsSinceBear':>12} {'chochUp?':>8}")
agg = {"W": {"unf": 0, "n": 0, "cad": [], "chu": 0}, "L": {"unf": 0, "n": 0, "cad": [], "chu": 0}}
for gid, u in plot:
    cj = u["cj_t"]; i = bisect.bisect_right(TS, cj) - 1
    atr = S[i].get("atr") or 5.0
    entry_low = S[i]["l"]; sl = u["g_sl"]
    win = R3[cj]["R3"] >= 3
    unf = 0; depth = 0.0
    tgt = u["g_entry"] + 3 * (u["g_entry"] - u["g_sl"])
    for k in range(i + 1, min(len(S), i + 33)):
        if S[k]["h"] >= tgt:
            break
        if S[k]["l"] < entry_low:
            unf = 1; depth = max(depth, (entry_low - S[k]["l"]) / atr)
    lb, chu = price_breaks(i)
    cad = i - lb if lb is not None else 99
    tag = "W" if win else "L"
    agg[tag]["unf"] += unf; agg[tag]["n"] += 1; agg[tag]["cad"].append(cad); agg[tag]["chu"] += chu
    print(f"#{gid:>2} {dt.datetime.utcfromtimestamp(cj).strftime('%Y-%m-%d %H:%M'):>16} "
          f"{'WIN' if win else 'LOSS':>4} {unf:>9} {depth:>9.2f} {cad:>12} {int(chu):>8}")
import statistics as st
for tag in ("W", "L"):
    a = agg[tag]
    print(f"\n{tag}: N{a['n']} · perna-inacabada {a['unf']}/{a['n']} · "
          f"cadência mediana desde última quebra bear {st.median(a['cad'])}b · CHoCH+preço antes: {a['chu']}/{a['n']}")
