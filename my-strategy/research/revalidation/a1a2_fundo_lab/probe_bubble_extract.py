#!/usr/bin/env python3
"""PROBE (não é stage) — descobrir a forma eficiente e COMPLETA de extrair o mapa de bubbles do RAW.
Compara: (a) activations da ÚLTIMA linha do bloco vs (b) união de activations de TODAS as linhas.
Se (a)≈(b), usa-se a última linha (rápido). Mede tempo. py3.9 stdlib."""
import gzip, json, glob, time
from pathlib import Path
from collections import Counter

BLK = sorted(glob.glob("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-08-25*.jsonl.gz"))[0]
print("bloco:", Path(BLK).name)


def acts_of_line(o):
    pb = o.get("pine_shapes_bubbles") or []
    out = []
    for st in pb:
        for a in (st.get("activations") or []):
            out.append((a.get("time"), tuple(sorted((a.get("shapes") or {}).items()))))
    return out


# (a) última linha
t0 = time.time()
last = None
n_lines = 0
with gzip.open(BLK, "rt") as fh:
    for line in fh:
        last = line; n_lines += 1
last_acts = set(acts_of_line(json.loads(last)))
ta = time.time() - t0
print(f"(a) última linha: {len(last_acts)} activations únicas · {n_lines} linhas · {ta:.1f}s")

# (b) união de todas (amostra a cada 1 p/ ser exato, mas medir custo)
t0 = time.time()
allset = set()
with gzip.open(BLK, "rt") as fh:
    for i, line in enumerate(fh):
        # extração leve: só a região pine_shapes_bubbles
        k = line.find('"pine_shapes_bubbles"')
        if k < 0:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        allset |= set(acts_of_line(o))
tb = time.time() - t0
print(f"(b) união todas as linhas: {len(allset)} activations únicas · {tb:.1f}s")

miss = allset - last_acts
print(f"na união mas NÃO na última linha: {len(miss)} ({100*len(miss)/max(1,len(allset)):.1f}%)")
# mapa de plots presentes
plots = Counter()
for _, shs in allset:
    for p, v in shs:
        plots[p] += 1
print("plots (união):", dict(plots))
print("\nVEREDITO:", "USA ÚLTIMA LINHA (completa)" if len(miss) == 0 else f"PRECISA UNIÃO ({len(miss)} perdidas na última)")
