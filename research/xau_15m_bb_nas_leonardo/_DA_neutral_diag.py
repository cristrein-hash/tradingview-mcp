#!/usr/bin/env python3
"""DIAGNÓSTICO (não-gate) do NEUTRAL: o macro atual exige swing∧EMA50. Quantos candidatos hoje neutral/counter
virariam with_macro sob macros alternativos mais permissivos (EMA-only)? Mede se a regra estrita descarta
continuações a-favor. Lê candidates_annotated.csv (RAW-derivado). NÃO altera o gate. Verified 2026-06-26."""
import csv
from pathlib import Path
from collections import Counter
HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "candidates_annotated.csv")))
n = len(rows)
def ema_macro(r):  # macro alternativo: só posição vs EMA50-4H (sem exigir swing confirmado)
    ep = int(r["macro_ema_pos"]); return "BULL" if ep > 0 else "BEAR"
def svm(D, macro):
    if (D == "LONG" and macro == "BULL") or (D == "SHORT" and macro == "BEAR"): return "with_macro"
    return "counter_macro"
cur = Counter(r["setup_vs_macro"] for r in rows)
alt = Counter(svm(r["dir"], ema_macro(r)) for r in rows)
print(f"candidatos = {n}")
print(f"ATUAL (swing∧EMA): with_macro {cur['with_macro']} | counter {cur['counter_macro']} | neutral {cur['neutral_macro']}")
print(f"ALT (EMA-only):    with_macro {alt['with_macro']} | counter {alt['counter_macro']}")
# quantos NEUTRAL atuais virariam with_macro sob EMA-only (= continuações potencialmente descartadas pela rigidez)
flip = [r for r in rows if r["setup_vs_macro"] == "neutral_macro" and svm(r["dir"], ema_macro(r)) == "with_macro"]
fl = sum(1 for r in flip if r["dir"] == "LONG")
print(f"\nNEUTRAL→with_macro sob EMA-only: {len(flip)} (LONG {fl} / SHORT {len(flip)-fl})")
print("  = continuações a-favor-da-EMA que o swing-estrito jogou em neutral.")
# desses, quantos têm swing_dir alinhado também (só faltou o par de 2 swings) vs swing contrário
import statistics as st
aligned = sum(1 for r in flip if (r["dir"]=="LONG" and int(r["macro_swing_dir"])>=0) or (r["dir"]=="SHORT" and int(r["macro_swing_dir"])<=0))
print(f"  destes, swing NÃO-contrário (só faltou confirmação): {aligned} | swing contrário (EMA-lag real): {len(flip)-aligned}")
# counter atuais que sob EMA-only continuam counter (brigando com EMA também) = descartes sólidos
solid_counter = sum(1 for r in rows if r["setup_vs_macro"]=="counter_macro" and svm(r["dir"], ema_macro(r))=="counter_macro")
print(f"\ncounter_macro que TAMBÉM brigam com a EMA (descarte sólido): {solid_counter}/{cur['counter_macro']}")
print("\nLeitura: se NEUTRAL→with sob EMA-only for grande E majoritariamente swing-não-contrário, a regra estrita")
print("está sufocando continuações; avaliar 'swing OR ema-slope-forte' como macro (a validar, não tunar ao alvo).")
