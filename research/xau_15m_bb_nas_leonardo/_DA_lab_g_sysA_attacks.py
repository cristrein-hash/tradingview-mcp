#!/usr/bin/env python3
"""DA LAB G — ATAQUES 2-10 sobre Sistema A (EMA-SHAKEOUT) e B (PoT-Map v2.1).
Re-implementação independente DO TEXTO das specs + subsample-vs-base435 + seed-sweep do
null context-pool + poder binomial + streak por block-bootstrap + sensibilidade WR/custo +
multiplicidade familiar + frequência (defs de BULL-week) + concorrência de posições.
Só leitura; nada é escrito fora de stdout.
"""
import json, random, math, collections, datetime as dt, statistics as stt
from pathlib import Path

HERE = Path(__file__).parent
U = sorted([json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")], key=lambda r: r["cj_t"])
assert len(U) == 4499
SB = 0.80

def fv(r, k, d=0):
    v = r.get(k)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d

# ---------- re-implementação INDEPENDENTE do texto da spec ----------
def sysA(r):
    return (r["g_v5h"] == "BULL"
            and fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33
            and (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3)
            and (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3)
            and (fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1)
            and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0)
            and r["g_knife"] == 0)

def knife_ok(r): return r["g_knife"] == 0 or r["g_rsi_div"] == 1 or fv(r, "sell_bub_w") >= 4
def pot(r): return fv(r, "reclaim_atr") >= 1.35 and (fv(r, "g_cj_body") >= 0.40 or fv(r, "up_closes_pc") >= 3)
def lenses3(r):
    return [fv(r, "sell_bub_w") >= 4 or r["g_rsi_div"] == 1,
            fv(r, "h1n_choch_up_rec") == 1 or fv(r, "nas_long_16") >= 1,
            fv(r, "h1n_in_demand") == 1 or fv(r, "htf_demand_confluence") == 1]
def sysB_raw(r):
    if r["g_v5h"] == "BEAR": return False
    k = 2 if r["g_v5h"] == "RANGE" else 1
    need = k + (1 if r["g_regime_flip5d"] else 0)
    if r["g_v5h"] == "RANGE":
        return (pot(r) and knife_ok(r) and r["g_box96"] <= 0.60
                and fv(r, "downleg_eff") <= 0.33 and sum(lenses3(r)) >= need)
    return (pot(r) and knife_ok(r) and fv(r, "h1n_trend") == 1 and fv(r, "h4n_trend") == 1
            and (r["g_ema21_dist"] <= 0.20 or fv(r, "in_demand") == 1)
            and sum(lenses3(r)) >= need)
def day_cap(rows, cap=2):
    out, c = [], collections.Counter()
    for r in rows:
        d = r["cj_t"] // 86400
        if c[d] < cap: c[d] += 1; out.append(r)
    return out

def net_of(r, cost=SB): return r["g_R"] - cost / r["g_risk"]

def panel(rows, cost=SB):
    rows = sorted(rows, key=lambda r: r["cj_t"]); n = len(rows)
    if not n: return None
    out = {"N": n}
    for tag, R in (("g", [r["g_R"] for r in rows]), ("q", [net_of(r, cost) for r in rows])):
        eq = pk = dd = 0.0; mL = cl = 0
        for x in R:
            eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
            if x > 0: cl = 0
            else: cl += 1
            mL = max(mL, cl)
        w = sum(1 for x in R if x > 0)
        out[tag] = dict(sum=round(sum(R), 1), wr=round(100 * w / n, 1), avg=round(sum(R) / n, 3),
                        dd=round(dd, 1), stk=mL, wins=w)
    out["yrs"] = {y: (sum(1 for r in rows if r["yr"] == y),
                      round(sum(net_of(r, cost) for r in rows if r["yr"] == y), 1)) for y in (2024, 2025, 2026)}
    return out

def show(nm, s):
    if s is None: print(f"{nm}: N=0"); return
    print(f"{nm:<28} N{s['N']:>3} | bruto WR {s['g']['wr']:>5.1f} sum {s['g']['sum']:>6.1f} DD {s['g']['dd']:>6.1f} stk-{s['g']['stk']}"
          f" | liq WR {s['q']['wr']:>5.1f} NET {s['q']['sum']:>6.1f} avg {s['q']['avg']:>6.3f} DD {s['q']['dd']:>6.1f} stk-{s['q']['stk']}"
          f" | anos(N,net) {s['yrs']}")

A = [r for r in U if sysA(r)]
B = day_cap([r for r in U if sysB_raw(r)], 2)
Bp = day_cap([r for r in U if r["g_v5h"] == "BULL" and sysB_raw(r)], 2)

print("=" * 118)
print("ATAQUE 9 — RE-IMPLEMENTAÇÃO INDEPENDENTE DO TEXTO DA SPEC")
stA = panel(A); stB = panel(B); stBp = panel(Bp)
show("A EMA-SHAKEOUT (re-impl DA)", stA)
show("B PoT-Map v2.1 (re-impl DA)", stB)
show("B' BULL-only (re-impl DA)", stBp)
okA = stA["N"] == 53 and abs(stA["g"]["sum"] - 29.8) < 0.05 and stA["g"]["wr"] == 62.3 and abs(stA["q"]["sum"] - 25.9) < 0.05
okB = stB["N"] == 182 and abs(stB["q"]["sum"] - 33.9) < 0.05
okBp = stBp["N"] == 127 and abs(stBp["q"]["sum"] - 36.8) < 0.05
print(f"reprodução vs registrado: A {'PASS' if okA else 'FAIL'} · B {'PASS' if okB else 'FAIL'} · B' {'PASS' if okBp else 'FAIL'}")

# ---------- ATAQUE 2: A = subsample da base435? ----------
print("\n" + "=" * 118)
print("ATAQUE 2 — A vs base435 (32 in / 21 out)")
Ain = [r for r in A if r["g_in_base435"] == 1]
Aout = [r for r in A if r["g_in_base435"] == 0]
show("A ∩ base435 (32)", panel(Ain))
show("A fora da base435 (21)", panel(Aout))
base = [r for r in U if r["g_in_base435"] == 1]
show("base435 inteira (ref)", panel(base))
base_notA = [r for r in base if not sysA(r)]
show("base435 SEM os picks de A", panel(base_notA))
# os 21 novos: de onde vêm? qual gate da base eles falham?
gates = {"swept_prior_low!=1": lambda r: fv(r, "swept_prior_low") != 1,
         "h4n/h1n trend": lambda r: not (fv(r, "h4n_trend") == 1 and fv(r, "h1n_trend") == 1),
         "h1_pos<0.44": lambda r: fv(r, "h1_pos", 0.5) < 0.44}
for g, f_ in gates.items():
    print(f"  21 fora-da-base falhando gate '{g}': {sum(1 for r in Aout if f_(r))}")

# ---------- ATAQUE 3: seed-sweep do null context-pool ----------
print("\n" + "=" * 118)
print("ATAQUE 3 — SEED-SWEEP context-pool null de A (kill: >=90)")
poolA = [r for r in U if r["g_v5h"] == "BULL" and r["g_knife"] == 0
         and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0)]
obsA = stA["q"]["sum"]
poolA_net = [net_of(r) for r in poolA]
print(f"  poolA N={len(poolA)} · avg_net={stt.mean(poolA_net):+.4f} · WR_net={100*sum(1 for x in poolA_net if x>0)/len(poolA_net):.1f}"
      f" · obs A avg_net={obsA/53:+.4f}")
pcts = []
for seed in (1, 2, 3, 7, 11, 42, 123, 777, 2026, 20260703):
    rng = random.Random(seed)
    dist = [sum(net_of(r) for r in rng.sample(poolA, 53)) for _ in range(2000)]
    p = 100 * sum(1 for d in dist if d < obsA) / len(dist)
    pcts.append(p)
print(f"  percentis @2000 reps x 10 seeds: {[round(p,1) for p in pcts]}")
print(f"  media {stt.mean(pcts):.1f} · min {min(pcts):.1f} · max {max(pcts):.1f} · seeds >=90: {sum(1 for p in pcts if p>=90)}/10")
# null exato via CLT-check + null com pool endurecido (todas as condições de A menos uma lente por vez)
conds = {
    "h1_trend&pos": lambda r: fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33,
    "ema21_shakeout": lambda r: (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3),
    "violence": lambda r: (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3),
    "demand": lambda r: (fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1),
}
rng = random.Random(42)
for drop in conds:
    pool2 = [r for r in poolA if all(f_(r) for k2, f_ in conds.items() if k2 != drop)]
    if len(pool2) <= 60:
        print(f"  pool endurecido (drop {drop}): N={len(pool2)} — pequeno demais p/ null"); continue
    dist = [sum(net_of(r) for r in rng.sample(pool2, 53)) for _ in range(2000)]
    p = 100 * sum(1 for d in dist if d < obsA) / len(dist)
    print(f"  null pool endurecido (todas condições MENOS {drop}): N={len(pool2)} avg_net {stt.mean(net_of(r) for r in pool2):+.4f} → percentil {p:.1f}")

# ---------- ATAQUE 4: poder binomial de N53 ----------
print("\n" + "=" * 118)
print("ATAQUE 4 — BINOMIAL honesto (N=53)")
def binom_tail(n, k, p):  # P(X>=k)
    s = 0.0
    for i in range(k, n + 1):
        s += math.comb(n, i) * p**i * (1 - p)**(n - i)
    return s
wg, wq = stA["g"]["wins"], stA["q"]["wins"]
poolA_wr_g = sum(1 for r in poolA if r["g_R"] > 0) / len(poolA)
bull = [r for r in U if r["g_v5h"] == "BULL"]
bull_wr = sum(1 for r in bull if r["g_R"] > 0) / len(bull)
base_wr = sum(1 for r in base if r["g_R"] > 0) / len(base)
se = math.sqrt(0.5 * 0.5 / 53)
print(f"  se_WR(N53, p=.5) = {100*se:.1f}pp · IC95 do WR bruto 62.3: [{62.3-196*se:.1f}, {62.3+196*se:.1f}]")
for lbl, p0 in (("p=0.50", .5), (f"p=WR poolA bruto {100*poolA_wr_g:.1f}", poolA_wr_g),
                (f"p=WR BULL-pool {100*bull_wr:.1f}", bull_wr), (f"p=WR base435 {100*base_wr:.1f}", base_wr)):
    print(f"  P(X>={wg}/53 | {lbl}) = {binom_tail(53, wg, p0):.3f}   (bruto)")
print(f"  P(X>={wq}/53 | p=0.50) = {binom_tail(53, wq, .5):.3f}   (liq)")

# ---------- ATAQUE 5: streak — block bootstrap por cluster (<4h) ----------
print("\n" + "=" * 118)
print("ATAQUE 5 — P(streak<=-7): permutação vs block-bootstrap por cluster")
seqA = sorted(A, key=lambda r: r["cj_t"])
netsA = [net_of(r) for r in seqA]
def max_lrun(v):
    m = c = 0
    for x in v:
        c = c + 1 if x <= 0 else 0; m = max(m, c)
    return m
rng = random.Random(42)
perm = [max_lrun(rng.sample(netsA, len(netsA))) for _ in range(20000)]
print(f"  permutação total (20000x): P(>=7) = {100*sum(1 for w in perm if w>=7)/len(perm):.1f}% · P(>=5) = {100*sum(1 for w in perm if w>=5)/len(perm):.1f}%")
# clusters <4h
cl = []
last = None
for r in seqA:
    if last is not None and r["cj_t"] - last <= 4 * 3600: cl[-1].append(net_of(r))
    else: cl.append([net_of(r)])
    last = r["cj_t"]
print(f"  A: {len(cl)} clusters (<4h) de N53 · tamanhos {sorted(collections.Counter(len(c) for c in cl).items())}")
bb = []
for _ in range(20000):
    picks = [rng.choice(cl) for _ in range(len(cl))]
    flat = [x for c in picks for x in c]
    bb.append(max_lrun(flat))
print(f"  block-bootstrap por cluster (20000x): P(>=7) = {100*sum(1 for w in bb if w>=7)/len(bb):.1f}% · P(>=5) = {100*sum(1 for w in bb if w>=5)/len(bb):.1f}%")
# incerteza do WR embutida: p ~ Beta(wins+1, losses+1), 53 iid
byes = []
for _ in range(20000):
    p_loss = 1 - random.betavariate(wq + 1, 53 - wq + 1)
    c = m = 0
    for _ in range(53):
        if rng.random() < p_loss: c += 1; m = max(m, c)
        else: c = 0
    byes.append(m)
print(f"  bayes (incerteza do WR, iid): P(>=7) = {100*sum(1 for w in byes if w>=7)/len(byes):.1f}% · P(>=5) = {100*sum(1 for w in byes if w>=5)/len(byes):.1f}%")
for p0 in (0.50, 0.55, 0.604):
    pl = 1 - p0
    sim = []
    for _ in range(10000):
        c = m = 0
        for _ in range(53):
            if rng.random() < pl: c += 1; m = max(m, c)
            else: c = 0
        sim.append(m)
    print(f"  P(streak<=-7 em 53 trades | WR verdadeiro {100*p0:.1f}) = {100*sum(1 for w in sim if w>=7)/len(sim):.1f}%")

# ---------- ATAQUE 6: fragilidade de convexidade / custo ----------
print("\n" + "=" * 118)
print("ATAQUE 6 — sensibilidade a WR e custo")
show("A com custo SC $1.50", panel(A, cost=1.50))
wins_sorted = sorted([net_of(r) for r in seqA if net_of(r) > 0])
tot = sum(netsA)
cum = tot; k = 0
for w in wins_sorted:
    cum -= (w + 1.0); k += 1   # win w vira loss -1 (líquida aprox)
    if cum <= 0: break
print(f"  NET 25.9: flips de wins marginais->loss(-1) até NET<=0: {k} flips = {100*k/53:.1f}pp de WR (WR_liq 60.4 -> {round(100*(stA['q']['wins']-k)/53,1)})")
bigw = sorted([net_of(r) for r in seqA], reverse=True)
print(f"  top-3 trades = {sum(bigw[:3]):.1f}R = {100*sum(bigw[:3])/tot:.0f}% do NET · sem top-3: {tot-sum(bigw[:3]):.1f}")

# ---------- ATAQUE 7: multiplicidade familiar (~18 olhadas) ----------
print("\n" + "=" * 118)
print("ATAQUE 7 — max-of-family sob H0")
for fam in (8, 12, 18):
    print(f"  P(max de {fam} olhadas independentes >= percentil 91) = {100*(1-0.91**fam):.1f}%")
print(f"  percentil individual necessário p/ FWE 5% com 18 olhadas: {100*0.95**(1/18):.2f}%")
print(f"  percentil individual necessário p/ FWE 20% com 18 olhadas: {100*0.80**(1/18):.2f}%")

# ---------- ATAQUE 8/B: amputação + célula RANGE ----------
print("\n" + "=" * 118)
print("ATAQUE 8 — B: célula RANGE e amputação")
Brange = [r for r in B if r["g_v5h"] == "RANGE"]
show("B célula RANGE", panel(Brange))
print(f"  kill-criteria 'RANGE avg_liq<0 com N>=40': N={len(Brange)} avg_liq={stt.mean(net_of(r) for r in Brange):+.3f} → amputação {'LEGÍTIMA' if len(Brange)>=40 and sum(net_of(r) for r in Brange)<0 else 'NÃO cumpre critério'}")

# ---------- ATAQUE 10: definição de BULL-week ----------
print("\n" + "=" * 118)
print("ATAQUE 10 — frequência: defs de BULL-week")
wk_any = collections.defaultdict(set)
for r in U: wk_any[r["g_v5h"]].add(r["g_week"])
wkc = collections.defaultdict(collections.Counter)
for r in U: wkc[r["g_week"]][r["g_v5h"]] += 1
major = collections.Counter(c.most_common(1)[0][0] for c in wkc.values())
aw = collections.Counter(r["g_week"] for r in A)
print(f"  def EXEC (semana com >=1 candidato do regime): BULL-weeks = {len(wk_any['BULL'])} → {len(A)/len(wk_any['BULL']):.2f}/sem")
print(f"  def DESIGNERS (regime majoritário da semana):   BULL-weeks = {major['BULL']} → {len(A)/major['BULL']:.2f}/sem")
print(f"  semanas ativas de A: {len(aw)} · max/semana {max(aw.values())} · semanas com >3: {sum(1 for v in aw.values() if v>3)}")

# ---------- EXTRA: concorrência de posições (episódio) ----------
print("\n" + "=" * 118)
print("EXTRA — concorrência de posições em A (let-run até 480 bars)")
ns = {"__name__": "engine", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "engine", "exec"), ns)
PRIMK = ns["PRIMK"]; cf_low = ns["cf_low"]
def letrun_exit_idx(s, cj, entry, sl, atr, HMAX=480):
    risk = entry - sl; trail = sl; r1 = False; end = min(cj + HMAX, len(s) - 1)
    for k in range(cj + 1, end + 1):
        if s[k]["l"] <= trail: return k
        if (s[k]["h"] - entry) / risk >= 1: r1 = True
        if r1:
            sw = cf_low(s, k)
            if sw: trail = max(trail, sw - 0.1 * atr)
    return end
open_until = 0; overl = 0; durations = []
for r in seqA:
    s = PRIMK[r["block"]]["series"]; tmap = {b["t"]: i for i, b in enumerate(s)}
    cj = tmap[r["cj_t"]]
    ex = letrun_exit_idx(s, cj, r["g_entry"], r["g_sl"], r["g_atr"])
    exit_t = s[ex]["t"]
    durations.append((exit_t - r["cj_t"]) / 3600)
    if r["cj_t"] < open_until: overl += 1
    open_until = max(open_until, exit_t)
print(f"  duração mediana {stt.median(durations):.1f}h · {overl}/53 entradas ocorrem com posição anterior AINDA ABERTA")
