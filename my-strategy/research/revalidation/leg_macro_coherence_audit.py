#!/usr/bin/env python3
"""AUDITORIA LEG × MACRO (ordem Cris 2026-07-13): como a PERNA (4H, macro-INDEPENDENTE) vive dentro
dos ciclos MACRO do Layer1 (1D aprovado). Leg = build_leg_series() base (estrutura só de pivôs 4H,
NÃO usa macro => coerência não-circular). Macro = build_layer1 (1D). Alinhamento CAUSAL: cada barra
4H recebe o rótulo macro 1D CONHECIDO ao fecho <= t (1D known = t_1d+86400). Sem lookahead.
Saída = VETOR AUDITADO (inventário + distribuição + coerência + sequência + spot-check + fricção),
nunca um score sozinho. RAW-only. Sem P&L."""
import sys, bisect, datetime as dt
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import macro_structural_v3 as M
import leg_state_4h as LG

d = lambda t: dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
T2019 = int(dt.datetime(2019, 1, 1, tzinfo=dt.timezone.utc).timestamp())

# --- macro 1D (Layer1) e known-times causais ---
lab1d = M.build_layer1()
T1 = M.T; KNOWN1 = [t + 86400 for t in T1]           # rótulo 1D conhecido só ao fecho (t+1d)
def macro_at(t):
    j = bisect.bisect_right(KNOWN1, t) - 1            # último 1D fechado <= t (causal)
    return lab1d[j] if j >= 0 else None

# --- leg 4H macro-INDEPENDENTE ---
legs = LG.build_leg_series()                          # {t, macro(ignorado), leg, leg_dir, leg_age}
rows = []
for r in legs:
    if r["t"] < T2019: continue
    mac = macro_at(r["t"])
    if mac is None: continue
    rows.append({"t": r["t"], "leg": r["leg"], "dir": r["leg_dir"], "age": r["leg_age"], "macro": mac})

# framework de coerência (declarado): impulso a favor + pullback contra = COERENTE; impulso contra
# = INCOERENTE; acumulação/pullback-ambíguo = NEUTRO. RANGE: acumulação coerente, impulso = fricção.
COH = {
    "BULL":  {"IMPULSO_UP": "coer", "PULLBACK_BEAR": "coer", "IMPULSO_DOWN": "incoer",
              "PULLBACK_BULL": "neutro", "ACUMULACAO": "neutro", "DISTRIBUICAO": "neutro"},
    "BEAR":  {"IMPULSO_DOWN": "coer", "PULLBACK_BULL": "coer", "IMPULSO_UP": "incoer",
              "PULLBACK_BEAR": "neutro", "ACUMULACAO": "neutro", "DISTRIBUICAO": "neutro"},
    "RANGE": {"ACUMULACAO": "coer", "DISTRIBUICAO": "coer", "PULLBACK_BULL": "neutro",
              "PULLBACK_BEAR": "neutro", "IMPULSO_UP": "incoer", "IMPULSO_DOWN": "incoer"},
}
def coh(mac, leg): return COH.get(mac, {}).get(leg, "neutro")

# --- blocos macro (runs sobre a timeline 4H) ---
blocks = []
for r in rows:
    if blocks and blocks[-1]["macro"] == r["macro"]: blocks[-1]["rows"].append(r)
    else: blocks.append({"macro": r["macro"], "rows": [r]})

def leg_episodes(brows):
    eps = []
    for r in brows:
        if eps and eps[-1][0] == r["leg"]: eps[-1][2] = r["t"]
        else: eps.append([r["leg"], r["t"], r["t"]])
    return eps

print("="*92)
print("AUDITORIA LEG(4H macro-indep) × MACRO(1D Layer1) · CAUSAL · 2019+ · barras 4H:", len(rows))
print("="*92)

# (A) INVENTÁRIO por bloco macro
print("\n(A) INVENTÁRIO — quantas/quais legs cada bloco macro contém:")
print(f"  {'macro':6} {'início':10} {'fim':10} {'dias':>4} {'nLeg':>4}  sequência de legs (episódios)")
LEGABBR = {"IMPULSO_UP": "I↑", "IMPULSO_DOWN": "I↓", "PULLBACK_BEAR": "pb↓",
           "PULLBACK_BULL": "pb↑", "ACUMULACAO": "AC", "DISTRIBUICAO": "DI"}
for b in blocks:
    eps = leg_episodes(b["rows"])
    days = int((b["rows"][-1]["t"] - b["rows"][0]["t"]) / 86400)
    if days < 5: continue
    seq = "·".join(LEGABBR.get(e[0], e[0]) for e in eps)
    print(f"  {b['macro']:6} {d(b['rows'][0]['t'])} {d(b['rows'][-1]['t'])} {days:4d} {len(eps):4d}  {seq}")

# (B) DISTRIBUIÇÃO por regime (fração de barras 4H por tipo de leg)
print("\n(B) DISTRIBUIÇÃO — % de barras 4H por tipo de leg, dentro de cada regime macro:")
byreg = defaultdict(Counter)
for r in rows: byreg[r["macro"]][r["leg"]] += 1
order = ["IMPULSO_UP", "PULLBACK_BEAR", "IMPULSO_DOWN", "PULLBACK_BULL", "ACUMULACAO", "DISTRIBUICAO"]
print(f"  {'regime':6} {'nbar':>5} " + " ".join(f"{LEGABBR[l]:>5}" for l in order))
for reg in ("BULL", "BEAR", "RANGE"):
    c = byreg[reg]; n = sum(c.values()) or 1
    print(f"  {reg:6} {n:5d} " + " ".join(f"{100*c[l]/n:5.0f}" for l in order))

# (C) COERÊNCIA por regime
print("\n(C) COERÊNCIA — % de barras coerentes / incoerentes / neutras por regime:")
print(f"  {'regime':6} {'nbar':>5} {'coer%':>6} {'incoer%':>7} {'neutro%':>7}")
for reg in ("BULL", "BEAR", "RANGE"):
    rr = [r for r in rows if r["macro"] == reg]; n = len(rr) or 1
    cc = Counter(coh(r["macro"], r["leg"]) for r in rr)
    print(f"  {reg:6} {n:5d} {100*cc['coer']/n:6.0f} {100*cc['incoer']/n:7.0f} {100*cc['neutro']/n:7.0f}")
alln = len(rows) or 1
ca = Counter(coh(r["macro"], r["leg"]) for r in rows)
print(f"  {'TOTAL':6} {alln:5d} {100*ca['coer']/alln:6.0f} {100*ca['incoer']/alln:7.0f} {100*ca['neutro']/alln:7.0f}")

# (D) SEQUÊNCIA — transições de leg dentro de cada regime (episódio->episódio)
print("\n(D) SEQUÊNCIA — transições de leg mais comuns dentro de cada regime (top 5):")
trans = defaultdict(Counter)
for b in blocks:
    eps = leg_episodes(b["rows"])
    for a, c in zip(eps, eps[1:]):
        trans[b["macro"]][f"{LEGABBR.get(a[0],a[0])}→{LEGABBR.get(c[0],c[0])}"] += 1
for reg in ("BULL", "BEAR", "RANGE"):
    top = trans[reg].most_common(5)
    print(f"  {reg:6}: " + " · ".join(f"{k}({v})" for k, v in top))

# (E) SPOT-CHECK — timeline de legs dos 3 maiores blocos de cada regime
print("\n(E) SPOT-CHECK — sequência de legs (episódios ≥3 barras 4H) nos maiores blocos:")
for reg in ("BULL", "BEAR", "RANGE"):
    cand = sorted([b for b in blocks if b["macro"] == reg],
                  key=lambda b: -(b["rows"][-1]["t"] - b["rows"][0]["t"]))[:2]
    for b in cand:
        print(f"  [{reg}] {d(b['rows'][0]['t'])}→{d(b['rows'][-1]['t'])}:")
        for leg, t0, t1 in leg_episodes(b["rows"]):
            nb = sum(1 for r in b["rows"] if t0 <= r["t"] <= t1)
            if nb < 3: continue
            print(f"       {d(t0)}→{d(t1)} {LEGABBR.get(leg,leg):>4} ({nb}b 4H) [{coh(reg,leg)}]")

# (F) FRICÇÃO — episódios INCOERENTES (impulso contra o macro) com ≥3 barras
print("\n(F) FRICÇÃO — episódios INCOERENTES (impulso contra o macro, ≥3 barras 4H):")
for b in blocks:
    for leg, t0, t1 in leg_episodes(b["rows"]):
        if coh(b["macro"], leg) != "incoer": continue
        nb = sum(1 for r in b["rows"] if t0 <= r["t"] <= t1)
        if nb < 3: continue
        print(f"  macro {b['macro']:5} contém {LEGABBR.get(leg,leg):>4} {d(t0)}→{d(t1)} ({nb}b 4H)")
