#!/usr/bin/env python3
"""MOTOR DE DEMANDA MACRO — leitura estrutural de pernas de DIAS/SEMANAS no 15M (2026-07-05).
Ordem do Cris (feedback GTQ/DF): "ler as pernas de contexto em 15M com largura de dias ou semanas
para descobrir as demandas verdadeiras onde preço volta para testar em pullback e parte para nova
alta". Nada de réguas locais: a unidade é a PERNA MACRO (zigzag causal, reversão em múltiplos de
ATR grandes) e a demanda é a ORIGEM da perna de alta.

CONSTRUÇÃO (causal estrita):
  zigzag: pivô LOW confirmado quando preço sobe >= r·ATR do low corrente (known_at = barra da
  confirmação, NUNCA a barra do pivô); simétrico p/ HIGH. r em ATR15 grandes (8/12/16/24 ≈ 1-3 dias
  de swing em XAU).
  zona de demanda: ao confirmar pivô LOW → zona [low, low + zh·ATR@pivô], ativa a partir de
  known_at; morre quando close < low − 0,25·ATR. 'validated' = a perna que nasceu nela rompeu o
  high do pivô macro anterior (pullback que parte para nova alta — a frase do Cris literal).

FASE 1 = CALIBRAÇÃO DE RECALL (declarado: mapa, não teste): dos 60 fundos GT do Cris, quantos
caem DENTRO de zona ativa conhecida ANTES do flush? + taxa-base de barras-em-zona p/ lift.

SANITY_PROBE:
  P1 known_at > pivot_t em 100% dos pivôs (assert) — zero look-ahead
  P2 zona só conta se known_at <= flush_t − 900 e não morta antes do flush (assert no matcher)
  P3 amostra de 3 zonas impressa com datas p/ reconciliação visual do Cris
  P4 taxa-base de barras-em-zona reportada — recall sem lift = régua frouxa, não leitura
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
print(f"barras 15M: {len(S)} · GT: {len(GT)}")

def zigzag_zones(r_atr, zh):
    """pivôs macro por reversão r_atr·ATR; zonas de demanda nos pivôs LOW."""
    zones = []; pivots = []
    d = 0; ehi = elo = 0
    for i in range(1, len(S)):
        b = S[i]; atr = b.get("atr") or 5.0
        if S[i]["h"] > S[ehi]["h"]:
            ehi = i
        if S[i]["l"] < S[elo]["l"]:
            elo = i
        if d >= 0 and S[ehi]["h"] - S[i]["l"] >= r_atr * atr and ehi < i:
            pivots.append(("H", ehi, i))
            assert i > ehi  # P1
            d = -1
            elo = min(range(ehi, i + 1), key=lambda k: S[k]["l"])
        elif d <= 0 and S[i]["h"] - S[elo]["l"] >= r_atr * atr and elo < i:
            pivots.append(("L", elo, i))
            assert i > elo  # P1
            patr = S[elo].get("atr") or 5.0
            zones.append({"lo": S[elo]["l"], "hi": S[elo]["l"] + zh * patr,
                          "atr": patr, "pivot_t": S[elo]["t"], "known_t": S[i]["t"],
                          "pivot_i": elo, "known_i": i})
            d = 1
            ehi = max(range(elo, i + 1), key=lambda k: S[k]["h"])
    # morte da zona: close < lo − 0,25·ATR após known
    for z in zones:
        z["death_t"] = None
        for k in range(z["known_i"] + 1, len(S)):
            if S[k]["c"] < z["lo"] - 0.25 * z["atr"]:
                z["death_t"] = S[k]["t"]; z["death_i"] = k
                break
    # validated: perna a partir do pivô rompeu o high macro anterior antes da morte
    ph = [(p[1], S[p[1]]["h"]) for p in pivots if p[0] == "H"]
    for z in zones:
        prev_h = [h for i2, h in ph if i2 < z["pivot_i"]]
        z["validated"] = False
        if prev_h:
            tgt = prev_h[-1]
            end = z.get("death_i", len(S) - 1) or len(S) - 1
            for k in range(z["pivot_i"], min(end + 1, len(S))):
                if S[k]["h"] > tgt:
                    z["validated"] = True
                    break
    return zones, pivots

def match_gt(zones, tol_lo=0.5, tol_hi=0.25):
    hits = []
    for g in GT:
        ft, flo = g["flush_t"], g["flush_low"]
        best = None
        for z in zones:
            if z["known_t"] > ft - 900:          # P2: conhecida ANTES do flush
                continue
            if z["death_t"] is not None and z["death_t"] < ft:
                continue
            if z["lo"] - tol_lo * z["atr"] <= flo <= z["hi"] + tol_hi * z["atr"]:
                if best is None or z["known_t"] > best["known_t"]:
                    best = z
        if best:
            hits.append((g, best))
    return hits

def base_rate(zones, tol_lo=0.5, tol_hi=0.25):
    touched = set()
    for z in zones:
        end = z.get("death_i") or len(S) - 1
        for k in range(z["known_i"] + 1, end + 1):
            if z["lo"] - tol_lo * z["atr"] <= S[k]["l"] <= z["hi"] + tol_hi * z["atr"]:
                touched.add(k)
    return len(touched) / len(S), touched

print(f"\n{'r·ATR':>6} {'zh':>4} {'zonas':>6} {'recall/60':>9} {'taxa-base%':>10} {'lift':>6} {'val-hits':>8}")
results = {}
for r in (8, 12, 16, 24):
    for zh in (0.5, 1.0, 1.5):
        zones, piv = zigzag_zones(r, zh)
        hits = match_gt(zones)
        br, _ = base_rate(zones)
        rec = len(hits) / len(GT)
        lift = (rec / br) if br > 0 else 0
        vh = sum(1 for g, z in hits if z["validated"])
        results[(r, zh)] = {"zones": len(zones), "recall": len(hits), "base_rate": round(br, 4),
                            "lift": round(lift, 2), "val_hits": vh}
        print(f"{r:>6} {zh:>4} {len(zones):>6} {len(hits):>6}/60 {100*br:>9.1f}% {lift:>6.2f} {vh:>8}")

# melhor config por lift com recall >= 30: detalhe por GT
cand = [(k, v) for k, v in results.items() if v["recall"] >= 30]
if cand:
    bk = max(cand, key=lambda kv: kv[1]["lift"])[0]
else:
    bk = max(results, key=lambda k: results[k]["recall"])
zones, piv = zigzag_zones(*bk)
hits = match_gt(zones)
hit_ids = {id(g) for g, z in hits}
print(f"\nMELHOR (r={bk[0]}, zh={bk[1]}): {len(hits)}/60 · zonas {len(zones)}")
print("GT capturados (data flush → zona nascida em · idade dias · validated):")
for g, z in sorted(hits, key=lambda x: x[0]["flush_t"]):
    age_d = (g["flush_t"] - z["known_t"]) / 86400
    print(f"  {dt.datetime.utcfromtimestamp(g['flush_t']).strftime('%Y-%m-%d %H:%M')} lo {g['flush_low']:.0f}"
          f" → zona {z['lo']:.0f}-{z['hi']:.0f} conhecida {dt.datetime.utcfromtimestamp(z['known_t']).strftime('%m-%d')}"
          f" · {age_d:.1f}d · {'VAL' if z['validated'] else '—'}")
print("\nGT PERDIDOS:")
for g in GT:
    if id(g) not in hit_ids:
        print(f"  {dt.datetime.utcfromtimestamp(g['flush_t']).strftime('%Y-%m-%d %H:%M')} lo {g['flush_low']:.0f}")
print("\nP3 amostra 3 zonas:")
for z in zones[:3]:
    print(f"  pivô {dt.datetime.utcfromtimestamp(z['pivot_t']).strftime('%Y-%m-%d %H:%M')} lo {z['lo']:.0f}"
          f" conhecida {dt.datetime.utcfromtimestamp(z['known_t']).strftime('%Y-%m-%d %H:%M')}"
          f" morte {dt.datetime.utcfromtimestamp(z['death_t']).strftime('%Y-%m-%d') if z['death_t'] else 'viva'}")
json.dump({str(k): v for k, v in results.items()},
          open(HERE / "results" / "macro_demand_zone_calib_20260705.json", "w"), indent=1)
print("OK → results/macro_demand_zone_calib_20260705.json")
