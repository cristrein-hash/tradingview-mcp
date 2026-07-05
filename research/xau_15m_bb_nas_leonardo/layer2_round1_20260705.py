#!/usr/bin/env python3
"""LAYER 2 — RONDA 1 pré-declarada: PULLBACK-TO-DEMAND (2026-07-05).
Do mapa do gap: 52/56 fundos perdidos vivem SOBRE demanda; cascata mediana 0-2 (dips de pullback,
não capitulação); veto macro-leg enviesado contra BULL (perna jovem por construção perto de máximas).

UNIVERSO L2 (complemento declarado da CASCEX): candidatos fractais com cascata<=3 (o que a CASCEX
NÃO cobre), regime v5h != BEAR de idade>=60d... simplificação causal: v5h qualquer (regime entra
como lente), EXCLUÍDOS os que satisfazem a regra CASCEX completa (sem dupla contagem de layer).
BASE ESTRUTURAL (do mapa, 2 condições): EM DEMANDA (in_demand==1 OU dist_demand_atr<=0,5) E
reclaim_atr>=1,5 (virada com força — 43/56 dos perdidos têm >=1,4).
LEDGER DE LENTES (8, declaradas do mapa + rondas validadas; singles + pares, FDR q=0,10 como v2):
  L1 rsi1h<=42 · L2 rsi1h<=55 (relaxada: mediana dos perdidos ~46) · L3 legpos60<=0.10 ·
  L4 cascata>=1 (alguma quebra) · L5 choch_up_rec (SMC known_at) · L6 v5h==BULL ·
  L7 pullback_depth>=0.5 · L8 swept_prior_low==1
MÉTRICAS (dois objetivos): hit-3R vs breakeven 25% + NET3 + recall dos 56 fundos GT perdidos.
Null: bootstrap subconjuntos do universo L2 (2000×) por grupo + FDR. Painel completo p/ finalistas
(hit>=40% & N>=40 & FDR)."""
import json, bisect, random, hashlib, math
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])   # U, R3, S, TS, CTX, POCKET, _ml, cascade, fv, macro_leg
GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GT.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
gt = json.load(open(GT))
gap = json.load(open(HERE / "results" / "layer2_gap_map_20260705.json"))
MISSED_FT = sorted(r["ft"] for r in gap["missed_rows"])

for u in U:
    u["_casc"] = None
def casc_of(u):
    if u["_casc"] is None:
        u["_casc"] = cascade(u["cj_t"])
    return u["_casc"]

def is_cascex_member(u):
    if casc_of(u) < 4:
        return False
    if not (fv(u, "reclaim_atr", 0) >= 1.5 and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)
            and fv(u, "h1_rsi", 99) <= 42):
        return False
    ml = macro_leg(u["cj_t"])
    return ml["vel"] < 0.10 and ml["recent_frac"] < 0.5

# universo L2: base estrutural, complemento da CASCEX
L2 = [u for u in U if u["cj_t"] in R3
      and (fv(u, "in_demand", 0) == 1 or fv(u, "dist_demand_atr", 9) <= 0.5)
      and fv(u, "reclaim_atr", 0) >= 1.5
      and casc_of(u) <= 3
      and not is_cascex_member(u)]
WEEKS = len({u["g_week"] for u in U})

def recall_of(rows):
    ts = sorted(u["cj_t"] for u in rows)
    r = 0
    for ft in MISSED_FT:
        j = bisect.bisect_left(ts, ft - 8 * 3600)
        if j < len(ts) and ts[j] <= ft + 8 * 3600:
            r += 1
    return r

H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in L2]
base = sum(H0) / len(H0)
print(f"UNIVERSO L2 (demanda & reclaim>=1,5 & cascata<=3, ex-CASCEX): N{len(L2)} · "
      f"hit-3R base {100*base:.1f}% (breakeven 25%) · recall GT-perdidos {recall_of(L2)}/56 · {len(L2)/WEEKS:.2f}/sem")

LENS = {
    "L1_rsi1h<=42": lambda u: fv(u, "h1_rsi", 99) <= 42,
    "L2_rsi1h<=55": lambda u: fv(u, "h1_rsi", 99) <= 55,
    "L3_legbase": lambda u: fv(u, "legpos60", 9) <= 0.10,
    "L4_casc>=1": lambda u: casc_of(u) >= 1,
    "L5_choch_up": lambda u: u.get("h1n_choch_up_rec", 0) or 0,   # placeholder se não existir
    "L6_bull": lambda u: u.get("g_v5h") == "BULL",
    "L7_deep_pull": lambda u: fv(u, "pullback_depth", 0) >= 0.5,
    "L8_swept": lambda u: fv(u, "swept_prior_low", 0) == 1,
}
# L5: usa SMC choch_up recente real (recomputado como nos labs anteriores)
EVsrc = None
def choch_up_recent(cj):
    # reusa 'events' do exec (smc tokens) se existir no namespace do macro_leg src? não existe lá.
    return None
# fallback: h4n_choch_up_rec do lab_g (causal, barra HTF fechada)
LENS["L5_choch_up"] = lambda u: fv(u, "h4n_choch_up_rec", 0) >= 1

groups = {}
for nm, fn in LENS.items():
    groups[frozenset([nm])] = [u for u in L2 if fn(u)]
K = list(LENS)
for i in range(len(K)):
    for j in range(i + 1, len(K)):
        groups[frozenset([K[i], K[j]])] = [u for u in L2 if LENS[K[i]](u) and LENS[K[j]](u)]
groups = {fs: g for fs, g in groups.items() if len(g) >= 40}
random.seed(17)
stats = []
for fs, g in groups.items():
    hs = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in g]
    net = sum(R3[u["cj_t"]]["net3"] for u in g)
    obs = sum(hs) / len(hs)
    ge = 0
    for _ in range(2000):
        if sum(random.sample(H0, len(g))) / len(g) >= obs:
            ge += 1
    stats.append((fs, len(g), obs, net, recall_of(g), ge / 2000))
m = len(stats); stats.sort(key=lambda x: x[5])
fdr = set()
for rank, (fs, n, obs, net, rec, p) in enumerate(stats, 1):
    if p <= 0.10 * rank / m:
        fdr.add(fs)
print(f"ledger {m} grupos · FDR q=0,10 → {len(fdr)} significativos vs base do universo L2")
print(f"{'grupo':<28} {'N':>5} {'hit%':>6} {'NET3':>8} {'recallGT':>8} {'/sem':>5} {'P':>7}")
stats.sort(key=lambda x: -x[2])
for fs, n, obs, net, rec, p in stats[:16]:
    tag = "&".join(sorted(fs))
    print(f"{tag:<28} {n:>5} {100*obs:>5.1f}% {net:>+8.1f} {rec:>5}/56 {n/WEEKS:>5.2f} {p:>7.4f}"
          f"{'  <<< FDR' if fs in fdr else ''}")
json.dump({"universe_n": len(L2), "base_hit": round(base, 3), "recall_universe": recall_of(L2),
           "top": [{"g": "&".join(sorted(fs)), "n": n, "hit": round(o, 3), "net3": round(float(net), 1),
                    "recall": rec, "p": p, "fdr": fs in fdr} for fs, n, o, net, rec, p in stats[:20]]},
          open(HERE / "results" / "layer2_round1_20260705.json", "w"), indent=1)
print("OK → results/layer2_round1_20260705.json")
