#!/usr/bin/env python3
"""ARQUÉTIPO FUNDO-GENUÍNO convergente (2026-07-05) — congelado das MEDIANAS MON+FORTE (não best-of):
pullback profundo à base da perna + abaixo das EMAs + varredura funda + reclaim forte/rápido, regime
!=BEAR, sem faca. Mede: precisão-MF (lift), hit-3R (árbitro), recall, freq, streak. Nulls random +
year. N pequeno = CALIBRAÇÃO (canon). Thresholds = ponto médio MF↔resto das medianas, declarados."""
import json, hashlib, random, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
SB = 0.80; random.seed(42)
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
WEEKS = len({r["g_week"] for r in U})
MF = set(r["cj_t"] for r in U if fv(r, "is_monforte") == 1)
base = len(MF) / len(U)
# 6 lentes do arquétipo (thresholds entre mediana MF e resto, congelados)
LENS = {
 "box96<=0.45": lambda r: fv(r, "g_box96", .5) <= 0.45,
 "ema21<=0.0": lambda r: fv(r, "g_ema21_dist", 9) <= 0.0,
 "legpos60<=0.2": lambda r: fv(r, "legpos60", 1) <= 0.2,
 "sweep>=0.7": lambda r: fv(r, "g_sweep_depth", 0) >= 0.7,
 "reclaim>=1.8": lambda r: fv(r, "reclaim_atr", 0) >= 1.8,
 "rec_speed>=0.6": lambda r: fv(r, "g_rec_speed", 0) >= 0.6,
}
def votes(r): return sum(1 for fn in LENS.values() if fn(r))
NB = [r for r in U if r["g_v5h"] != "BEAR" and r["g_knife"] == 0]
def panel(rows, tag):
    n = len(rows)
    if not n: print(f"  {tag:<20} vazio"); return None
    rs = sorted(rows, key=lambda r: r["cj_t"]); nets = [R3[r["cj_t"]]["net3"] for r in rs]
    h = sum(1 for r in rs if R3[r["cj_t"]]["R3"] >= 3); w = sum(1 for x in nets if x > 0)
    mfin = sum(1 for r in rs if r["cj_t"] in MF)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {}
    for r, x in zip(rs, nets): yr[r["yr"]] = round(yr.get(r["yr"], 0) + x, 1)
    print(f"  {tag:<20} N{n:>3} hit3R {100*h/n:>5.1f}% WR {100*w/n:>5.1f}% NET {sum(nets):>6.1f} DD {dd:>6.1f} "
          f"stk-{mL} | {n/WEEKS:.2f}/sem | MF {mfin}/{len(MF)} prec {100*mfin/n:.0f}% | {yr}")
    return {"n": n, "hit": h / n, "net": sum(nets), "stk": mL, "mf": mfin}
print("=" * 104)
print("ARQUÉTIPO FUNDO-GENUÍNO convergente (mira MON+FORTE; árbitro hit-3R). base-rate MF %.2f%%" % (100 * base))
print("=" * 104)
res = {}
for k in (3, 4, 5, 6):
    keep = [r for r in NB if votes(r) >= k]
    st = panel(keep, f">={k}/6 lentes")
    if st: res[k] = st
# nulls para a melhor convergência viável (maior hit com N>=15 e ~<=2/sem)
viable = [(k, s) for k, s in res.items() if s["n"] >= 15]
if viable:
    kbest, sb = max(viable, key=lambda ks: ks[1]["hit"])
    keep = [r for r in NB if votes(r) >= kbest]; kk = len(keep)
    pool = NB; nd = []; hn = []
    by = collections.defaultdict(list)
    for r in pool: by[r["yr"]].append(r)
    kyr = collections.Counter(r["yr"] for r in keep); nd_y = []
    for _ in range(500):
        s = random.sample(pool, kk)
        nd.append(sum(R3[r["cj_t"]]["net3"] for r in s))
        hn.append(sum(1 for r in s if R3[r["cj_t"]]["R3"] >= 3) / kk)
        py = [r for y, c in kyr.items() for r in random.sample(by[y], min(c, len(by[y])))]
        nd_y.append(sum(R3[r["cj_t"]]["net3"] for r in py))
    pct = lambda o, d: round(100 * sum(1 for x in d if x < o) / len(d), 1)
    print(f"\nNULLS p/ >={kbest}/6 (hit {100*sb['hit']:.1f}%): árbitro hit3R vs null méd {100*sum(hn)/len(hn):.1f}% "
          f"q95 {100*sorted(hn)[475]:.1f}% → pct {pct(sb['hit'], hn)}% · NET random pct {pct(sb['net'], nd)}% year {pct(sb['net'], nd_y)}%")
    json.dump({"lens": list(LENS), "k": kbest, "N": kk, "hit3R": sb["hit"], "net": sb["net"], "stk": sb["stk"],
               "mf_recall": sb["mf"], "per_week": kk / WEEKS,
               "null_hit_pct": pct(sb["hit"], hn), "members_cjt": [r["cj_t"] for r in keep]},
              open(HERE / "results" / "deepdip_convergence_20260705.json", "w"), indent=1)
print("OK → results/deepdip_convergence_20260705.json")
