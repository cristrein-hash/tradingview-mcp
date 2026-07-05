#!/usr/bin/env python3
"""RECONCILIAÇÃO: BASE435 (swept-runner OFICIAL_FN) × 34 fundos ground-truth do Cris (2026-07-05).
Pergunta única: a assinatura swept-runner JÁ dispara nos fundos de capitulação que o Cris marcou?
Se sim → problema = seleção/filtro em cima dela (não falta detector). Se não → falta detector novo.
GT selado: results/ground_truth_bottoms_20260705.json (sha 226962f9, extraído dos círculos via MCP).
Entrada do engine = close da barra cj_t (convenção do engine). Gap medido em ATR vs flush real.
Janela de match ±8h (mesma da reconciliação RWS). Sem tuning, zero parâmetros livres."""
import json, glob, bisect, hashlib, contextlib, io, statistics as st
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent

GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
sha = hashlib.sha256(GT.read_bytes()).hexdigest()
assert sha == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0], "GT selo violado"
gt = json.load(open(GT))
assert len(gt) == 34

ns = {"__name__": "engine", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "engine", "exec"), ns)
base = [c for c in ns["cand"] if c["v5h"] != "BEAR"]
assert len(base) == 435 and abs(sum(c["R"] for c in base) - 291.5) < 0.5, "BASE435 não reproduz"

series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]:
        series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]

def bar(t):
    i = bisect.bisect_right(TS, t) - 1
    return S[i] if i >= 0 else None

BT = sorted(c["cj_t"] for c in base)
BP = {c["cj_t"]: c for c in base}

def nearest(t, arr, wh=8):
    j = bisect.bisect_left(arr, t); best = None
    for k in (j - 1, j, j + 1):
        if 0 <= k < len(arr) and abs(arr[k] - t) <= wh * 3600:
            if best is None or abs(arr[k] - t) < abs(best - t):
                best = arr[k]
    return best

print("BASE435 × 34 FUNDOS GROUND-TRUTH (±8h)")
print(f"{'data flush':<17} {'flush':>8} {'match?':>6} {'Δt(h)':>6} {'gap ATR':>8} {'R':>6}")
cov = 0; gaps = []; rr = []
for g in gt:
    nb = nearest(g["flush_t"], BT)
    if nb is None:
        print(f"{dt.datetime.utcfromtimestamp(g['flush_t']).strftime('%Y-%m-%d %H:%M'):<17} "
              f"{g['flush_low']:>8.0f} {'NAO':>6}")
        continue
    cov += 1; c = BP[nb]; b = bar(nb)
    entry = b["c"]; atr = b.get("atr") or 5.0
    gap = (entry - g["flush_low"]) / atr
    gaps.append(gap); rr.append(c["R"])
    print(f"{dt.datetime.utcfromtimestamp(g['flush_t']).strftime('%Y-%m-%d %H:%M'):<17} "
          f"{g['flush_low']:>8.0f} {'SIM':>6} {(nb-g['flush_t'])/3600:>+6.1f} {gap:>+8.2f} {c['R']:>+6.2f}")

print()
print(f"COBERTURA: {cov}/34 fundos do Cris têm sinal BASE435 em ±8h")
if gaps:
    print(f"  gap entrada-vs-flush: mediana {st.median(gaps):+.2f}ATR · média {st.mean(gaps):+.2f}ATR")
    print(f"  resultado dos matches (R let-run): sum {sum(rr):+.1f} · R>0: {sum(1 for r in rr if r > 0)}/{len(rr)} "
          f"· R>=3: {sum(1 for r in rr if r >= 3)}/{len(rr)}")
# contexto: RWS cobria 4/34 a +3.6ATR
json.dump({"coverage": cov, "total_gt": 34,
           "gap_atr_median": round(st.median(gaps), 2) if gaps else None,
           "matches_R_sum": round(sum(rr), 1) if rr else None,
           "matches_R_pos": sum(1 for r in rr if r > 0) if rr else 0,
           "matches_R3": sum(1 for r in rr if r >= 3) if rr else 0},
          open(HERE / "results" / "gt_cross_base435_20260705.json", "w"), indent=1)
print("OK → results/gt_cross_base435_20260705.json")
