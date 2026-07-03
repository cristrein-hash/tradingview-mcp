#!/usr/bin/env python3
"""LAB A RODADA 2 — ENTRY REDESIGN (2026-07-03). Prereg: XAU_15M_LONG_LAB_A_ENTRY_GEOMETRY_PREREG_20260703.md
Rodada 1 (execução pós-sinal limit/retest, FAILS) está no git history (c95d711).
Hipóteses P1-P6 congeladas ANTES da execução (síntese do discovery wf_fe1ae2d6-cfe, versão integral em
results/lab_a2_discovery_synthesis.json). Nulls determinísticos (seed 42). SB $0,80 líquido sempre.
LEDGER de variantes da rodada: P1, P2, P3, P4, P5, P6 + 1 tentativa pré-descartada (absorption score,
falhou no scan exploratório do discovery) + nulls (não contam como variantes). Zero grid/varredura."""
import json, math, random, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
SB_USD = 0.80          # round-trip realista (Lab E, COST_ROBUST)
RISK_FLOOR_USD = 6.40  # P1: 8×RT
RISK_FLOOR_ATR = 0.35  # P1
EP_GAP = 96            # barras 15M — cadeia de episódio (P5 herda achado B, congelado)
random.seed(42)

# ---------- engine real (fail-loud) ----------
ns = {"__name__": "engine", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(),
             "engine_substrate4_v5_hourcausal.py", "exec"), ns)
cand, ROWS, PRIMK = ns["cand"], ns["ROWS"], ns["PRIMK"]
letrun, cf_low, f = ns["letrun"], ns["cf_low"], ns["f"]
regime_h, QPOS, QRSI = ns["regime_hourcausal"], ns["QPOS"], ns["QRSI"]
HMAX, RCAP, ema_at = ns["HMAX"], ns["RCAP"], ns["ema_at"]

base_c = sorted([c for c in cand if c["v5h"] != "BEAR"], key=lambda z: z["cj_t"])
assert len(base_c) == 435, f"baseline N={len(base_c)} != 435"
rmap = {r["cj_t"]: r for r in ROWS}

def letrun_from(s, j0, entry, sl, atr):
    """letrun idêntico ao engine, ancorado no bar de fill j0 (horizonte HMAX a partir do fill)."""
    risk = entry - sl
    if risk <= 0: return None
    trail = sl; r1 = False; ex = None; end = min(j0 + HMAX, len(s) - 1)
    for k in range(j0 + 1, end + 1):
        if s[k]["l"] <= trail: ex = trail; break
        if (s[k]["h"] - entry) / risk >= 1: r1 = True
        if r1:
            sw = cf_low(s, k)
            if sw: trail = max(trail, sw - 0.1 * atr)
    if ex is None: ex = s[end]["c"]
    return max(-1.0, min(RCAP, (ex - entry) / risk))

# ---------- JOIN + geometria dos 435 (reprodução fail-loud) ----------
SIG = []
for c in base_c:
    r = rmap[c["cj_t"]]; s = PRIMK[r["block"]]["series"]
    tmap = {b["t"]: i for i, b in enumerate(s)}
    p, cj = tmap[r["t"]], tmap[r["cj_t"]]
    atr = s[p]["atr"] or s[cj]["atr"]
    entry0 = s[cj]["c"]; sl = min(x["l"] for x in s[p:cj + 1]) - 0.1 * atr
    Rre = letrun(s, cj, entry0, sl, atr)
    assert abs(Rre - c["R"]) < 1e-9, f"JOIN fail {c['cj_t']}: {Rre} vs {c['R']}"
    SIG.append({"t": c["cj_t"], "yr": c["yr"], "R0": c["R"], "s": s, "p": p, "cj": cj,
                "atr": atr, "entry0": entry0, "sl": sl, "risk0": entry0 - sl, "row": r})

def net(R, risk): return R - SB_USD / risk
def stats(seq):
    """seq = [(t, yr, Rg, Rn)] cronológico. Painel completo bruto ('g') e líquido-SB ('q')."""
    seq = sorted(seq); n = len(seq)
    if not n: return None
    out = {"N": n}
    for tag, R in (("g", [x[2] for x in seq]), ("q", [x[3] for x in seq])):
        eq = pk = dd = 0.0
        for x in R: eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        mL = mW = cl = cw = 0
        for x in R:
            if x > 0: cw += 1; cl = 0
            else: cl += 1; cw = 0
            mW = max(mW, cw); mL = max(mL, cl)
        w = sum(1 for x in R if x > 0)
        out[tag] = {"sum": sum(R), "wr": 100 * w / n, "avg": sum(R) / n, "dd": dd,
                    "rdd": abs(sum(R) / dd) if dd < 0 else 99, "stkL": mL, "stkW": mW,
                    "run": sum(1 for x in R if x >= 3)}
    out["yrs"] = {y: round(sum(x[3] for x in seq if x[1] == y), 1) for y in (2024, 2025, 2026)}
    mo = {}
    for t, yr, g, q in seq:
        k = dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"); mo[k] = mo.get(k, 0) + q
    out["mo_pos"] = 100 * sum(1 for v in mo.values() if v > 0) / len(mo)
    out["mo_worst"] = min(mo.values())
    return out
def show(tag, st, extra=""):
    if st is None: print(f"{tag:<26} vazio"); return
    G, Q = st["g"], st["q"]
    print(f"{tag:<26} N{st['N']:>4} | BRUTO sum{G['sum']:>7.1f} WR{G['wr']:>5.1f} run{G['run']}"
          f" | NET sum{Q['sum']:>7.1f} WR{Q['wr']:>5.1f} avg{Q['avg']:>6.3f} DD{Q['dd']:>6.1f}"
          f" r/DD{Q['rdd']:>5.2f} stk-{Q['stkL']}/+{Q['stkW']} | yr {st['yrs'][2024]}/{st['yrs'][2025]}/{st['yrs'][2026]}"
          f" | mes+{st['mo_pos']:.0f}% pior{st['mo_worst']:+.1f} {extra}")

BASE_SEQ = [(g["t"], g["yr"], g["R0"], net(g["R0"], g["risk0"])) for g in SIG]
bs = stats(BASE_SEQ)
assert abs(bs["g"]["sum"] - 291.5) < 0.5 and abs(bs["q"]["sum"] - 233.6) < 0.5, \
    f"painel base não reproduz: {bs['g']['sum']:.1f}/{bs['q']['sum']:.1f}"
BASE_RUNNERS = bs["g"]["run"]

# ---------- episódios ----------
eps = []; last_t = None
for i, g in enumerate(SIG):
    if last_t is not None and (g["t"] - last_t) <= EP_GAP * 900: eps[-1].append(i)
    else: eps.append([i])
    last_t = g["t"]
EP_OF = {i: e for e, mem in enumerate(eps) for i in mem}
# cadeia estrita P5: gap<=96b E anterior stopado E flush compartilhado (<=1,0 ATR_prev)
chain_pos = [0] * len(SIG)
for i in range(1, len(SIG)):
    a, b = SIG[i - 1], SIG[i]
    fl_a, fl_b = a["sl"] + 0.1 * a["atr"], b["sl"] + 0.1 * b["atr"]
    if (b["t"] - a["t"]) <= EP_GAP * 900 and a["R0"] <= 0 and abs(fl_b - fl_a) <= 1.0 * a["atr"]:
        chain_pos[i] = chain_pos[i - 1] + 1

def null_p(obs, dist): return sum(1 for d in dist if d >= obs) / len(dist)

def fn_gate(st, kept_runners, costs):
    """GATE FUNDEDNEXT congelado (prereg §5.10)."""
    cm = sorted(costs)[len(costs) // 2] if costs else 9
    ok = {"WR_liq>=50": st["q"]["wr"] >= 50, "streak<=6": st["q"]["stkL"] <= 6,
          "runners>=48": kept_runners >= 48, "sumR_liq>=200": st["q"]["sum"] >= 200,
          "anos+ (2024>=10)": all(st["yrs"][y] > 0 for y in (2024, 2025, 2026)) and st["yrs"][2024] >= 10,
          "costR_med<=0.15": cm <= 0.15}
    return ok, cm

print("=" * 112)
print("LAB A RODADA 2 — ENTRY REDESIGN (P1-P6 pré-registradas)")
print("=" * 112)
show("BASE market@cj", bs, f"runners_g{BASE_RUNNERS}")
okb, cmb = fn_gate(bs, BASE_RUNNERS, [SB_USD / g["risk0"] for g in SIG])
print(f"  FN-gate base: {sum(okb.values())}/6 falha={[k for k, v in okb.items() if not v]} costR_med {cmb:.3f}")

# ---------- STREAK_ANATOMY (passo 0 comum) ----------
print("\n" + "-" * 112 + "\nSTREAK_ANATOMY (passo 0)")
runs = []; cur = []
for i, g in enumerate(SIG):
    if net(g["R0"], g["risk0"]) <= 0: cur.append(i)
    else:
        if len(cur) >= 3: runs.append(cur)
        cur = []
if len(cur) >= 3: runs.append(cur)
n_intra = n_week = n_spread = 0
for run in runs:
    eset = {EP_OF[i] for i in run}
    wk = {dt.datetime.utcfromtimestamp(SIG[i]["t"]).strftime("%G-%V") for i in run}
    span_d = (SIG[run[-1]]["t"] - SIG[run[0]]["t"]) / 86400
    if len(eset) == 1: n_intra += 1
    elif len(wk) <= 2: n_week += 1
    else: n_spread += 1
    print(f"  run len{len(run):>2} eps{len(eset):>2} sem{len(wk):>2} span{span_d:>6.1f}d "
          f"{dt.datetime.utcfromtimestamp(SIG[run[0]]['t']).strftime('%Y-%m-%d')}→"
          f"{dt.datetime.utcfromtimestamp(SIG[run[-1]]['t']).strftime('%Y-%m-%d')}")
conc = (n_intra + n_week) / len(runs) if runs else 0
print(f"  loss-runs>=3: {len(runs)} | intra-episódio {n_intra} · <=2 semanas {n_week} · espalhadas {n_spread}"
      f" → concentração {100*conc:.0f}% (gate P5: >=50%)")
P5_GO = conc >= 0.5

RESULTS = {}

# ---------- P1 — TRIG_DISP_EARLY ----------
print("\n" + "-" * 112 + "\nP1 — TRIG_DISP_EARLY (antecipação p+1/p+2, 3 lentes + piso de risco, fallback cj)")
HAS_OPEN = "o" in SIG[0]["s"][SIG[0]["cj"]]
print(f"  série tem OPEN: {HAS_OPEN}")
def disp_ok(s, j, p, atr, C):
    assert j < p + 3, "anti-look-ahead: decisão precede cj"
    b = s[j]
    if not (b["c"] > s[p]["h"]): return False
    body = (b["c"] - b["o"]) if HAS_OPEN else (b["c"] - s[j - 1]["c"])  # fallback declarado se sem open
    if body < 0.5 * atr: return False
    return b["c"] > ema_at(C, j, 21)
def recomp_gates(s, j, entry, sl, atr):
    """gates recomputáveis na barra de decisão (regime v5h, rsi, pos20, piso). Residual declarado: knife/h1_pos/HTF do snapshot cj."""
    risk = entry - sl
    if risk <= 0 or risk < RISK_FLOOR_USD or risk < RISK_FLOOR_ATR * atr: return False
    if regime_h(s[j]["t"]) == "BEAR": return False
    if (s[j].get("rsi") or 50) < QRSI: return False
    lo20 = min(x["l"] for x in s[max(0, j - 19):j + 1]); hi20 = max(x["h"] for x in s[max(0, j - 19):j + 1])
    return (entry - lo20) / ((hi20 - lo20) or atr) >= QPOS

p1_seq = []; p1_ant = []; p1_costs = []
for g in SIG:
    s, p, cj, atr, sl = g["s"], g["p"], g["cj"], g["atr"], g["sl"]
    C = [b["c"] for b in s]
    fired = None
    for j in (p + 1, p + 2):
        if j >= cj: break
        if disp_ok(s, j, p, atr, C) and recomp_gates(s, j, s[j]["c"], sl, atr):
            fired = j; break
    if fired is not None:
        entry = s[fired]["c"]; risk = entry - sl
        R = letrun_from(s, fired, entry, sl, atr)
        p1_seq.append((s[fired]["t"], g["yr"], R, net(R, risk))); p1_costs.append(SB_USD / risk)
        p1_ant.append((g, R, net(R, risk), net(g["R0"], g["risk0"])))
    else:
        p1_seq.append((g["t"], g["yr"], g["R0"], net(g["R0"], g["risk0"]))); p1_costs.append(SB_USD / g["risk0"])
st1 = stats(p1_seq); kept_run1 = st1["g"]["run"]
# contagem por barra de disparo (para null like-for-like)
fired_bar = []
for g in SIG:
    s, p, cj, atr, sl = g["s"], g["p"], g["cj"], g["atr"], g["sl"]
    C = [b["c"] for b in s]; fb = 0
    for j in (p + 1, p + 2):
        if j < cj and disp_ok(s, j, p, atr, C) and recomp_gates(s, j, s[j]["c"], sl, atr):
            fb = j - p; break
    fired_bar.append(fb)
N1, N2 = fired_bar.count(1), fired_bar.count(2)
show("P1 disp-early", st1, f"antecipadas {len(p1_ant)}/{len(SIG)} ({N1}@p+1/{N2}@p+2)")
d_ant = sum(x[2] - x[3] for x in p1_ant)
print(f"  pareado (antecipadas): ΔNET {d_ant:+.1f}R (base-NET delas {sum(x[3] for x in p1_ant):+.1f} → novo {sum(x[2] for x in p1_ant):+.1f})")
# NULL JUSTO (correção DA rodada 2): like-for-like — mesma mistura N1@p+1/N2@p+2, PISO DE RISCO aplicado
# (null sem piso inflava R por risco minúsculo: mediana +87,8/p=1,000 era ARTEFATO — bug material do DA).
def _elig(g, j):
    risk = g["s"][j]["c"] - g["sl"]
    return risk > 0 and risk >= RISK_FLOOR_USD and risk >= RISK_FLOOR_ATR * g["atr"]
elig1 = [i for i, g in enumerate(SIG) if _elig(g, g["p"] + 1)]
elig2 = [i for i, g in enumerate(SIG) if _elig(g, g["p"] + 2)]
print(f"  elegíveis c/ piso: {len(elig1)}@p+1 · {len(elig2)}@p+2")
nd = []
for _ in range(500):
    pick1 = set(random.sample(elig1, min(N1, len(elig1))))
    pool2 = [i for i in elig2 if i not in pick1]
    pick2 = set(random.sample(pool2, min(N2, len(pool2))))
    tot = 0.0
    for i, g in enumerate(SIG):
        j = g["p"] + 1 if i in pick1 else (g["p"] + 2 if i in pick2 else None)
        if j is not None:
            entry = g["s"][j]["c"]; risk = entry - g["sl"]
            tot += net(letrun_from(g["s"], j, entry, g["sl"], g["atr"]), risk)
        else:
            tot += net(g["R0"], g["risk0"])
    nd.append(tot - bs["q"]["sum"])
p1_p = null_p(st1["q"]["sum"] - bs["q"]["sum"], nd)
print(f"  NULL JUSTO timing-com-piso (500): Δobs {st1['q']['sum']-bs['q']['sum']:+.1f} vs null med {sorted(nd)[250]:+.1f}"
      f" [q05 {sorted(nd)[25]:+.1f} · q95 {sorted(nd)[475]:+.1f}] → p={p1_p:.3f}")
# phantom scan (bound do residual look-ahead): universo fora dos 435
base_ts = {g["t"] for g in SIG}
ph_n = 0; ph_sum = 0.0
for r in ROWS:
    if r["cj_t"] in base_ts or f(r, "swept_prior_low", 0) != 1: continue
    pr = PRIMK.get(r["block"])
    if not pr: continue
    s = pr["series"]; tmap = {b["t"]: i for i, b in enumerate(s)}
    p, cj = tmap.get(r["t"]), tmap.get(r["cj_t"])
    if p is None or cj is None or cj + 2 >= len(s): continue
    atr = s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    C = [b["c"] for b in s]
    for j in (p + 1, p + 2):
        if j >= cj: break
        slj = min(x["l"] for x in s[p:j + 1]) - 0.1 * atr
        if disp_ok(s, j, p, atr, C) and recomp_gates(s, j, s[j]["c"], slj, atr):
            R = letrun_from(s, j, s[j]["c"], slj, atr)
            if R is not None: ph_n += 1; ph_sum += net(R, s[j]["c"] - slj)
            break
print(f"  PHANTOM (residual bound): {ph_n} entradas live-only · sumR_NET {ph_sum:+.1f} → tradeable-lower-bound {st1['q']['sum']+ph_sum:+.1f}")
ok1, cm1 = fn_gate(st1, kept_run1, p1_costs)
p1_kill = d_ant < 0
print(f"  FN-gate: {sum(ok1.values())}/6 falha={[k for k,v in ok1.items() if not v]} costR_med {cm1:.3f} | KILL(pareadoΔ<0)={p1_kill}")
RESULTS["P1"] = {"net": st1["q"]["sum"], "p_null": p1_p, "anticipated": len(p1_ant), "phantom_n": ph_n,
                 "phantom_net": round(ph_sum, 1), "kill": p1_kill, "fn": sum(ok1.values())}

# ---------- P2 — EXEC_STOP_CONT ----------
print("\n" + "-" * 112 + "\nP2 — EXEC_STOP_CONT (buy-stop max(high[p..cj])+0,05ATR, W8, THROUGH $0,40)")
p2_seq = []; p2_miss = []; p2_costs = []; p2_fill = 0; p2_samebar = 0
for g in SIG:
    s, p, cj, atr, sl = g["s"], g["p"], g["cj"], g["atr"], g["sl"]
    stop = max(x["h"] for x in s[p:cj + 1]) + 0.05 * atr
    filled = False
    for k in range(cj + 1, min(cj + 8, len(s) - 1) + 1):
        b = s[k]
        gap_open = HAS_OPEN and b["o"] >= stop
        crossed = gap_open or b["h"] >= stop + 0.40
        if b["l"] <= sl and not crossed: break            # SL primeiro → cancela
        if crossed:
            fill = b["o"] if gap_open else stop
            risk = fill - sl
            if risk <= 0: break
            if b["l"] <= sl: R = -1.0; p2_samebar += 1    # same-bar → conservador
            else: R = letrun_from(s, k, fill, sl, atr)
            p2_seq.append((b["t"], g["yr"], R, net(R, risk))); p2_costs.append(SB_USD / risk)
            filled = True; p2_fill += 1
            break
    if not filled:
        p2_miss.append(g); p2_seq.append((g["t"], g["yr"], 0.0, 0.0))  # cronológico miss=0
st2 = stats(p2_seq); kept_run2 = st2["g"]["run"]
miss_avg = sum(net(m["R0"], m["risk0"]) for m in p2_miss) / len(p2_miss) if p2_miss else 0
show("P2 stop-cont (miss=0)", st2, f"fill {p2_fill}/{len(SIG)} samebar-1R {p2_samebar}")
print(f"  misses {len(p2_miss)}: base-avgR-NET {miss_avg:+.3f} → KILL exige <=0: {'PASS' if miss_avg <= 0 else 'FAIL → DISCARD'}")
nd2 = []; fr = p2_fill / len(SIG)
for _ in range(500):
    tot = sum(net(g["R0"], g["risk0"]) for g in SIG if random.random() < fr)
    nd2.append(tot)
p2_p = null_p(st2["q"]["sum"], nd2)
print(f"  null cancelamento aleatório (500): obs {st2['q']['sum']:+.1f} vs null med {sorted(nd2)[250]:+.1f} → p={p2_p:.3f}")
ok2, cm2 = fn_gate(st2, kept_run2, p2_costs)
p2_kill = miss_avg > 0
print(f"  FN-gate: {sum(ok2.values())}/6 falha={[k for k,v in ok2.items() if not v]} costR_med {cm2:.3f} | KILL={p2_kill}")
RESULTS["P2"] = {"net": st2["q"]["sum"], "fill": p2_fill, "miss_base_avg": round(miss_avg, 3),
                 "p_null": p2_p, "kill": p2_kill, "fn": sum(ok2.values())}

# ---------- SKIPs P3/P4 — helpers ----------
def eval_skip(name, skip_flags):
    kept = [i for i in range(len(SIG)) if not skip_flags[i]]
    cut = [i for i in range(len(SIG)) if skip_flags[i]]
    seq = [(SIG[i]["t"], SIG[i]["yr"], SIG[i]["R0"], net(SIG[i]["R0"], SIG[i]["risk0"])) for i in kept]
    st = stats(seq)
    rk = sum(1 for i in cut if SIG[i]["R0"] >= 4)
    cut_net = sum(net(SIG[i]["R0"], SIG[i]["risk0"]) for i in cut)
    show(name, st, f"cut {len(cut)} (netΔ {-cut_net:+.1f}) runner-kill {rk}")
    nd = []
    for _ in range(500):
        pick = set(random.sample(range(len(SIG)), len(cut)))
        nd.append(sum(net(SIG[i]["R0"], SIG[i]["risk0"]) for i in range(len(SIG)) if i not in pick))
    p_rand = null_p(st["q"]["sum"], nd)
    delta = st["q"]["sum"] - bs["q"]["sum"]; conc_max = 0.0
    if delta > 1e-9:
        for e, mem in enumerate(eps):
            d_e = -sum(net(SIG[i]["R0"], SIG[i]["risk0"]) for i in mem if skip_flags[i])
            conc_max = max(conc_max, d_e / delta)
    print(f"  null cortes aleatórios: p={p_rand:.3f} | leave-episódio: máx {100*conc_max:.0f}% do delta (gate <=15%)")
    return st, {"cut": len(cut), "runner_kill": rk, "p_rand": p_rand, "conc": round(conc_max, 2),
                "net": st["q"]["sum"], "delta": round(delta, 1)}, kept

def perm_null(flags_from, votes, nreps=500):
    obs = sum(net(SIG[i]["R0"], SIG[i]["risk0"]) for i in range(len(SIG)) if not flags_from(votes[i]))
    vv = votes[:]; nd = []
    for _ in range(nreps):
        random.shuffle(vv)
        nd.append(sum(net(SIG[i]["R0"], SIG[i]["risk0"]) for i in range(len(SIG)) if not flags_from(vv[i])))
    return null_p(obs, nd)

# ---------- P3 — SKIP_CEILING ----------
print("\n" + "-" * 112 + "\nP3 — SKIP_CEILING (>=3 de 4 lentes de teto, formato L2)")
sup_vals = sorted(f(r, "n_supply_overhead", 0) for r in ROWS)
q80 = sup_vals[int(0.80 * len(sup_vals))]
def lens3(r):
    return [f(r, "n_supply_overhead", 0) >= q80, f(r, "legpos90", 0) >= 0.75,
            f(r, "h1n_clean_sky_atr", 99) <= 0.35, f(r, "sell_bub_w", 0) >= 1]
UL = [lens3(r) for r in ROWS]
def phi(a, b):
    n11 = sum(1 for x, y in zip(a, b) if x and y); n10 = sum(1 for x, y in zip(a, b) if x and not y)
    n01 = sum(1 for x, y in zip(a, b) if not x and y); n00 = len(a) - n11 - n10 - n01
    den = math.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    return (n11 * n00 - n10 * n01) / den if den else 0
cols = list(zip(*UL)); maxphi = 0.0; pair = None
for i in range(4):
    for j in range(i + 1, 4):
        v = abs(phi(cols[i], cols[j]))
        if v > maxphi: maxphi, pair = v, (i, j)
print(f"  q80(n_supply_overhead)={q80} | pré-check corr: máx|φ|={maxphi:.2f} par{pair} → {'OK' if maxphi < 0.8 else 'SUBSTITUI lente por h1_rsi>=65 (pré-declarada)'}")
if maxphi >= 0.8:
    def lens3(r):
        return [f(r, "n_supply_overhead", 0) >= q80, f(r, "legpos90", 0) >= 0.75,
                f(r, "h1_rsi", 50) >= 65, f(r, "sell_bub_w", 0) >= 1]
votes3 = [sum(lens3(g["row"])) for g in SIG]
uni_v = [sum(l) for l in UL]
print(f"  votos universo(4502): {[uni_v.count(k) for k in range(5)]} | votos 435: {[votes3.count(k) for k in range(5)]}")
flags3 = [v >= 3 for v in votes3]
st3, m3, kept3 = eval_skip("P3 skip-ceiling", flags3)
p3_perm = perm_null(lambda v: v >= 3, votes3)
p3_kill = m3["runner_kill"] >= 1
ok3, cm3 = fn_gate(st3, st3["g"]["run"], [SB_USD / SIG[i]["risk0"] for i in kept3])
print(f"  null permutado: p={p3_perm:.3f} | KILL(runner-kill>=1)={p3_kill} | FN-gate {sum(ok3.values())}/6 falha={[k for k,v in ok3.items() if not v]}")
RESULTS["P3"] = {**m3, "p_perm": p3_perm, "kill": p3_kill, "fn": sum(ok3.values())}

# ---------- P4 — SKIP_CAPX ----------
print("\n" + "-" * 112 + "\nP4 — SKIP_CAPX (cap_score<=1 = fundo sem capitulação legítima)")
print("  LEDGER: 1º score da rodada (absorption, priors de varejo) FALHOU no scan do discovery — conta como tentativa.")
def cap_score(r):
    return (int(f(r, "sell_bub_w", 0) > 0) + int(f(r, "downleg_eff", 0) >= 0.45) +
            int(f(r, "downleg_decel", 9) == 0) + int(f(r, "pullback_depth", 0) >= 0.6) +
            int(f(r, "low_wick", 9) < 0.5))
votes4 = [cap_score(g["row"]) for g in SIG]
uni4 = [cap_score(r) for r in ROWS]
print(f"  cap_score universo: {[uni4.count(k) for k in range(6)]} | 435: {[votes4.count(k) for k in range(6)]}")
by = {}
for g, v in zip(SIG, votes4): by.setdefault(v, []).append(g["R0"])
print("  monotonicidade (score→avgR bruto 435): " + " · ".join(
    f"s{k}:n{len(v)} avg{sum(v)/len(v):+.2f}" for k, v in sorted(by.items())))
lowg = [x for k, v in by.items() if k <= 1 for x in v]; hig = [x for k, v in by.items() if k >= 2 for x in v]
transfer = bool(lowg) and (sum(lowg) / len(lowg)) < (sum(hig) / len(hig) if hig else 0)
flags4 = [v <= 1 for v in votes4]
st4, m4, kept4 = eval_skip("P4 skip-capx", flags4)
p4_perm = perm_null(lambda v: v <= 1, votes4)
p4_kill = (m4["runner_kill"] >= 1) or (not transfer)
ok4, cm4 = fn_gate(st4, st4["g"]["run"], [SB_USD / SIG[i]["risk0"] for i in kept4])
print(f"  null permutado: p={p4_perm:.3f} | transferência: {'PASS' if transfer else 'FAIL'} | KILL={p4_kill} | FN-gate {sum(ok4.values())}/6 falha={[k for k,v in ok4.items() if not v]}")
RESULTS["P4"] = {**m4, "p_perm": p4_perm, "transfer": transfer, "kill": p4_kill, "fn": sum(ok4.values())}

# ---------- P5 — EPISODE_RISK_BUDGET ----------
print("\n" + "-" * 112 + "\nP5 — EPISODE_RISK_BUDGET (0,5/0,3/0,2 por posição na cadeia estrita)")
if not P5_GO:
    print("  STREAK_ANATOMY <50% concentrada → hipótese morre no diagnóstico (negativo registrado; budget NÃO roda).")
    RESULTS["P5"] = {"go": False, "conc": round(conc, 2)}
else:
    W = {0: 0.5, 1: 0.3}
    wts = [W.get(cp, 0.2) for cp in chain_pos]
    print(f"  cadeias estritas: pos0 {chain_pos.count(0)} · pos1 {chain_pos.count(1)} · pos2+ {sum(1 for c in chain_pos if c >= 2)}")
    wseq = [(g["t"], g["yr"], w * g["R0"], w * net(g["R0"], g["risk0"])) for g, w in zip(SIG, wts)]
    st5 = stats(wseq)
    show("P5 budget (R ponderado)", st5)
    def boot(weights, reps=1000):
        out = []
        for _ in range(reps):
            seq = [weights[i] * net(SIG[i]["R0"], SIG[i]["risk0"])
                   for _ in range(len(eps)) for i in eps[random.randrange(len(eps))]]
            eq = pk = dd = 0.0; mL = cl = 0
            for x in seq:
                eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
                if x <= 0: cl += 1; mL = max(mL, cl)
                else: cl = 0
            out.append((mL, dd))
        return out
    bb = boot([1.0] * len(SIG)); b5 = boot(wts)
    q95 = lambda v: sorted(v)[int(0.95 * len(v))]
    print(f"  bootstrap 1000 (blocos episódio): streak q95 base {q95([x[0] for x in bb])} vs budget {q95([x[0] for x in b5])}"
          f" (NOTA DA: streak em CONTAGEM é invariante POR CONSTRUÇÃO — pesos>0 preservam sinal W/L)"
          f" | DD q95 base {q95([-x[1] for x in bb]):.1f} vs budget {q95([-x[1] for x in b5]):.1f}")
    tot_w = sum(wts)
    print(f"  leitura risco-normalizada (a única honesta): R/unidade-alocada base {bs['q']['sum']/len(SIG):.3f}"
          f" vs budget {st5['q']['sum']/tot_w:.3f} | sum/|DDobs| {bs['q']['rdd']:.1f}→{st5['q']['rdd']:.1f}"
          f" | NET absoluto 233,6→{st5['q']['sum']:.1f} ({100*st5['q']['sum']/bs['q']['sum']:.0f}% — relevante p/ target de lucro prop)")
    RESULTS["P5"] = {"go": True, "net_w": round(st5["q"]["sum"], 1), "stk_obs": st5["q"]["stkL"],
                     "boot_stk_q95_base": q95([x[0] for x in bb]), "boot_stk_q95_budget": q95([x[0] for x in b5]),
                     "boot_dd_q95_base": round(q95([-x[1] for x in bb]), 1), "boot_dd_q95_budget": round(q95([-x[1] for x in b5]), 1)}

# ---------- P6 — COMBO ----------
print("\n" + "-" * 112 + "\nP6 — COMBO (composição congelada pré-resultado; zero re-tuning)")
p1_ok = (not p1_kill) and RESULTS["P1"]["net"] >= bs["q"]["sum"] and kept_run1 >= 48
p3_ok = (not p3_kill) and m3["p_rand"] < 0.05 and p3_perm < 0.05 and m3["conc"] <= 0.15 and m3["net"] > bs["q"]["sum"]
p4_ok = (not p4_kill) and m4["p_rand"] < 0.05 and p4_perm < 0.05 and m4["conc"] <= 0.15 and m4["net"] > bs["q"]["sum"]
print(f"  gates individuais: P1 {'PASS' if p1_ok else 'FAIL'} · P3 {'PASS' if p3_ok else 'FAIL'} · P4 {'PASS' if p4_ok else 'FAIL'}")
if not (p1_ok or p3_ok or p4_ok):
    print("  nenhum componente sobrevive → COMBO = base (registrado, não rodado).")
    RESULTS["P6"] = {"ran": False}
else:
    skipU = [(flags3[i] if p3_ok else False) or (flags4[i] if p4_ok else False) for i in range(len(SIG))]
    seq6 = []; costs6 = []
    for i, g in enumerate(SIG):
        if skipU[i]: continue
        if p1_ok: seq6.append(p1_seq[i]); costs6.append(p1_costs[i])
        else: seq6.append((g["t"], g["yr"], g["R0"], net(g["R0"], g["risk0"]))); costs6.append(SB_USD / g["risk0"])
    st6 = stats(seq6)
    show("P6 COMBO", st6, f"skips {sum(skipU)}")
    dP1 = RESULTS["P1"]["net"] - bs["q"]["sum"] if p1_ok else 0
    dSk = (m3["delta"] if p3_ok else 0) + (m4["delta"] if p4_ok else 0)
    inter = st6["q"]["sum"] - bs["q"]["sum"] - dP1 - dSk
    print(f"  reconciliação: base {bs['q']['sum']:.1f} + ΔP1 {dP1:+.1f} + Δskips {dSk:+.1f} + interação {inter:+.1f} = {st6['q']['sum']:.1f}")
    # null combinado JUSTO (correção DA): antecipação like-for-like COM PISO × cortes aleatórios
    nd6 = []
    ncut = sum(skipU)
    for _ in range(500):
        pick_cut = set(random.sample(range(len(SIG)), ncut)) if ncut else set()
        pick1 = set(random.sample(elig1, min(N1, len(elig1)))) if p1_ok else set()
        pool2 = [i for i in elig2 if i not in pick1]
        pick2 = set(random.sample(pool2, min(N2, len(pool2)))) if p1_ok else set()
        tot = 0.0
        for i, g in enumerate(SIG):
            if i in pick_cut: continue
            j = g["p"] + 1 if i in pick1 else (g["p"] + 2 if i in pick2 else None)
            if j is not None:
                entry = g["s"][j]["c"]; risk = entry - g["sl"]
                tot += net(letrun_from(g["s"], j, entry, g["sl"], g["atr"]), risk)
            else:
                tot += net(g["R0"], g["risk0"])
        nd6.append(tot)
    p6_p = null_p(st6["q"]["sum"], nd6)
    ok6, cm6 = fn_gate(st6, st6["g"]["run"], costs6)
    print(f"  null COMBINADO (500): p={p6_p:.3f} | FN-gate {sum(ok6.values())}/6 falha={[k for k,v in ok6.items() if not v]}")
    RESULTS["P6"] = {"ran": True, "net": round(st6["q"]["sum"], 1), "p_null": p6_p, "fn": sum(ok6.values())}

(HERE / "results").mkdir(exist_ok=True)
json.dump(RESULTS, open(HERE / "results" / "lab_a2_results.json", "w"), indent=1)
print("\nOK → results/lab_a2_results.json")
