#!/usr/bin/env python3
"""SELA ground-truth dos 34 fundos do Cris (v2 — snap corrigido, 2026-07-05).
v1 falhou: janela ±6 barras (±1,5h) em círculos que cobrem horas → flush errado (ex. círculo 4019
snapou 4156). v2: janela ±16 barras (±4h) E âncora ao PREÇO do círculo — o flush é o menor low
da janela cujo low fique a ≤1,5% do preço do círculo (o círculo marca o nível do fundo); se nenhum
qualificar, alarga para ±32 barras (±8h) antes de aceitar o min-low puro (declarado no registo).
v3 (pós-DA): círculos largos + gaps de fim-de-semana (49h) tornavam ±32b curto — 3/34 snaps errados
(2025-09-04, 2025-11-13, 2026-06-10). Regra final: o PREÇO do círculo é a autoridade (é o nível que
o Cris marcou como fundo). Busca única ±120 barras (±30h); entre as barras cujo low fica a ≤1,5% do
preço do círculo, escolhe a de low MAIS PRÓXIMO do preço do círculo (não o min-low — evita saltar
para dip vizinho mais fundo); empate ≤0,1% resolve pela mais próxima no tempo. Fallback minlow ±32b
só se nada qualificar (declarado).
Também regista o swing-low imediatamente superior (entrada válida por decisão do Cris)."""
import json, glob, bisect, hashlib
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
# v4 (2026-07-05): Cris marcou mais fundos — fonte = TODOS os círculos atuais do chart (61).
# Timestamps de círculos re-extraídos jitteram com a vista → dedup é PÓS-SNAP (flush_t idêntico).
SRC = HERE / "results" / "cris_bottom_circles_all_20260705.json"
if not SRC.exists():
    SRC = HERE / "results" / "cris_bottom_circles_20260705.json"
circ = json.load(open(SRC))
print(f"fonte: {SRC.name} · {len(circ)} círculos")

series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]:
        series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]

def snap(t, pc):
    i = bisect.bisect_right(TS, t) - 1
    if i < 0:
        return None
    win = range(max(0, i - 120), min(len(S), i + 121))
    cand = [k for k in win if abs(S[k]["l"] - pc) / pc <= 0.015]
    if cand:
        best = min(abs(S[k]["l"] - pc) for k in cand)
        ties = [k for k in cand if abs(S[k]["l"] - pc) - best <= 0.001 * pc]
        lk = min(ties, key=lambda k: abs(S[k]["t"] - t))
        return lk, "anchored", 120
    win = range(max(0, i - 32), min(len(S), i + 33))
    lk = min(win, key=lambda k: S[k]["l"])
    return lk, "minlow", 32

gt = []
seen = set()
for t, pc in circ:
    r = snap(t, pc)
    assert r, (t, pc)
    lk, mode, w = r
    flush_t, flush_lo = S[lk]["t"], S[lk]["l"]
    if flush_t in seen:   # círculo re-extraído/jitterado do mesmo fundo
        continue
    seen.add(flush_t)
    hi_low = None
    for k in range(lk + 1, min(len(S), lk + 25)):
        if S[k]["l"] == min(S[j]["l"] for j in range(max(0, k - 2), min(len(S), k + 3))) and S[k]["l"] > flush_lo:
            hi_low = (S[k]["t"], S[k]["l"]); break
    gt.append({"circle_t": t, "circle_price": pc, "flush_t": flush_t, "flush_low": round(flush_lo, 2),
               "snap_mode": mode, "snap_win_bars": w,
               "higher_low_t": hi_low[0] if hi_low else None,
               "higher_low": round(hi_low[1], 2) if hi_low else None})

out = HERE / "results" / "ground_truth_bottoms_20260705.json"
json.dump(gt, open(out, "w"), indent=0)
sha = hashlib.sha256(out.read_bytes()).hexdigest()
(HERE / "results" / "ground_truth_bottoms_20260705.sha256").write_text(sha + "  ground_truth_bottoms_20260705.json\n")
bad = [g for g in gt if abs(g["flush_low"] - g["circle_price"]) / g["circle_price"] > 0.015]
print(f"GT SELADO: {len(gt)} fundos · sha {sha[:12]} · snap anchored={sum(1 for g in gt if g['snap_mode']=='anchored')}/{len(gt)}"
      f" · desvio>1,5% do círculo: {len(bad)}")
for g in gt:
    print(f"  {dt.datetime.utcfromtimestamp(g['flush_t']).strftime('%Y-%m-%d %H:%M')} "
          f"flush {g['flush_low']:>8.2f} (círculo {g['circle_price']:>8.2f}, {g['snap_mode']}/±{g['snap_win_bars']}b)")
