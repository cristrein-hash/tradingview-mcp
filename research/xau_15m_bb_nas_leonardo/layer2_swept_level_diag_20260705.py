#!/usr/bin/env python3
"""LAYER 2 — DIAGNÓSTICO: que NÍVEL estrutural os 33 fundos BULL do Cris varrem? (2026-07-05)
IMPULSO-VIVO r1 falhou recall (5/33) usando só EQL-48h como nível. Calibração de recall no rótulo
(target-definition, declarada): para cada fundo GT BULL (e RANGE), testar que nível foi
FURADO-e-RECUPERADO pelo episódio:
  L_EQL     preço do último token EQL <=48h antes do flush
  L_BOS+    preço do último BOS+ <=96h (suporte do rompimento — retest/sweep clássico)
  L_CHoCH+  preço do último CHoCH+ <=96h
  L_FRACLOW low do candidato fractal anterior (<=96h)
  L_SWING24 min low das 24 barras que antecedem a janela do dip (24..96b atrás do flush)
Critério: flush_low < nível E close de alguma das 8 barras pós-flush > nível.
Saída: matriz por fundo + contagem por tipo → o(s) nível(is) dominante(s) para o gatilho v2."""
import json, bisect, hashlib, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])
GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GT.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
gap = json.load(open(HERE / "results" / "layer2_gap_map_20260705.json"))
MISSED = gap["missed_rows"]

EV2 = []
seen2 = set()
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for e in json.load(open(p))["smc_events"]:
        key = (e["t"], e["text"], round(e["price"], 2))
        if key in seen2:
            continue
        seen2.add(key)
        c = close_at(e["t"])
        if c is None:
            continue
        tok = e["text"] + (("+" if c > e["price"] else "-") if e["text"] in ("BOS", "CHoCH") else "")
        EV2.append({"t": e["t"], "tok": tok, "price": e["price"]})
EV2.sort(key=lambda x: x["t"]); ET2 = [e["t"] for e in EV2]
UT = sorted(U, key=lambda u: u["t"]); UTT = [u["t"] for u in UT]

def last_tok_price(ft, tok, hours):
    hi = bisect.bisect_right(ET2, ft)
    for i in range(hi - 1, -1, -1):
        if EV2[i]["t"] < ft - hours * 3600:
            break
        if EV2[i]["tok"] == tok:
            return EV2[i]["price"]
    return None

def prior_fraclow(ft):
    j = bisect.bisect_left(UTT, ft) - 1
    while j >= 0 and ft - UT[j]["t"] <= 96 * 3600:
        # low do fractal anterior = flush dele
        return UT[j]["g_sl"] + 0.1 * UT[j]["g_atr"]
    return None

def swing24(ft):
    i = bisect.bisect_right(TS, ft) - 1
    if i < 96:
        return None
    return min(S[k]["l"] for k in range(i - 96, i - 24))

def reclaimed(ft, flo, lvl):
    if lvl is None or not (flo < lvl):
        return 0
    i = bisect.bisect_right(TS, ft) - 1
    return int(any(S[k]["c"] > lvl for k in range(i, min(len(S), i + 9))))

from collections import Counter
print(f"{'classe':<6} {'data flush':>16} {'EQL':>4} {'BOS+':>4} {'CHoCH+':>6} {'FRACLOW':>7} {'SWING24':>7}")
cnt = {c: Counter() for c in ("BULL", "RANGE", "BEAR")}
tot = Counter()
for r in MISSED:
    cls = r["reg"] if r["reg"] in ("BULL", "BEAR") else "RANGE"
    ft, flo = r["ft"], r["flo"]
    res = {
        "EQL": reclaimed(ft, flo, last_tok_price(ft, "EQL", 48)),
        "BOS+": reclaimed(ft, flo, last_tok_price(ft, "BOS+", 96)),
        "CHoCH+": reclaimed(ft, flo, last_tok_price(ft, "CHoCH+", 96)),
        "FRACLOW": reclaimed(ft, flo, prior_fraclow(ft)),
        "SWING24": reclaimed(ft, flo, swing24(ft)),
    }
    for k, v in res.items():
        cnt[cls][k] += v
        tot[k] += v
    tot["_n"] += 1; cnt[cls]["_n"] += 1
    print(f"{cls:<6} {dt.datetime.utcfromtimestamp(ft).strftime('%Y-%m-%d %H:%M'):>16} "
          f"{res['EQL']:>4} {res['BOS+']:>4} {res['CHoCH+']:>6} {res['FRACLOW']:>7} {res['SWING24']:>7}"
          f"   {'NENHUM' if not any(res.values()) else ''}")
print("\nCONTAGEM sweep&reclaim por tipo de nível:")
for cls in ("BULL", "RANGE", "BEAR"):
    n = cnt[cls].pop("_n", 0)
    print(f"  {cls:<6} (N{n}): " + " · ".join(f"{k} {v}/{n}" for k, v in cnt[cls].most_common()))
n = tot.pop("_n")
print(f"  TOTAL (N{n}): " + " · ".join(f"{k} {v}/{n}" for k, v in tot.most_common()))
