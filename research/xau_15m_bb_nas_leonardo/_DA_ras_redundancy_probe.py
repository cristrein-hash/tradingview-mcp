#!/usr/bin/env python3
"""DA probe — avaliacao adversarial da feature RAS (regime_alignment_stack).
Verifica se os blocos da RAS ja existem como colunas e mede a populacao dos estados
propostos (ideal_pullback, macro_only, counter_macro) na base anotada (sem outcome).
Conclusao: setup_vs_macro/leg_dir/is_pullback/op_flow/setup_vs_flow JA EXISTEM.
ideal_pullback colapsa para n=6 (0.06/sem) -> alvo 1-3/sem inatingivel como gate unico.
Read-only. 2026-06-26."""
import csv
from collections import Counter
from pathlib import Path
HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "candidates_annotated.csv")))
print("n=", len(rows))
print("setup_vs_macro:", dict(Counter(r["setup_vs_macro"] for r in rows)))
print("setup_vs_flow:", dict(Counter(r["setup_vs_flow"] for r in rows)))
print("is_pullback:", dict(Counter(r["is_pullback"] for r in rows)))
wm = [r for r in rows if r["setup_vs_macro"] == "with_macro"]
print("with_macro n=", len(wm), "| flow:", dict(Counter(r["setup_vs_flow"] for r in wm)))
ideal = [r for r in wm if r["setup_vs_flow"] == "continuation" and r["is_pullback"] == "True"]
mo = [r for r in wm if r["setup_vs_flow"] == "reversal"]
print("ideal_pullback (wm+cont+pb) n=", len(ideal))
print("macro_only-ish (wm + flow reversal) n=", len(mo))
print("counter_macro n=", sum(1 for r in rows if r["setup_vs_macro"] == "counter_macro"))
ts = sorted(int(r["entry_t"]) for r in rows); wk = (ts[-1] - ts[0]) / (7 * 86400)
print("weeks=%.0f ideal/wk=%.2f" % (wk, len(ideal) / wk))
