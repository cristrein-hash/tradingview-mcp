#!/usr/bin/env python3
"""DIP-3R — entrada de FUNDO REAL, árbitro hit-3R (2026-07-05, GO Cris após crítica do Sistema A).
Diagnóstico aceito: Sistema A = 0/53 no fundo, 41/53 no TOPO do range (box96>0.66), WR inflado por
pops de topo; os gates de momentum (violência/resposta/reclaim<=3) empurram a seleção pro esticado.
CORREÇÃO: posição estrutural de FUNDO = gate de 1ª classe; árbitro = hit-3R limpo (não WR-let-run).

FASE 1 — CARACTERIZAÇÃO (declarada como looks): hit-3R por box96/ema21_dist/dip-profundidade no
universo não-BEAR — revela onde o 3R vive (achar o sinal descartado).
FASE 2 — ENTRADA CONGELADA a partir da TESE (não do melhor bucket): dip genuíno = box96 baixo +
NÃO-esticado (ema21_dist<=q) + profundidade real abaixo do high + suporte (demanda) + regime !=BEAR +
anti-faca. UMA config, thresholds por quantil do universo declarados, zero grid.
FASE 3 — painel (hit-3R/WR-3R/NET-SB/DD/streak/freq/por-ano) + nulls (random mesmo-N 500 · year 500).
Universo selado; R3 pré-computado. Seed 42."""
import json, bisect, random, hashlib, collections, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
SB = 0.80; random.seed(42)
CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
WEEKS = len({r["g_week"] for r in U})

NB = [r for r in U if r["g_v5h"] != "BEAR"]   # não-BEAR (BEAR = lane separada)
def hit(rows): return sum(1 for r in rows if R3[r["cj_t"]]["R3"] >= 3) / len(rows) if rows else 0
def q(vals, p):
    v = sorted(vals); return v[int(p * len(v))]

print("=" * 96)
print("DIP-3R — desenho de FUNDO REAL (árbitro hit-3R). Universo não-BEAR N=%d · breakeven 25%%" % len(NB))
print("=" * 96)
print("\nFASE 1 — CARACTERIZAÇÃO (looks declarados): hit-3R por POSIÇÃO ESTRUTURAL")
print("  box96 (posição no range 96b; FUNDO=baixo):")
for lo, hival in [(0, .2), (.2, .4), (.4, .6), (.6, .8), (.8, 1.01)]:
    sub = [r for r in NB if lo <= fv(r, "g_box96", .5) < hival]
    print(f"    [{lo:.1f},{hival:.1f}) N{len(sub):>4} hit3R {100*hit(sub):>5.1f}% ({sum(1 for r in sub if R3[r['cj_t']]['R3']>=3)} de {len(sub)})")
print("  ema21_dist (esticamento; NEGATIVO=abaixo da EMA):")
for lo, hival in [(-9, 0), (0, .5), (.5, 1.0), (1.0, 1.5), (1.5, 9)]:
    sub = [r for r in NB if lo <= fv(r, "g_ema21_dist", 0) < hival]
    print(f"    [{lo:.1f},{hival:.1f}) N{len(sub):>4} hit3R {100*hit(sub):>5.1f}%")
# dip real: profundidade da queda desde o high-96 em ATR = (1-box96) proxy? usar g_box96 baixo já cobre.
print("  legpos90 (posição na perna maior):")
for lo, hival in [(0, .25), (.25, .5), (.5, .75), (.75, 1.01)]:
    sub = [r for r in NB if lo <= fv(r, "legpos90", .5) < hival]
    print(f"    [{lo:.2f},{hival:.2f}) N{len(sub):>4} hit3R {100*hit(sub):>5.1f}%")
print("  in_demand (suporte sob o preço):")
for v in (0, 1):
    sub = [r for r in NB if fv(r, "in_demand") == v]
    print(f"    in_demand={v} N{len(sub):>4} hit3R {100*hit(sub):>5.1f}%")

# quantis do universo p/ thresholds declarados
box_q40 = q([fv(r, "g_box96", .5) for r in NB], 0.40)
ema_q50 = q([fv(r, "g_ema21_dist", 0) for r in NB], 0.50)
print(f"\nquantis declarados: box96 q40={box_q40:.2f} · ema21_dist q50={ema_q50:.2f}")

print("\nFASE 2 — ENTRADA DIP-3R CONGELADA (tese de fundo; UMA config):")
def dip3r(r):
    return (r["g_v5h"] != "BEAR"                                 # regime up/range (BEAR = lane separada)
        and fv(r, "g_box96", .5) <= box_q40                      # FUNDO do range (1ª classe)
        and fv(r, "g_ema21_dist", 9) <= ema_q50                  # NÃO-esticado (correção central)
        and fv(r, "legpos60", 1) <= 0.5                          # metade inferior da perna
        and (fv(r, "in_demand") == 1 or fv(r, "dist_demand_atr", 9) <= 1.0)  # suporte real
        and r["g_knife"] == 0                                    # anti-faca
        and fv(r, "rsi_low", 50) >= 30)                          # não capitulação extrema
def panel(rows, tag, show=True):
    n = len(rows)
    if not n:
        if show: print(f"  {tag:<22} vazio");
        return None
    rs = sorted(rows, key=lambda r: r["cj_t"]); nets = [R3[r["cj_t"]]["net3"] for r in rs]
    h = sum(1 for r in rs if R3[r["cj_t"]]["R3"] >= 3); w = sum(1 for x in nets if x > 0)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {}
    for r, x in zip(rs, nets): yr[r["yr"]] = round(yr.get(r["yr"], 0) + x, 1)
    if show:
        print(f"  {tag:<22} N{n:>4} hit3R {100*h/n:>5.1f}% WR {100*w/n:>5.1f}% NET {sum(nets):>7.1f} "
              f"DD {dd:>6.1f} stk-{mL} | {n/WEEKS:.2f}/sem | {yr}")
    return {"n": n, "hit": h / n, "net": sum(nets), "stk": mL, "dd": dd}
D = [r for r in U if dip3r(r)]
std = panel(D, "DIP-3R")
# comparação estrutural: onde caem (box96)?
if D:
    boxes = collections.Counter("fundo" if fv(r, "g_box96", .5) < 0.33 else ("topo" if fv(r, "g_box96", .5) > 0.66 else "meio") for r in D)
    print(f"    posição estrutural: {dict(boxes)} (contraste: Sistema A = 0 fundo / 41 topo)")
    # nulls
    k = len(D); pool = NB
    nd_r = []; by_yr = collections.defaultdict(list)
    for r in pool: by_yr[r["yr"]].append(r)
    kyr = collections.Counter(r["yr"] for r in D); nd_y = []
    for _ in range(500):
        nd_r.append(sum(R3[r["cj_t"]]["net3"] for r in random.sample(pool, k)))
        py = [r for y, c in kyr.items() for r in random.sample(by_yr[y], min(c, len(by_yr[y])))]
        nd_y.append(sum(R3[r["cj_t"]]["net3"] for r in py))
    pct = lambda o, d: round(100 * sum(1 for x in d if x < o) / len(d), 1)
    # null de hit-3R (o árbitro): fração de amostras aleatórias com hit >= observado
    hits_null = [sum(1 for r in random.sample(pool, k) if R3[r["cj_t"]]["R3"] >= 3) / k for _ in range(500)]
    print(f"    árbitro hit-3R: obs {100*std['hit']:.1f}% vs null méd {100*st.mean(hits_null):.1f}% "
          f"q95 {100*sorted(hits_null)[475]:.1f}% → pct {round(100*sum(1 for x in hits_null if x<std['hit'])/500,1)}%")
    print(f"    null NET: random pct {pct(std['net'], nd_r)}% · year-aware pct {pct(std['net'], nd_y)}%")
    print(f"    FN: hit>=55? {std['hit']>=0.55} · streak {std['stk']} · ~1/sem? {k/WEEKS:.2f}")
json.dump({"box96_q40": box_q40, "ema21_q50": ema_q50, "N": len(D),
           "hit3R": std["hit"] if D else None, "net": std["net"] if D else None,
           "stk": std["stk"] if D else None, "per_week": len(D) / WEEKS,
           "members_cjt": [r["cj_t"] for r in D]},
          open(HERE / "results" / "dip3r_design_20260705.json", "w"), indent=1)
print("OK → results/dip3r_design_20260705.json")
