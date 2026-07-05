#!/usr/bin/env python3
"""LAYER 2 — MAPA DO GAP (2026-07-05, mandato Cris: capturar os fundos deixados para trás).
Para cada um dos 60 fundos GT (selados): a CASCEX cobriu? Se NÃO — qual(is) gate(s) bloquearam
(cascata<4 · h1_rsi>42 · sem-demanda · reclaim<1,5 · veto macro-leg · nem-candidato-fractal),
em que ESTRUTURA vive (regime v5h, cascata efetiva, demanda, posição na perna/box, macro-leg),
e qual o prémio perdido (entrada causal reclaim+0,3ATR no flush, SL flush−0,1ATR, 3R, 480b capado,
custo SB — ORACLE-CONDICIONAL ao rótulo, declarado). Saída: tabela por fundo + histograma de gates
+ clusters estruturais = onde mora a Layer 2."""
import json, glob, bisect, hashlib
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])   # U, R3, S, TS, CTX, POCKET, _ml, cascade(), fv(), macro_leg()
GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
sha = hashlib.sha256(GT.read_bytes()).hexdigest()
assert sha == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
gt = json.load(open(GT)); assert len(gt) == 60
CASCEX = sorted([u for u in POCKET if u["_ml"]["vel"] < 0.10 and u["_ml"]["recent_frac"] < 0.5],
                key=lambda u: u["cj_t"])
CT = sorted(u["cj_t"] for u in CASCEX)

def near(t, arr, wh=8):
    j = bisect.bisect_left(arr, t)
    for k in (j - 1, j, j + 1):
        if 0 <= k < len(arr) and abs(arr[k] - t) <= wh * 3600:
            return True
    return False

# candidato fractal mais próximo do flush (±4h) — para ler contexto/gates
UT = sorted(range(len(U)), key=lambda k: U[k]["t"]); T = [U[k]["t"] for k in UT]
def nearest_cand(ft):
    j = bisect.bisect_left(T, ft - 4 * 3600); best = None
    while j < len(T) and T[j] <= ft + 4 * 3600:
        u = U[UT[j]]
        if best is None or abs(u["t"] - ft) < abs(best["t"] - ft):
            best = u
        j += 1
    return best

def oracle_entry(ft, flo):
    i = bisect.bisect_right(TS, ft) - 1
    atr = S[i].get("atr") or 5.0
    for k in range(i, min(len(S), i + 33)):
        if S[k]["c"] >= flo + 0.3 * atr:
            e = S[k]["c"]; sl = flo - 0.1 * atr; risk = e - sl
            if risk <= 0:
                return None
            tgt = e + 3 * risk
            for m in range(k + 1, min(len(S), k + 481)):
                if S[m]["l"] <= sl:
                    return -1.0 - 0.8 / risk
                if S[m]["h"] >= tgt:
                    return 3.0 - 0.8 / risk
            m = min(len(S) - 1, k + 480)
            return max(-1, min(3, (S[m]["c"] - e) / risk)) - 0.8 / risk
    return None

rows = []
for g in gt:
    ft, flo = g["flush_t"], g["flush_low"]
    covered = near(ft, CT)
    u = nearest_cand(ft)
    ml = macro_leg(ft)
    casc = cascade(u["cj_t"]) if u else cascade(ft)
    gates = []
    if u is None:
        gates.append("SEM_CANDIDATO")
    else:
        if casc < 4: gates.append(f"cascata={casc}")
        if fv(u, "h1_rsi", 99) > 42: gates.append(f"rsi1h={fv(u,'h1_rsi',99):.0f}")
        if not (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5): gates.append("sem_demanda")
        if fv(u, "reclaim_atr", 0) < 1.5: gates.append(f"reclaim={fv(u,'reclaim_atr',0):.1f}")
        if ml["vel"] >= 0.10 or ml["recent_frac"] >= 0.5: gates.append("veto_macroleg")
    orc = oracle_entry(ft, flo)
    rows.append({"ft": ft, "flo": flo, "covered": covered, "gates": gates,
                 "reg": (u or {}).get("g_v5h"), "casc": casc,
                 "demand": int(u is not None and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)),
                 "rsi1h": fv(u, "h1_rsi", None) if u else None,
                 "reclaim": fv(u, "reclaim_atr", None) if u else None,
                 "legpos": fv(u, "legpos60", None) if u else None,
                 "oracle_r": orc})

cov = [r for r in rows if r["covered"]]; miss = [r for r in rows if not r["covered"]]
print(f"COBERTURA CASCEX dos 60 fundos GT (±8h): {len(cov)}/60 → PERDIDOS: {len(miss)}")
mp = [r["oracle_r"] for r in miss if r["oracle_r"] is not None]
print(f"PRÉMIO PERDIDO (oracle-condicional, declarado): {len(mp)} entradas simuláveis · "
      f"hit3R {sum(1 for x in mp if x>=2.9)}/{len(mp)} · NET {sum(mp):+.1f}R")
print()
print(f"{'data flush':>16} {'reg':>6} {'casc':>4} {'dem':>3} {'rsi1h':>5} {'recl':>5} {'legp':>5} {'oracle':>7}  gates bloqueando")
for r in sorted(miss, key=lambda x: x["ft"]):
    print(f"{dt.datetime.utcfromtimestamp(r['ft']).strftime('%Y-%m-%d %H:%M'):>16} {str(r['reg']):>6} "
          f"{r['casc']:>4} {r['demand']:>3} {(f'{r[chr(114)+chr(115)+chr(105)+chr(49)+chr(104)]:.0f}' if r['rsi1h'] is not None else '—'):>5} "
          f"{(f'{r[chr(114)+chr(101)+chr(99)+chr(108)+chr(97)+chr(105)+chr(109)]:.1f}' if r['reclaim'] is not None else '—'):>5} "
          f"{(f'{r[chr(108)+chr(101)+chr(103)+chr(112)+chr(111)+chr(115)]:.2f}' if r['legpos'] is not None else '—'):>5} "
          f"{(f'{r[chr(111)+chr(114)+chr(97)+chr(99)+chr(108)+chr(101)+chr(95)+chr(114)]:+.2f}' if r['oracle_r'] is not None else '—'):>7}  {', '.join(r['gates'])}")
from collections import Counter
gc = Counter()
for r in miss:
    for gname in r["gates"]:
        gc[gname.split("=")[0]] += 1
print("\nHISTOGRAMA de gates bloqueando (fundos perdidos, multi-conta):")
for k, v in gc.most_common():
    print(f"  {k:<16} {v}/{len(miss)}")
solo = Counter()
for r in miss:
    keys = sorted({g.split("=")[0] for g in r["gates"]})
    solo["+".join(keys)] += 1
print("\nCOMBINAÇÕES de bloqueio (assinatura por fundo):")
for k, v in solo.most_common(12):
    print(f"  {k:<44} {v}")
json.dump({"covered": len(cov), "missed": len(miss),
           "missed_rows": [{k: v for k, v in r.items()} for r in miss]},
          open(HERE / "results" / "layer2_gap_map_20260705.json", "w"), indent=1, default=str)
print("OK → results/layer2_gap_map_20260705.json")
