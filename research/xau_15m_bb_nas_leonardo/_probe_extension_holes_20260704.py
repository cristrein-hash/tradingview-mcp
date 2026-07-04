#!/usr/bin/env python3
"""Extensão 2026-07-04 run-2: quantifica buracos de 1 barra (30min meio-de-sessão) no trecho novo
e compara com o PRECEDENTE dos blocos históricos (8º bloco) — soluços de replay_step são artefato
conhecido do coletor? Decide aceitação documentada."""
import json, csv, datetime as dt
from pathlib import Path
HERE = Path(__file__).parent

r2 = list(csv.DictReader(open(HERE / "results" / "raw_15m_extension_gap_report_20260704.csv")))
holes = [g for g in r2 if g["type"] == "session" and int(g["gap_min"]) == 30]
print(f"run-2: {len(holes)} buracos de 1 barra em 2689 ({100*len(holes)/2689:.2f}%)")

for name in ("2026-02-25_to_2026-05-25_rerun_customOBbaseline", "2025-11-25_to_2026-02-25"):
    s = json.load(open(HERE / "primitives" / f"XAUUSD_15m_replay_{name}.primitives.json"))["series"]
    ts = [b["t"] for b in s]
    h = 0
    for i in range(1, len(ts)):
        d = ts[i] - ts[i - 1]
        if d == 1800:  # 30 min = exatamente 1 barra faltando
            a = dt.datetime.utcfromtimestamp(ts[i - 1])
            if a.weekday() < 5 and not (a.hour in (20, 21, 22)):  # exclui breaks diários/fds
                h += 1
    print(f"bloco {name[:10]}: {h} buracos de 1 barra em {len(ts)} bars ({100*h/len(ts):.2f}%)")
