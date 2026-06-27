#!/usr/bin/env python3
"""DIAGNÓSTICO: a esparsidade de sweep_reclaim/failed_breakdown é BUG ou o substrato NAS-em-zona não casa com o
gatilho sweep+reclaim+retest da leitura visual? Conta disponibilidade de EQ no RAW, penetração>1, e testa
failed_breakdown numa JANELA (não só no run in-zone). Verified 2026-06-26."""
import csv, json
from pathlib import Path
from collections import Counter
HERE = Path(__file__).parent
PRIM = {p.name.split(".")[0].replace("XAUUSD_15m_replay_", ""): json.loads(p.read_text())
        for p in (HERE / "primitives").glob("*.primitives.json")}
# disponibilidade EQH/EQL no smc_events
eqc = Counter()
for b, pr in PRIM.items():
    for e in pr["smc_events"]:
        t = str(e.get("text") or "")
        if "EQH" in t: eqc["EQH"] += 1
        elif "EQL" in t: eqc["EQL"] += 1
        elif "CHoCH" in t: eqc["CHoCH"] += 1
        elif "BOS" in t: eqc["BOS"] += 1
print("SMC eventos (2 anos):", dict(eqc))
rows = list(csv.DictReader(open(HERE / "candidates_features.csv")))
wm = [r for r in rows if r["setup_vs_macro"] == "with_macro"]
# penetração>1 (onde failed_breakdown deveria ser possível)
pen1 = [r for r in rows if float(r["penetration_pct"]) > 1.0]
pen1_wm = [r for r in wm if float(r["penetration_pct"]) > 1.0]
print(f"penetração>1: geral {len(pen1)}/{len(rows)} | with_macro {len(pen1_wm)}/{len(wm)}")
# failed_breakdown numa JANELA de 12 barras antes de j (não só run in-zone)
SER = {b: pr["series"] for b, pr in PRIM.items()}
TID = {b: {x["t"]: i for i, x in enumerate(s)} for b, s in SER.items()}
fb_win = 0
for r in wm:
    b = r["block"]; s = SER.get(b); j = TID.get(b, {}).get(int(r["nas_t"]))
    if j is None: continue
    long = r["dir"] == "LONG"; zlo = float(r["zone_low"]); zhi = float(r["zone_high"])
    win = s[max(0, j - 12):j + 1]
    if long:
        broke = any(x["c"] < zlo for x in win); back = s[j]["c"] > zlo
    else:
        broke = any(x["c"] > zhi for x in win); back = s[j]["c"] < zhi
    if broke and back: fb_win += 1
print(f"failed_breakdown (janela 12b, with_macro): {fb_win}/{len(wm)}")
# quantos with_macro têm ALGUM EQ oposto no lookback 96b (pré-condição do sweep_reclaim)
have_eq = 0
for r in wm:
    b = r["block"]; nas_t = int(r["nas_t"]); long = r["dir"] == "LONG"; want = "EQL" if long else "EQH"
    if any(e.get("text") and want in str(e["text"]) and nas_t - 96 * 900 <= (e["t"] or 0) <= nas_t for e in PRIM[b]["smc_events"]):
        have_eq += 1
print(f"with_macro com EQ oposto no lookback 96b (pré-cond sweep): {have_eq}/{len(wm)}")
print("\nLeitura: se EQ raríssimo E penetração>1 raro no with_macro => substrato NAS-em-zona NÃO casa com o gatilho")
print("sweep+reclaim+retest da visão => pivot p/ NOVO universo (gatilho=liquidez), NAS/zona/regime como confluência.")
