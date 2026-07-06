#!/usr/bin/env python3
"""REFRAME DA DENSIDADE — a parede 28:1 mede o GERADOR, não o gráfico (2026-07-06).
Cris: "densidade 28:1 indistinguível é IMPOSSÍVEL, não faz parte da realidade do gráfico". Ele
marcou os 60 fundos OLHANDO — logo são distinguíveis. Meu erro provável: comparei winners contra
TODO candidato flush-reclaim (o gerador emite ~6/dia em qualquer mínima k=3 c/ reclaim), a maioria
dos quais NÃO tem perna de queda — não são "fundos plausíveis" que o olho confundiria.
TESTE: medir a MAGNITUDE ABSOLUTA da perna de queda antes de cada candidato (travel_atr da perna
macro que termina no flush; causal, <= cj) e ver:
  1. distribuição travel_atr nos 60 fundos (via matcher v2) vs pool inteiro
  2. quanto o pool ENCOLHE filtrando por travel_atr >= q-dos-fundos, mantendo os fundos
  3. densidade sósia:fundo ANTES e DEPOIS do filtro de perna → a densidade real é do gráfico?
+ mesma coisa p/ clímax (g_atr_spike) e profundidade de sweep (g_sweep_depth) — os 3 traços que o
olho usa p/ dizer "isto é um fundo, aquilo é ruído".
SEM outcome/seleção: é reframe de POOL (o que conta como fundo-plausível), não seletor de winner.
SANITY_PROBE: sha GT · matcher v2 · travel via macro_leg causal · densidade contada por CÍRCULO
distinto (não por candidato)."""
import json, bisect, hashlib
import statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])          # U, R3, S, TS, fv, macro_leg
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
UNIV = sorted([u for u in U if u["cj_t"] in R3], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]

# marca círculo (matcher v2) e computa travel da perna macro
for u in UNIV:
    u["_circ"] = set()
    ml = macro_leg(u["cj_t"])
    u["_travel"] = ml["travel"] if ml else None
    u["_vel"] = ml["vel"] if ml else None
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8 * 3600:
        u = UNIV[j]
        a = u.get("g_atr") or 5.0
        d = (u["g_sl"] + 0.1 * a) - g["flush_low"]
        if -3 * a <= d <= 1 * a:
            u["_circ"].add(gi)
        j += 1

FUND = [u for u in UNIV if u["_circ"]]        # candidatos que SÃO fundo (capturam círculo)
POOL = UNIV
def dist(rows, k):
    v = sorted(fv2(u, k) for u in rows if fv2(u, k) is not None)
    if not v: return None
    return (v[int(0.10*(len(v)-1))], v[len(v)//2], v[int(0.90*(len(v)-1))])
def fv2(u, k):
    return u.get(k) if isinstance(u.get(k), (int, float)) and not isinstance(u.get(k), bool) else None

print("distribuição q10/med/q90 — FUNDO (candidatos-círculo) vs POOL inteiro:")
for k in ("_travel", "g_atr_spike", "g_sweep_depth", "_vel", "g_downrun", "pullback_depth"):
    df = dist(FUND, k); dp = dist(POOL, k)
    if df and dp:
        print(f"  {k:<16} FUNDO {df[0]:>6.2f}/{df[1]:>6.2f}/{df[2]:>6.2f}  ·  POOL {dp[0]:>6.2f}/{dp[1]:>6.2f}/{dp[2]:>6.2f}")

def circles_in(rows):
    return len(set().union(*(u["_circ"] for u in rows)) if rows else set())
def density(rows):
    c = circles_in(rows)
    f = sum(1 for u in rows if u["_circ"])
    n = len(rows)
    return n, f, c

n0, f0, c0 = density(POOL)
print(f"\nPOOL bruto: N{n0} · candidatos-fundo {f0} · círculos {c0}/60 · densidade sósia:fundo {(n0-f0)/f0:.1f}:1")

print("\nFiltro por PERNA (travel_atr) — pool encolhe, círculos ficam?:")
tf = sorted(u["_travel"] for u in FUND if u["_travel"] is not None)
for qq, lab in ((0.05, "q05-fundos"), (0.10, "q10-fundos"), (0.25, "q25-fundos")):
    thr = tf[int(qq*(len(tf)-1))]
    sub = [u for u in POOL if u["_travel"] is not None and u["_travel"] >= thr]
    n, f, c = density(sub)
    print(f"  travel>={thr:>5.1f} ({lab}): N{n:>4} · fundo {f} · círculos {c}/60 · densidade {(n-f)/max(1,f):.1f}:1")

print("\nFiltro CONVERGENTE (perna + clímax + sweep, thresholds = q10 dos fundos):")
def q10f(k):
    v = sorted(fv2(u, k) for u in FUND if fv2(u, k) is not None)
    return v[int(0.10*(len(v)-1))]
t_tr, t_sp, t_sw = None, q10f("g_atr_spike"), q10f("g_sweep_depth")
t_tr = tf[int(0.10*(len(tf)-1))]
conv = [u for u in POOL if u["_travel"] is not None and u["_travel"] >= t_tr
        and fv2(u, "g_atr_spike") is not None and fv2(u, "g_atr_spike") >= t_sp
        and fv2(u, "g_sweep_depth") is not None and fv2(u, "g_sweep_depth") >= t_sw]
n, f, c = density(conv)
print(f"  perna>={t_tr:.1f} & spike>={t_sp:.2f} & sweep>={t_sw:.2f}: N{n} · fundo {f} · círculos {c}/60 "
      f"· densidade {(n-f)/max(1,f):.1f}:1")
# outcome do pool convergente (mapa, não seletor): hit3R
if conv:
    h = sum(1 for u in conv if R3[u["cj_t"]]["R3"] >= 3)
    nets = [R3[u["cj_t"]]["net3"] for u in conv]
    print(f"  (referência outcome do pool convergente: hit3R {100*h/n:.1f}% · NET {sum(nets):+.1f} · {n/len({u['g_week'] for u in U}):.2f}/sem)")
json.dump({"pool_density": round((n0-f0)/f0, 1),
           "conv_density": round((n-f)/max(1,f), 1), "conv_n": n, "conv_circ": c},
          open(HERE / "results" / "density_reframe_leg_20260706.json", "w"), indent=1)
print("OK → results/density_reframe_leg_20260706.json")
