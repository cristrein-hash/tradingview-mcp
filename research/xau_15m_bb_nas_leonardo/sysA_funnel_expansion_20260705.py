#!/usr/bin/env python3
"""FRENTE 1 — EXPANSÃO DO FUNIL DO SISTEMA A sob exit 3R (2026-07-05, GO Cris).
Objetivo: hit3R 49,1%→>=55% com ~1/sem (N~104) e streak <=5. MÉTODO PRÉ-DECLARADO:
(1) cascata do funil (qual gate mata N) — outcome-blind;
(2) 6 EIXOS de relaxamento pré-declarados (1 gate por eixo, valor único, zero grid):
    X1 sem violência · X2 sem resposta · X3 h1_pos>=0.20 · X4 reclaim_ema_bars<=8 ·
    X5 +RANGE (regime BULL ou RANGE) · X6 sem demanda;
(3) leitura do hit3R da COORTE MARGINAL de cada eixo (os candidatos NOVOS que o eixo adiciona)
    — 6 looks declarados;
(4) REGRA DE COMBINAÇÃO CONGELADA ANTES DA LEITURA: entram na união FINAL apenas eixos cuja coorte
    marginal tiver hit3R >= 49,1% (a semente) E N marginal >= 15; união = A ∪ marginais aprovadas;
(5) painel final duplo + nulls (random mesmo-N do pool BULL+RANGE 500× · year-aware 500×) +
    streak + FN-gate. STATUS: CALIBRAÇÃO (thresholds do A herdados; 6+1 looks nesta rodada).
Universo selado; alvo R3 pré-computado (r3_target_universe). Seed 42."""
import json, random, hashlib, collections
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SB = 0.80
random.seed(42)
CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]
R3 = {}
for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl"):
    d = json.loads(l); R3[d["cj_t"]] = d

def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
G = {
    "regime": lambda r: r["g_v5h"] == "BULL",
    "h1": lambda r: fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33,
    "ema": lambda r: fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3,
    "viol": lambda r: fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3,
    "dem": lambda r: fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1,
    "resp": lambda r: fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0,
    "knife": lambda r: r["g_knife"] == 0,
}
def sysA(r, override=None):
    o = override or {}
    for k, fn in G.items():
        if k in o:
            if not o[k](r): return False
        elif not fn(r): return False
    return True
A = [r for r in U if sysA(r)]
assert len(A) == 53
WEEKS = len({r["g_week"] for r in U})

# (1) cascata do funil
print("=" * 106)
print("EXPANSÃO DO FUNIL — SISTEMA A sob 3R (eixos pré-declarados; coorte marginal; regra congelada)")
print("=" * 106)
print("(1) CASCATA (N que cada gate deixa passar, aplicado sozinho sobre BULL 2132):")
BULL = [r for r in U if r["g_v5h"] == "BULL"]
for k, fn in G.items():
    if k == "regime": continue
    print(f"    só {k:<6}: {sum(1 for r in BULL if fn(r)):>5}")
casc = BULL
for k in ("h1", "ema", "viol", "dem", "resp", "knife"):
    casc = [r for r in casc if G[k](r)]
    print(f"    ...+{k:<6}: {len(casc):>5}")

# (2)+(3) eixos e coortes marginais
AX = {
    "X1_sem_violencia": {"viol": lambda r: True},
    "X2_sem_resposta": {"resp": lambda r: True},
    "X3_h1pos_020": {"h1": lambda r: fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.20},
    "X4_ema_rec8": {"ema": lambda r: fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 8},
    "X5_mais_range": {"regime": lambda r: r["g_v5h"] in ("BULL", "RANGE")},
    "X6_sem_demanda": {"dem": lambda r: True},
}
def panel(rows, tag, show=True):
    n = len(rows)
    if not n:
        if show: print(f"  {tag:<28} vazio")
        return None
    rs = sorted(rows, key=lambda r: r["cj_t"])
    nets = [R3[r["cj_t"]]["net3"] for r in rs]
    hit = sum(1 for r in rs if R3[r["cj_t"]]["R3"] >= 3)
    w = sum(1 for x in nets if x > 0)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {}
    for r, x in zip(rs, nets): yr[r["yr"]] = round(yr.get(r["yr"], 0) + x, 1)
    if show:
        print(f"  {tag:<28} N{n:>4} hit3R {100*hit/n:>5.1f}% NET {sum(nets):>7.1f} DD {dd:>6.1f} stk-{mL} "
              f"| {n/WEEKS:.2f}/sem | anos {yr}")
    return {"n": n, "hit": hit / n, "net": sum(nets), "stk": mL, "dd": dd}
base = panel(A, "A semente (49,1%)")
print("\n(3) COORTES MARGINAIS (looks 1-6 declarados; regra de aprovação: hit>=49,1% E N>=15):")
approved = []
Aset = {r["cj_t"] for r in A}
for nm, ov in AX.items():
    exp = [r for r in U if sysA(r, ov)]
    marg = [r for r in exp if r["cj_t"] not in Aset]
    st = panel(marg, f"marginal {nm}")
    if st and st["hit"] >= 0.491 and st["n"] >= 15:
        approved.append(nm)
        print(f"      → APROVADA pela regra congelada")
print(f"\n(4) eixos aprovados: {approved or 'NENHUM'}")
if approved:
    union = {r["cj_t"]: r for r in A}
    for nm in approved:
        for r in (x for x in U if sysA(x, AX[nm]) and x["cj_t"] not in Aset):
            union[r["cj_t"]] = r
    UN = list(union.values())
    stu = panel(UN, "A EXPANDIDO (união)")
    # nulls
    pool = [r for r in U if r["g_v5h"] in ("BULL", "RANGE")]
    k = stu["n"]
    nd_r = []
    by_yr = collections.defaultdict(list)
    for r in pool: by_yr[r["yr"]].append(r)
    kyr = collections.Counter(r["yr"] for r in UN)
    nd_y = []
    for _ in range(500):
        pick = random.sample(pool, k)
        nd_r.append(sum(R3[r["cj_t"]]["net3"] for r in pick))
        py = [r for y, c in kyr.items() for r in random.sample(by_yr[y], min(c, len(by_yr[y])))]
        nd_y.append(sum(R3[r["cj_t"]]["net3"] for r in py))
    pct = lambda o, d: round(100 * sum(1 for x in d if x < o) / len(d), 1)
    print(f"  nulls união: random pct {pct(stu['net'], nd_r)}% · year-aware pct {pct(stu['net'], nd_y)}%")
    # streak bootstrap por episódio
    rs = sorted(UN, key=lambda r: r["cj_t"])
    eps = []; lastt = None
    for j, r in enumerate(rs):
        if lastt is not None and r["cj_t"] - lastt <= 96 * 900: eps[-1].append(j)
        else: eps.append([j])
        lastt = r["cj_t"]
    nets = [R3[r["cj_t"]]["net3"] for r in rs]
    worst = []
    for _ in range(1000):
        seq = [nets[j] for _ in range(len(eps)) for j in eps[random.randrange(len(eps))]]
        mL = cl = 0
        for x in seq:
            if x <= 0: cl += 1; mL = max(mL, cl)
            else: cl = 0
        worst.append(mL)
    print(f"  streak q95 (bootstrap episódio): {sorted(worst)[950]} · FN gate: hit>=55? {stu['hit']>=0.55} · ~1/sem? {stu['n']/WEEKS:.2f}")
    json.dump({"approved_axes": approved, "union_n": stu["n"], "union_hit": stu["hit"], "union_net": stu["net"],
               "union_stk": stu["stk"], "stk_q95": sorted(worst)[950],
               "nulls": {"random": pct(stu["net"], nd_r), "year": pct(stu["net"], nd_y)}},
              open(HERE / "results" / "sysA_funnel_expansion_20260705.json", "w"), indent=1)
else:
    json.dump({"approved_axes": [], "verdict": "nenhum eixo aprovado pela regra congelada"},
              open(HERE / "results" / "sysA_funnel_expansion_20260705.json", "w"), indent=1)
print("OK → results/sysA_funnel_expansion_20260705.json")
