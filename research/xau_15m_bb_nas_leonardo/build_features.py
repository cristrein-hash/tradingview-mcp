#!/usr/bin/env python3
"""ANEL 1 — FEATURE BUILDER (top8 backlog rodada 1), causal RAW. Adiciona ao candidates_annotated.csv:
  sweep_reclaim (EQ SMC: varre EQL/EQH e refecha dentro <=2 barras) — entry-timing canon #1;
  failed_breakdown (spring/upthrust: fecha além da borda da zona e refecha dentro, id vivo) — resgata penetração-alta;
  micro_choch (CHoCH SMC na direção macro na janela) — timing de retomada;
  nas_density50 (nº NAS ambas direções em 50 barras) — chop/risk-shaping (alto=ambiente ruim);
  room_to_run (dist à estrutura oposta — OB oposto/EQ oposto — em ATR) — runway p/ let-run.
Causal: tudo com bars/eventos t<=nas_t (j=bar de confirmação), SHIFT1 nos que repintam (SMC). Saída candidates_features.csv.
Verified 2026-06-26."""
import csv, json, bisect
from pathlib import Path
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in (HERE / "primitives").glob("*.primitives.json")}
SER = {b: pr["series"] for b, pr in PRIM.items()}
TID = {b: {x["t"]: i for i, x in enumerate(s)} for b, s in SER.items()}
SMC = {b: sorted(pr["smc_events"], key=lambda e: e["t"] or 0) for b, pr in PRIM.items()}
ZON = {b: pr["zones"] for b, pr in PRIM.items()}
EPS = 0.0003

def feats(r):
    b = r["block"]; s = SER.get(b); tid = TID.get(b)
    if s is None: return {}
    j = tid.get(int(r["nas_t"]))
    if j is None: return {}
    long = r["dir"] == "LONG"; entry = float(r["entry_close"])
    zlo = float(r["zone_low"]); zhi = float(r["zone_high"]); zwa = float(r["zone_width_atr"])
    atr = (zhi - zlo) / zwa if zwa > 0 else None
    if not atr or atr <= 0: return {}
    nas_t = int(r["nas_t"]); smc = SMC[b]
    # --- sweep_reclaim no nível EQ oposto ---
    want = "EQL" if long else "EQH"
    lvls = [e["price"] for e in smc if e["text"] and want in str(e["text"]) and e["price"] is not None
            and nas_t - 96 * 900 <= (e["t"] or 0) <= nas_t]
    swept = 0; sweep_depth = 0.0
    if lvls:
        lvl = lvls[-1]; w0 = max(0, j - 20)
        win = s[w0:j + 1]
        if long:
            mn = min(x["l"] for x in win); breach = mn < lvl * (1 - EPS)
            recl = any(x["c"] > lvl for x in win[-3:]); swept = int(breach and recl); sweep_depth = (lvl - mn) / atr
        else:
            mx = max(x["h"] for x in win); breach = mx > lvl * (1 + EPS)
            recl = any(x["c"] < lvl for x in win[-3:]); swept = int(breach and recl); sweep_depth = (mx - lvl) / atr
    # --- failed_breakdown (spring/upthrust na borda da zona) ---
    rs = j
    while rs - 1 >= 0 and (s[rs - 1]["l"] <= zhi and s[rs - 1]["h"] >= zlo): rs -= 1
    run = s[rs:j + 1]; fb = 0; brk_exc = 0.0
    if long:
        broke = any(x["c"] < zlo for x in run); back = s[j]["c"] > zlo
        fb = int(broke and back); brk_exc = (zlo - min(x["l"] for x in run)) / atr if run else 0
    else:
        broke = any(x["c"] > zhi for x in run); back = s[j]["c"] < zhi
        fb = int(broke and back); brk_exc = (max(x["h"] for x in run) - zhi) / atr if run else 0
    # --- micro_choch na direção macro ---
    mc = int(any(e["text"] and "CHoCH" in str(e["text"]) and nas_t - 40 * 900 <= (e["t"] or 0) <= nas_t for e in smc))
    # --- nas_density (chop) ---
    pr = PRIM[b]; nas_ev = pr["nas_events"]
    dens = sum(1 for e in nas_ev if nas_t - 50 * 900 <= (e["t"] or 0) <= nas_t)
    # --- room_to_run: dist à estrutura oposta (OB oposto + EQ oposto) ---
    opp_pol = "SUPPLY" if long else "DEMAND"
    opp = []
    for z in ZON[b]:
        if opp_pol in z["text"] and z["born_t"] and z["born_t"] <= nas_t and z["last_t"] >= nas_t:
            edge = z["low"] if long else z["high"]
            if (long and edge > entry) or ((not long) and edge < entry): opp.append(abs(edge - entry))
    eqw = "EQH" if long else "EQL"
    for e in smc:
        if e["text"] and eqw in str(e["text"]) and e["price"] is not None and (e["t"] or 0) <= nas_t:
            if (long and e["price"] > entry) or ((not long) and e["price"] < entry): opp.append(abs(e["price"] - entry))
    room = (min(opp) / atr) if opp else 99.0
    return {"sweep_reclaim": swept, "sweep_depth_atr": round(sweep_depth, 2), "failed_breakdown": fb,
            "brk_exc_atr": round(brk_exc, 2), "micro_choch": mc, "nas_density50": dens, "room_to_run_atr": round(room, 2)}

rows = list(csv.DictReader(open(HERE / "candidates_annotated.csv")))
out = []
for r in rows:
    f = feats(r); out.append({**r, **f}) if f else None
out = [o for o in out if o]
cols = list(out[0].keys())
with open(HERE / "candidates_features.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(out)
# sumário cobertura
from collections import Counter
n = len(out); wm = [o for o in out if o["setup_vs_macro"] == "with_macro"]
print(f"candidates_features.csv: {n} linhas")
for k in ("sweep_reclaim", "failed_breakdown", "micro_choch"):
    print(f"  {k}=1: geral {sum(int(o[k]) for o in out)}/{n} | with_macro {sum(int(o[k]) for o in wm)}/{len(wm)}")
import statistics as st
print(f"  nas_density50 med={st.median([int(o['nas_density50']) for o in out])} | room_to_run_atr med={st.median([float(o['room_to_run_atr']) for o in out if float(o['room_to_run_atr'])<99]):.1f}")
