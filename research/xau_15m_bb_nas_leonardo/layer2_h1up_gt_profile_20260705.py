#!/usr/bin/env python3
"""LAYER 2 — perfil GT-vs-vizinhos dentro da família h1up (2026-07-05).
h1up = 1ª lente FDR da caça (P=0,002). Diagnóstico de calibração (N pequeno, declarado): dos
membros h1up da base v3, separa os GT-estritos dos vizinhos pelos medianos das features causais
(15M + 30M/1H computadas) → candidatos a lente da próxima iteração. Não é teste; é mapa."""
import json, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "layer2_cris35_lenses_20260705.py").read_text().split("pb = panel(BASE")[0])
# marca GT-estrito nos membros da base
gt = json.load(open(HERE / "results" / "ground_truth_bottoms_20260705.json"))
import bisect as bs
BS = sorted(BASE, key=lambda u: u["cj_t"]); BT = [u["cj_t"] for u in BS]
for u in BASE:
    u["_gt"] = 0
for g in gt:
    j = bs.bisect_left(BT, g["flush_t"] - 8 * 3600)
    while j < len(BT) and BT[j] <= g["flush_t"] + 8 * 3600:
        u = BS[j]
        if abs((u["g_sl"] + 0.1 * u["g_atr"]) - g["flush_low"]) <= (u.get("g_atr") or 5.0):
            u["_gt"] = 1
        j += 1
H1 = [u for u in BASE if fv(u, "h1_trend", 0) == 1]
GTm = [u for u in H1 if u["_gt"]]; NG = [u for u in H1 if not u["_gt"]]
print(f"família h1up: N{len(H1)} · GT-estritos {len(GTm)} · vizinhos {len(NG)}")
FEATS = ["legpos60", "g_box96", "g_sweep_depth", "reclaim_atr", "g_atr_spike", "pullback_depth",
         "rsi_low", "h1_rsi", "h1_pos", "g_ema21_dist", "n_supply_overhead", "dist_demand_atr",
         "low_wick", "confirm_body_atr", "up_closes_pc", "atr_compression_pre", "g_hour"]
print(f"{'feature':<20} {'GT med':>8} {'viz med':>8} {'razão/Δ':>8}")
rows = {}
for f in FEATS:
    a = [fv(u, f) for u in GTm if fv(u, f) is not None]
    b = [fv(u, f) for u in NG if fv(u, f) is not None]
    if not a or not b:
        continue
    ma, mb = st.median(a), st.median(b)
    rows[f] = (ma, mb)
    print(f"{f:<20} {ma:>8.2f} {mb:>8.2f} {(ma-mb):>+8.2f}")
for nm, arr in (("quiet30", "_q30"), ("vdry1h", "_vd"), ("choch24", "_ch")):
    a = [u[arr] for u in GTm if u.get(arr) is not None]
    b = [u[arr] for u in NG if u.get(arr) is not None]
    if a and b:
        print(f"{nm:<20} {st.median(a):>8.2f} {st.median(b):>8.2f} {(st.median(a)-st.median(b)):>+8.2f}")
import datetime as dt
print("\nGT-estritos h1up (datas p/ leitura visual do Cris):")
for u in sorted(GTm, key=lambda x: x["cj_t"]):
    print(" ", dt.datetime.utcfromtimestamp(u["cj_t"]).strftime("%Y-%m-%d %H:%M"),
          f"legpos {fv(u,'legpos60',9):.2f} sweep {fv(u,'g_sweep_depth',0):.2f} recl {fv(u,'reclaim_atr',0):.1f}")
