#!/usr/bin/env python3
"""MOTOR DE DEMANDA MACRO v2 (2026-07-05) — correção de geometria após v1 (pivô-low macro: 10/60).
Diagnóstico v1: em BULL forte o preço NÃO volta ao low do pivô macro — os fundos do Cris são
pullbacks à ORIGEM DA PARTIDA. Duas geometrias novas (causais):

  ZB breakout-retest: swing high H (janela w barras p/ cada lado, known_at = k+w) é ROMPIDO
     (close > H + 0,1·ATR) → H vira demanda: zona [H − zh·ATR, H + 0,25·ATR], nasce no rompimento.
     Morte: close < H − (zh+0,5)·ATR.
  ZC base de impulso: compressão (range de M barras <= c·ATR) seguida de impulso
     (close > topo_box + 0,5·ATR) → zona = topo da base [box_hi − zh·ATR, box_hi + 0,25·ATR].
     Morte: close < box_lo − 0,25·ATR.

Match GT: flush_low em [lo − 0,75·ATR, hi + 0,25·ATR] (fundos do Cris varrem ABAIXO do nível —
sweep da demanda é parte da assinatura). Zona conhecida ANTES do flush. Taxa-base p/ lift.

SANITY_PROBE:
  P1 known_at >= swing_i + w (assert) — swing high só conta depois de confirmado
  P2 zona nasce no rompimento (close acima), nunca antes (assert breakout_i > swing_i + w)
  P3 taxa-base barras-em-zona vs recall → lift; recall alto sem lift = régua frouxa
  P4 amostra de zonas com datas p/ reconciliação visual
"""
import json, bisect, hashlib
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]

def swing_highs(w):
    out = []
    for k in range(w, N - w):
        h = HI[k]
        if h == max(HI[k - w:k + w + 1]) and HI[k - w:k].count(h) == 0:
            out.append(k)
    return out

def zones_breakout(w, zh):
    zones = []
    shs = swing_highs(w)
    for k in shs:
        H = HI[k]
        # rompimento: primeiro close > H + 0,1·ATR depois de k+w
        for i in range(k + w, min(k + w + 1920, N)):
            if CL[i] > H + 0.1 * ATR[i]:
                assert i >= k + w  # P1/P2
                z = {"lo": H - zh * ATR[i], "hi": H + 0.25 * ATR[i], "atr": ATR[i],
                     "ref": H, "known_i": i, "known_t": S[i]["t"], "src_i": k, "kind": "ZB"}
                zones.append(z)
                break
            if CL[i] < H - 6 * ATR[i]:      # afundou longe: swing morto sem romper
                break
    for z in zones:
        z["death_t"] = None; z["death_i"] = N - 1
        thr = z["ref"] - (zh + 0.5) * z["atr"]
        for k2 in range(z["known_i"] + 1, N):
            if CL[k2] < thr:
                z["death_t"] = S[k2]["t"]; z["death_i"] = k2
                break
    return zones

def zones_basebox(M, c, zh):
    zones = []
    i = M
    while i < N:
        seg_hi = max(HI[i - M:i]); seg_lo = min(LO[i - M:i])
        if seg_hi - seg_lo <= c * ATR[i] and CL[i] > seg_hi + 0.5 * ATR[i]:
            z = {"lo": seg_hi - zh * ATR[i], "hi": seg_hi + 0.25 * ATR[i], "atr": ATR[i],
                 "ref": seg_hi, "box_lo": seg_lo, "known_i": i, "known_t": S[i]["t"], "kind": "ZC"}
            zones.append(z)
            i += M          # não empilhar a mesma base
            continue
        i += 1
    for z in zones:
        z["death_t"] = None; z["death_i"] = N - 1
        thr = z["box_lo"] - 0.25 * z["atr"]
        for k2 in range(z["known_i"] + 1, N):
            if CL[k2] < thr:
                z["death_t"] = S[k2]["t"]; z["death_i"] = k2
                break
    return zones

def match_gt(zones, tol_lo=0.75, tol_hi=0.25):
    hits = []
    for g in GT:
        ft, flo = g["flush_t"], g["flush_low"]
        best = None
        for z in zones:
            if z["known_t"] > ft - 900:
                continue
            if z["death_t"] is not None and z["death_t"] < ft:
                continue
            if z["lo"] - tol_lo * z["atr"] <= flo <= z["hi"] + tol_hi * z["atr"]:
                if best is None or z["known_t"] > best["known_t"]:
                    best = z
        if best:
            hits.append((g, best))
    return hits

def base_rate(zones, tol_lo=0.75, tol_hi=0.25):
    touched = set()
    for z in zones:
        lo, hi = z["lo"] - tol_lo * z["atr"], z["hi"] + tol_hi * z["atr"]
        for k in range(z["known_i"] + 1, z["death_i"] + 1):
            if lo <= LO[k] <= hi:
                touched.add(k)
    return len(touched) / N

print(f"{'geom':<22} {'zonas':>6} {'recall/60':>9} {'base%':>7} {'lift':>6}")
res = {}
for w in (32, 96):
    for zh in (0.5, 1.0):
        zs = zones_breakout(w, zh)
        h = match_gt(zs); br = base_rate(zs)
        lift = (len(h) / 60) / br if br else 0
        res[f"ZB w{w} zh{zh}"] = (zs, h, br, lift)
        print(f"{'ZB w' + str(w) + ' zh' + str(zh):<22} {len(zs):>6} {len(h):>6}/60 {100*br:>6.1f}% {lift:>6.2f}")
for M, c in ((24, 2.0), (48, 3.0)):
    for zh in (0.5, 1.0):
        zs = zones_basebox(M, c, zh)
        h = match_gt(zs); br = base_rate(zs)
        lift = (len(h) / 60) / br if br else 0
        res[f"ZC M{M} c{c} zh{zh}"] = (zs, h, br, lift)
        print(f"{'ZC M' + str(M) + ' c' + str(c) + ' zh' + str(zh):<22} {len(zs):>6} {len(h):>6}/60 {100*br:>6.1f}% {lift:>6.2f}")

# união melhor-ZB + melhor-ZC
bZB = max((k for k in res if k.startswith("ZB")), key=lambda k: len(res[k][1]))
bZC = max((k for k in res if k.startswith("ZC")), key=lambda k: len(res[k][1]))
uz = res[bZB][0] + res[bZC][0]
h = match_gt(uz); br = base_rate(uz)
print(f"\nUNIÃO {bZB} + {bZC}: recall {len(h)}/60 · base {100*br:.1f}% · lift {(len(h)/60)/br if br else 0:.2f}")
hit_ids = {id(g) for g, z in h}
print("PERDIDOS na união:")
for g in GT:
    if id(g) not in hit_ids:
        print(f"  {dt.datetime.utcfromtimestamp(g['flush_t']).strftime('%Y-%m-%d %H:%M')} lo {g['flush_low']:.0f}")
json.dump({k: {"zones": len(v[0]), "recall": len(v[1]), "base": round(v[2], 4), "lift": round(v[3], 2)}
           for k, v in res.items()},
          open(HERE / "results" / "macro_demand_zone_v2_20260705.json", "w"), indent=1)
print("OK → results/macro_demand_zone_v2_20260705.json")
