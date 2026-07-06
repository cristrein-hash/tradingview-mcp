#!/usr/bin/env python3
"""DEMANDA VERDADEIRA = NÍVEL REVISITADO COM MEMÓRIA (2026-07-06).
Cris (literal): "ler as pernas de contexto em 15M com largura de dias/semanas para descobrir as
demandas verdadeiras ONDE PREÇO VOLTA PARA TESTAR EM PULLBACK E PARTE PARA NOVA ALTA". Não é a
zona-OB do indicador (já testada = h4n_in_demand). É MEMÓRIA DE PREÇO:
  demanda verdadeira D = swing-low anterior (>= LAG barras atrás) de onde o preço SUBIU >= UP·ATR
  (partiu para nova alta / rompeu o high anterior). O candidato TESTA D se flush_low em
  [D − tol·ATR, D + tol·ATR]. known_at causal: D confirmado antes de cj.
TESTE (reframe de POOL, o que o olho conta como fundo-plausível): densidade sósia:fundo e
recall-círculo do subconjunto "testa demanda verdadeira", varrendo (LAG, UP, tol). Se colapsa a
densidade mantendo círculos → o discriminador do olho ERA memória de nível, não feature local.
SANITY_PROBE: sha GT · matcher v2 · D causal (swing confirmado + subida antes de cj) · densidade
por CÍRCULO distinto · sem outcome na seleção do pool."""
import json, bisect, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]
UNIV = sorted([u for u in U if u["cj_t"] in R3], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]
for u in UNIV: u["_circ"] = set()
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8 * 3600:
        u = UNIV[j]
        a = u.get("g_atr") or 5.0
        d = (u["g_sl"] + 0.1 * a) - g["flush_low"]
        if -3 * a <= d <= 1 * a: u["_circ"].add(gi)
        j += 1

# swing lows w=8 (fractais)
SWL = []
w = 8
for k in range(w, N - w):
    if LO[k] == min(LO[k - w:k + w + 1]) and LO[k - w:k].count(LO[k]) == 0:
        SWL.append(k)
# suffix-max de HI p/ "nova alta" O(1); pré-cálculo do breakout bar por (swing, UP)
BRK = {}   # (k, UP) -> primeiro bar m onde subiu UP·ATR acima de LO[k] E rompeu pre-hi; None
for UP in (3, 5, 8):
    for k in SWL:
        base = LO[k]; a = ATR[k]
        pre_hi = max(HI[max(0, k - 96):k]) if k > 0 else base
        need = max(base + UP * a, pre_hi + 1e-9)
        m = None
        for mm in range(k + 1, min(N, k + 1920)):   # até 20 dias após o swing
            if HI[mm] >= need:
                m = mm; break
        BRK[(k, UP)] = m
# demandas ordenadas por breakout bar p/ query rápida
DEM = {UP: sorted(((BRK[(k, UP)], k) for k in SWL if BRK[(k, UP)] is not None))
       for UP in (3, 5, 8)}
DEM_B = {UP: [x[0] for x in DEM[UP]] for UP in (3, 5, 8)}

def true_demands(cj, LAG, UP):
    ci = bisect.bisect_right(TS, cj) - 1
    hi = bisect.bisect_right(DEM_B[UP], ci)      # breakout conhecido (<= ci)
    out = []
    for idx in range(hi):
        brk_m, k = DEM[UP][idx]
        if k <= ci - LAG:                         # swing suficientemente antigo
            out.append((LO[k], ATR[k]))
    return out

def density(rows):
    c = len(set().union(*(u["_circ"] for u in rows)) if rows else set())
    f = sum(1 for u in rows if u["_circ"]); n = len(rows)
    return n, f, c

n0, f0, c0 = density(UNIV)
print(f"POOL bruto: N{n0} · fundo {f0} · círculos {c0}/60 · densidade {(n0-f0)/f0:.1f}:1")
print("\ntesta-demanda-verdadeira (LAG barras, UP·ATR subida, tol·ATR):")
best = None
for LAG in (96, 192, 384):
    for UP in (3, 5, 8):
        for tol in (0.5, 1.0):
            sub = []
            for u in UNIV:
                a = u.get("g_atr") or 5.0
                flo = u["g_sl"] + 0.1 * a
                ds = true_demands(u["cj_t"], LAG, UP)
                if any(D - tol * da <= flo <= D + tol * da for D, da in ds):
                    sub.append(u)
            n, f, c = density(sub)
            dd = (n - f) / max(1, f)
            tag = f"  LAG{LAG:>3} UP{UP} tol{tol}: N{n:>4} fundo {f:>3} círc {c:>2}/60 dens {dd:>5.1f}:1"
            print(tag)
            score = (c, -dd)
            if c >= 30 and (best is None or score > best[0]):
                best = (score, (LAG, UP, tol), (n, f, c, dd))
if best:
    (LAG, UP, tol) = best[1]; n, f, c, dd = best[2]
    print(f"\nMELHOR c/ recall>=30: LAG{LAG} UP{UP} tol{tol} → densidade {dd:.1f}:1 (círc {c}/60)")
    print(f"redução vs pool bruto: {(n0-f0)/f0:.1f}:1 → {dd:.1f}:1")
json.dump({"pool_dens": round((n0-f0)/f0, 1), "best": best[2] if best else None},
          open(HERE / "results" / "density_true_demand_20260706.json", "w"), indent=1, default=str)
print("OK → results/density_true_demand_20260706.json")
