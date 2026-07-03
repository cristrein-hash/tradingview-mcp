#!/usr/bin/env python3
"""LAB F — EPISODE RISK / STREAK / DD / WR (2026-07-03).
Prereg: docs/architecture/XAU_15M_LONG_LAB_F_EPISODE_RISK_STREAK_DD_WR_PREREG_20260703.md
Discovery: workflow wf_7e18ae96-186 (7 agentes) — 17 exigências de execução (D1-D17) implementadas:
exit materializado (D1), estado sequencial só atualiza no EXIT realizado (D2), cooldown ancorado no
exit da loss (D3), F4 chain_pos causal (D4), skip não atualiza estado (D5), dual-baseline com topologia
recomputada por linha (D6), F8 por re-simulação (D7/D8), nulls random-drop E episode-aware (D9),
Bonferroni informal α≈0,004 (D10), FN-proxy com disclosure de concorrência (D11), F5 por exit-time com
bounds entry-time (D12), outputs pequenos (D13), máquina de estados real em cascata (D14), F4 nunca
edge (D15), runner-kill columns fixas + leave-episódio (D16), proibições D17.
Configs CONGELADAS (13): F1 cd8/cd24/cd96 · F2 max1c/max2c/max2day · F3 br2/br3 · F4 sizing 1/.5/.25 ·
F5 daily-3R/weekly-5R · F8a/F8b. Ledger integral, zero varredura. Seed 42 determinístico."""
import csv, json, math, random, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
SB = 0.80
RISK_FLOOR_USD, RISK_FLOOR_ATR = 6.40, 0.35   # P1 (linha 2)
BAR = 900
random.seed(42)

ns = {"__name__": "engine", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "engine", "exec"), ns)
cand, ROWS, PRIMK = ns["cand"], ns["ROWS"], ns["PRIMK"]
cf_low, f, regime_h = ns["cf_low"], ns["f"], ns["regime_hourcausal"]
QPOS, QRSI, HMAX, RCAP, ema_at = ns["QPOS"], ns["QRSI"], ns["HMAX"], ns["RCAP"], ns["ema_at"]

def letrun_ext(s, j0, entry, sl, atr):
    """letrun do engine, instrumentado: retorna (R, exit_k). Idêntico em R (assert D1)."""
    risk = entry - sl
    if risk <= 0: return None, None
    trail = sl; r1 = False; end = min(j0 + HMAX, len(s) - 1)
    for k in range(j0 + 1, end + 1):
        if s[k]["l"] <= trail: return max(-1.0, min(RCAP, (trail - entry) / risk)), k
        if (s[k]["h"] - entry) / risk >= 1: r1 = True
        if r1:
            sw = cf_low(s, k)
            if sw: trail = max(trail, sw - 0.1 * atr)
    return max(-1.0, min(RCAP, (s[end]["c"] - entry) / risk)), end

base_c = sorted([c for c in cand if c["v5h"] != "BEAR"], key=lambda z: z["cj_t"])
assert len(base_c) == 435
rmap = {r["cj_t"]: r for r in ROWS}

def build_lines():
    """Duas linhas (D6): BASE (entry@cj) e P1 (disp-early do Lab A r2, fallback cj). Topologia própria."""
    lines = {"BASE": [], "P1": []}
    for c in base_c:
        r = rmap[c["cj_t"]]; s = PRIMK[r["block"]]["series"]
        tmap = {b["t"]: i for i, b in enumerate(s)}
        p, cj = tmap[r["t"]], tmap[r["cj_t"]]
        atr = s[p]["atr"] or s[cj]["atr"]
        sl = min(x["l"] for x in s[p:cj + 1]) - 0.1 * atr
        entry0 = s[cj]["c"]
        R0, ek0 = letrun_ext(s, cj, entry0, sl, atr)
        assert abs(R0 - c["R"]) < 1e-9, f"D1 fail {c['cj_t']}"
        common = dict(s=s, p=p, cj=cj, atr=atr, sl=sl, yr=c["yr"], flush=sl + 0.1 * atr)
        lines["BASE"].append(dict(common, j0=cj, t=s[cj]["t"], entry=entry0, risk=entry0 - sl,
                                  R=R0, exit_k=ek0, exit_t=s[ek0]["t"]))
        # P1: disp p+1/p+2 (3 lentes) + gates recomputáveis + piso (Lab A r2, congelado)
        C = [b["c"] for b in s]; fired = None
        for j in (p + 1, p + 2):
            if j >= cj: break
            b = s[j]
            if not (b["c"] > s[p]["h"] and (b["c"] - b["o"]) >= 0.5 * atr and b["c"] > ema_at(C, j, 21)): continue
            risk = b["c"] - sl
            if risk <= 0 or risk < RISK_FLOOR_USD or risk < RISK_FLOOR_ATR * atr: continue
            if regime_h(b["t"]) == "BEAR" or (b.get("rsi") or 50) < QRSI: continue
            lo20 = min(x["l"] for x in s[max(0, j - 19):j + 1]); hi20 = max(x["h"] for x in s[max(0, j - 19):j + 1])
            if (b["c"] - lo20) / ((hi20 - lo20) or atr) < QPOS: continue
            fired = j; break
        j1 = fired if fired is not None else cj
        e1 = s[j1]["c"]
        R1, ek1 = letrun_ext(s, j1, e1, sl, atr)
        lines["P1"].append(dict(common, j0=j1, t=s[j1]["t"], entry=e1, risk=e1 - sl,
                                R=R1, exit_k=ek1, exit_t=s[ek1]["t"]))
    return lines

LINES = build_lines()
def net(g): return g["R"] - SB / g["risk"]
for nm, exp in (("BASE", 233.6), ("P1", 257.1)):
    tot = sum(net(g) for g in LINES[nm])
    assert abs(tot - exp) < 0.5, f"linha {nm} não reproduz: {tot:.1f} vs {exp}"

def topology(sigs):
    """clusters (gap<=96b no stream de candidatos) + chain_pos CAUSAL (D4: prev precisa ter EXITADO
    com NET<=0 antes do entry, flush compartilhado <=1 ATR, gap<=96b; prev aberto => pos 0)."""
    cl = []; last = None
    for i, g in enumerate(sigs):
        if last is not None and (g["t"] - last) <= 96 * BAR: cl.append(cl[-1])
        else: cl.append(len(set(cl)) if cl else 0)
        last = g["t"]
    pos = [0] * len(sigs)
    for i in range(1, len(sigs)):
        a, b = sigs[i - 1], sigs[i]
        if (cl[i] == cl[i - 1] and a["exit_t"] <= b["t"] and net(a) <= 0
                and abs(b["flush"] - a["flush"]) <= 1.0 * a["atr"]):
            pos[i] = pos[i - 1] + 1
    return cl, pos

TOPO = {nm: topology(LINES[nm]) for nm in LINES}

def panel(seq):
    """seq=[(t,yr,Rg,Rn,risk)] cronológico → painel completo."""
    seq = sorted(seq); n = len(seq)
    if not n: return None
    out = {"N": n}
    for tag, R in (("g", [x[2] for x in seq]), ("q", [x[3] for x in seq])):
        eq = pk = dd = 0.0; mL = mW = cl_ = cw = 0
        for x in R:
            eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
            if x > 0: cw += 1; cl_ = 0
            else: cl_ += 1; cw = 0
            mW = max(mW, cw); mL = max(mL, cl_)
        w = sum(1 for x in R if x > 0)
        out[tag] = dict(sum=sum(R), wr=100 * w / n, avg=sum(R) / n, dd=dd,
                        rdd=abs(sum(R) / dd) if dd < 0 else 99, stkL=mL, stkW=mW,
                        run=sum(1 for x in R if x >= 3))
    out["yrs"] = {y: round(sum(x[3] for x in seq if x[1] == y), 1) for y in (2024, 2025, 2026)}
    mo, wk = {}, {}
    for t, yr, g_, q, rk in seq:
        d = dt.datetime.utcfromtimestamp(t)
        mo[d.strftime("%Y-%m")] = mo.get(d.strftime("%Y-%m"), 0) + q
        wk[d.strftime("%G-%V")] = wk.get(d.strftime("%G-%V"), 0) + q
    out["mo_pos"] = 100 * sum(1 for v in mo.values() if v > 0) / len(mo)
    out["mo_worst"] = min(mo.values()); out["wk_worst"] = min(wk.values())
    out["cost_med"] = sorted(SB / x[4] for x in seq)[n // 2]
    return out

def fn_gate(st, runners_kept, line):
    need_run = 48 if line == "BASE" else 51
    return {"WR>=50": st["q"]["wr"] >= 50, "stk<=6": st["q"]["stkL"] <= 6,
            f"run>={need_run}": runners_kept >= need_run, "sum>=200": st["q"]["sum"] >= 200,
            "anos+2024>=10": all(st["yrs"][y] > 0 for y in (2024, 2025, 2026)) and st["yrs"][2024] >= 10,
            "cost<=0.15": st["cost_med"] <= 0.15}

def seq_of(sigs, idxs=None, wts=None):
    idxs = range(len(sigs)) if idxs is None else idxs
    out = []
    for i in idxs:
        g = sigs[i]; w = 1.0 if wts is None else wts[i]
        out.append((g["t"], g["yr"], w * g["R"], w * net(g), g["risk"]))
    return out

BASE_ST = {nm: panel(seq_of(LINES[nm])) for nm in LINES}
BASE_RUN = {nm: BASE_ST[nm]["g"]["run"] for nm in LINES}

ROWS_CSV = []; SUMMARY = {}
def report(line, name, kept, sigs, wts=None, extra=""):
    st = panel(seq_of(sigs, kept, wts))
    cut = [i for i in range(len(sigs)) if i not in set(kept)] if wts is None else []
    rk = sum(1 for i in cut if sigs[i]["R"] >= 3)
    rk_net = sum(net(sigs[i]) for i in cut if sigs[i]["R"] >= 3)
    losers_cut = sum(1 for i in cut if net(sigs[i]) <= 0)
    blocked_net = sum(net(sigs[i]) for i in cut)
    top10 = sorted(range(len(sigs)), key=lambda i: -net(sigs[i]))[:10]
    top10_kill = sum(1 for i in cut if i in set(top10))
    ret = 100 * st["q"]["sum"] / BASE_ST[line]["q"]["sum"]
    runners_kept = st["g"]["run"]
    fn = fn_gate(st, runners_kept, line)
    # leave-episódio (clusters) sobre delta>0
    delta = st["q"]["sum"] - BASE_ST[line]["q"]["sum"]; conc = 0.0
    if delta > 1e-9 and wts is None:
        cl = TOPO[line][0]
        for c in set(cl):
            d_c = -sum(net(sigs[i]) for i in cut if cl[i] == c)
            conc = max(conc, d_c / delta)
    q = st["q"]
    print(f"  {name:<16} N{st['N']:>3} WR{q['wr']:>5.1f} NET{q['sum']:>7.1f} ret{ret:>5.1f}% DD{q['dd']:>6.1f} "
          f"r/DD{q['rdd']:>5.2f} stk-{q['stkL']} run{runners_kept} | cut{len(cut)} rk{rk}({rk_net:+.0f}) top10k{top10_kill} "
          f"lc{losers_cut} | piorMes{st['mo_worst']:+.1f} piorSem{st['wk_worst']:+.1f} | FN{sum(fn.values())}/6 {extra}")
    ROWS_CSV.append(dict(line=line, config=name, N=st["N"], WR_liq=round(q["wr"], 1), sumNET=round(q["sum"], 1),
                         retention=round(ret, 1), DD=round(q["dd"], 1), rDD=round(q["rdd"], 2), streak=q["stkL"],
                         runners=runners_kept, blocked=len(cut), blocked_NET=round(blocked_net, 1), runner_kill=rk,
                         runner_kill_NET=round(rk_net, 1), top10_killed=top10_kill, losers_cut=losers_cut,
                         worst_month=round(st["mo_worst"], 1), worst_week=round(st["wk_worst"], 1),
                         yr2024=st["yrs"][2024], yr2025=st["yrs"][2025], yr2026=st["yrs"][2026],
                         fn_pass=sum(fn.values()), fn_fail=";".join(k for k, v in fn.items() if not v),
                         conc_max=round(conc, 2), extra=extra))
    return st, cut

def nulls_sel(line, kept_n, blocked_n, obs_net, reps=500):
    """random-drop mesmo N + episode-aware (drop só em clusters multi-trade) — D9."""
    sigs = LINES[line]; nets = [net(g) for g in sigs]
    cl = TOPO[line][0]
    from collections import Counter
    csz = Counter(cl); pool = [i for i in range(len(sigs)) if csz[cl[i]] >= 2]
    nd_r, nd_e = [], []
    for _ in range(reps):
        drop = set(random.sample(range(len(sigs)), blocked_n))
        nd_r.append(sum(nets[i] for i in range(len(sigs)) if i not in drop))
        drop = set(random.sample(pool, min(blocked_n, len(pool))))
        nd_e.append(sum(nets[i] for i in range(len(sigs)) if i not in drop))
    p_r = sum(1 for d in nd_r if d >= obs_net) / reps
    p_e = sum(1 for d in nd_e if d >= obs_net) / reps
    return p_r, p_e

# ---------------- máquina de estados causal (D2/D3/D5/D14) ----------------
def simulate(line, rule):
    """Cascata real: processa entries em ordem; estado alimentado APENAS por exits realizados de
    trades TOMADOS (skip não atualiza estado). rule(g,i,state)->take?; exits entram por exit_t."""
    sigs = LINES[line]; cl, _ = TOPO[line]
    taken = []; kept = []
    pend = []  # exits pendentes de trades tomados: (exit_t, net, cluster)
    cl_start = {}
    for i, g in enumerate(sigs): cl_start.setdefault(cl[i], g["t"])
    state = dict(realized=[], cl=cl, cl_start=cl_start, line=line)
    for i, g in enumerate(sigs):
        pend.sort()
        while pend and pend[0][0] <= g["t"]:
            et, nv, c = pend.pop(0); state["realized"].append((et, nv, c))
        state["day_taken"] = sum(1 for j in kept if dt.datetime.utcfromtimestamp(sigs[j]["t"]).date()
                                 == dt.datetime.utcfromtimestamp(g["t"]).date())
        state["cl_taken"] = sum(1 for j in kept if cl[j] == cl[i])
        if rule(g, i, state):
            kept.append(i); pend.append((g["exit_t"], net(g), cl[i]))
    return kept

def r_cooldown(X):
    def rule(g, i, st):
        for et, nv, c in reversed(st["realized"]):
            if nv <= 0 and c == st["cl"][i] and 0 < g["t"] - et <= X * BAR: return False
        return True
    return rule
def r_maxcluster(K):
    return lambda g, i, st: st["cl_taken"] < K
def r_maxday(K):
    return lambda g, i, st: st["day_taken"] < K
def r_breaker(K):
    def rule(g, i, st):
        rz = st["realized"]
        # run de losses consecutivos no fim da sequência realizada
        run = []
        for et, nv, c in reversed(rz):
            if nv <= 0: run.append(et)
            else: break
        if len(run) < K: return True
        lastK = sorted(run)[-K:] if len(run) >= K else run
        if max(lastK) - min(lastK) > 48 * BAR: return True
        # pausa até NOVO CLUSTER (prereg §5): termina quando o cluster corrente começou APÓS o disparo
        # (correção DA BUG-1: versão anterior só liberava o starter do cluster novo — pausa persistia)
        fire_t = max(lastK)
        if st["cl_start"][st["cl"][i]] > fire_t: return True
        return False
    return rule
def r_calguard(thresh, keyfn):
    def rule(g, i, st):
        key = keyfn(g["t"])
        tot = sum(nv for et, nv, c in st["realized"] if keyfn(et) == key)
        return tot > thresh
    return rule
kday = lambda t: dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
kweek = lambda t: dt.datetime.utcfromtimestamp(t).strftime("%G-%V")

def f5_extras(line, thresh, keyfn, obs_net, reps=500):
    """D12 + prereg §6 (correção DA): null calendar-shuffle (cascata com rótulos permutados)
    e bound de atribuição por ENTRY-time (hindsight, só como bound — nunca melhor-de-2)."""
    sigs = LINES[line]
    labels = [keyfn(g["exit_t"]) for g in sigs]
    nd = []
    for _ in range(reps):
        perm = labels[:]; random.shuffle(perm)
        kept = []; pend = []; realized = []
        for i, g in enumerate(sigs):
            pend.sort()
            while pend and pend[0][0] <= g["t"]:
                _, nv, lb = pend.pop(0); realized.append((nv, lb))
            if sum(nv for nv, lb in realized if lb == perm[i]) > thresh:
                kept.append(i); pend.append((g["exit_t"], net(g), perm[i]))
        nd.append(sum(net(sigs[i]) for i in kept))
    p_cal = sum(1 for d in nd if d >= obs_net) / reps
    kept_e = []; tot_by = {}
    for i, g in enumerate(sigs):
        k = keyfn(g["t"])
        if tot_by.get(k, 0.0) > thresh:
            kept_e.append(i); tot_by[k] = tot_by.get(k, 0.0) + net(g)
    bound_e = sum(net(sigs[i]) for i in kept_e) - BASE_ST[line]["q"]["sum"]
    return p_cal, bound_e

# ---------------- F8: re-simulação com abort (D7) ----------------
def letrun_abort(g, mode):
    s, j0, entry, sl, atr = g["s"], g["j0"], g["entry"], g["sl"], g["atr"]
    level = max(x["h"] for x in s[g["p"]:g["cj"] + 1]) + 0.05 * atr
    tstart = max(j0, g["cj"])  # P1: nível só observável a partir de cj (declarado)
    risk = entry - sl
    trail = sl; r1 = False; end = min(j0 + HMAX, len(s) - 1); crossed = False
    for k in range(j0 + 1, end + 1):
        if s[k]["l"] <= trail: return max(-1.0, min(RCAP, (trail - entry) / risk)), k, crossed
        if k > tstart and s[k]["h"] >= level: crossed = True
        if not crossed and k - j0 >= 8:
            if mode == "a" or s[k]["c"] < entry:
                return max(-1.0, min(RCAP, (s[k]["c"] - entry) / risk)), k, False
            crossed = True  # F8b: acima da entrada na 8ª barra → segue let-run sem novo abort
        if (s[k]["h"] - entry) / risk >= 1: r1 = True
        if r1:
            sw = cf_low(s, k)
            if sw: trail = max(trail, sw - 0.1 * atr)
    return max(-1.0, min(RCAP, (s[end]["c"] - entry) / risk)), end, crossed

print("=" * 118)
print("LAB F — EPISODE RISK / STREAK / DD / WR (13 configs congeladas × 2 baselines; nulls D9; Bonferroni α≈0,004)")
print("=" * 118)
for line in ("BASE", "P1"):
    sigs = LINES[line]; st0 = BASE_ST[line]
    # disclosure de concorrência (D11)
    open_ct = 0; mx = 0; evs = []
    for g in sigs: evs += [(g["t"], 1), (g["exit_t"], -1)]
    cur = 0
    overlap = sum(1 for i, g in enumerate(sigs) if any(h["t"] < g["t"] < h["exit_t"] for h in sigs[max(0, i - 6):i]))
    for t, d in sorted(evs): cur += d; mx = max(mx, cur)
    print(f"\n─── LINHA {line}: NET {st0['q']['sum']:.1f} WR {st0['q']['wr']:.1f} DD {st0['q']['dd']:.1f} stk-{st0['q']['stkL']} "
          f"run{BASE_RUN[line]} piorMes{st0['mo_worst']:+.1f} | concorrência: máx {mx} posições abertas, {overlap} entries com posição aberta (D11)")
    report(line, "BASELINE", list(range(len(sigs))), sigs)
    for name, rule in (("F1_cd8", r_cooldown(8)), ("F1_cd24", r_cooldown(24)), ("F1_cd96", r_cooldown(96)),
                       ("F2_max1c", r_maxcluster(1)), ("F2_max2c", r_maxcluster(2)), ("F2_max2day", r_maxday(2)),
                       ("F3_br2", r_breaker(2)), ("F3_br3", r_breaker(3)),
                       ("F5_daily3", r_calguard(-3.0, kday)), ("F5_wk5", r_calguard(-5.0, kweek))):
        kept = simulate(line, rule)
        st, cut = report(line, name, kept, sigs)
        if cut:
            p_r, p_e = nulls_sel(line, len(kept), len(cut), st["q"]["sum"])
            claim = "CLAIM" if (p_r < 0.004 and p_e < 0.004) else "no-claim"
            print(f"      nulls: random-drop p={p_r:.3f} · episode-aware p={p_e:.3f} → {claim}")
            ROWS_CSV[-1].update(p_random=p_r, p_episode=p_e)
        if name.startswith("F5_"):
            th, kf = (-3.0, kday) if name == "F5_daily3" else (-5.0, kweek)
            p_cal, bound_e = f5_extras(line, th, kf, st["q"]["sum"])
            d_exit = st["q"]["sum"] - BASE_ST[line]["q"]["sum"]
            print(f"      calendar-shuffle p={p_cal:.3f} · bounds Δ exit-attr {d_exit:+.1f} / entry-attr {bound_e:+.1f} (D12)")
            ROWS_CSV[-1].update(p_calshuffle=p_cal, delta_entry_attr=round(bound_e, 1))
    # F4 sizing causal (D4): pesos 1,0/0,5/0,25 por chain_pos causal
    _, pos = TOPO[line]
    wts = [1.0 if p == 0 else (0.5 if p == 1 else 0.25) for p in pos]
    st4, _ = report(line, "F4_sz", list(range(len(sigs))), sigs, wts=wts,
                    extra=f"[sizing; pos0 {pos.count(0)}/pos1 {pos.count(1)}/pos2+ {sum(1 for p in pos if p >= 2)}; NUNCA edge (D15)]")
    tw = sum(wts)
    print(f"      risco-normalizado: R/unid {st0['q']['sum']/len(sigs):.3f}→{st4['q']['sum']/tw:.3f} | bootstrap por cluster:")
    cl = TOPO[line][0]
    from collections import defaultdict
    clmap = defaultdict(list)
    for i, c in enumerate(cl): clmap[c].append(i)
    blocks = list(clmap.values())
    def boot(w):
        out = []
        for _ in range(1000):
            seq = [w[i] * net(sigs[i]) for _ in range(len(blocks)) for i in blocks[random.randrange(len(blocks))]]
            eq = pk = dd = 0.0; mL = cl_ = 0
            for x in seq:
                eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
                if x <= 0: cl_ += 1; mL = max(mL, cl_)
                else: cl_ = 0
            out.append((mL, dd))
        return out
    q95 = lambda v: sorted(v)[int(0.95 * len(v))]
    bb, b4 = boot([1.0] * len(sigs)), boot(wts)
    print(f"        streak q95 {q95([x[0] for x in bb])}→{q95([x[0] for x in b4])} (contagem invariante por construção) · "
          f"DD q95 {q95([-x[1] for x in bb]):.1f}→{q95([-x[1] for x in b4]):.1f}")
    ROWS_CSV[-1].update(dd_q95_base=round(q95([-x[1] for x in bb]), 1), dd_q95=round(q95([-x[1] for x in b4]), 1))
    # F8 re-simulação
    for mode in ("a", "b"):
        res = [letrun_abort(g, mode) for g in sigs]
        seq = [(g["t"], g["yr"], R, R - SB / g["risk"], g["risk"]) for g, (R, ek, cr) in zip(sigs, res)]
        st8 = panel(seq)
        aborted = [i for i, (R, ek, cr) in enumerate(res) if not cr and ek < min(sigs[i]["j0"] + HMAX, len(sigs[i]["s"]) - 1)
                   and ek - sigs[i]["j0"] >= 8 and abs(R - sigs[i]["R"]) > 1e-9]
        rk8 = sum(1 for i in aborted if sigs[i]["R"] >= 3)
        w2w = sum(1 for i in aborted if net(sigs[i]) > 0 and seq[i][3] > 0)
        w2l = sum(1 for i in aborted if net(sigs[i]) > 0 and seq[i][3] <= 0)
        l2w = sum(1 for i in aborted if net(sigs[i]) <= 0 and seq[i][3] > 0)
        ret = 100 * st8["q"]["sum"] / st0["q"]["sum"]
        fn8 = fn_gate(st8, st8["g"]["run"], line)
        print(f"  F8{mode}_abort8     N{st8['N']:>3} WR{st8['q']['wr']:>5.1f} NET{st8['q']['sum']:>7.1f} ret{ret:>5.1f}% "
          f"DD{st8['q']['dd']:>6.1f} r/DD{st8['q']['rdd']:>5.2f} stk-{st8['q']['stkL']} run{st8['g']['run']} | aborts{len(aborted)} "
          f"rkill{rk8} winner→loser{w2l} loser→winner{l2w} winner-mantido{w2w} | piorMes{st8['mo_worst']:+.1f} | FN{sum(fn8.values())}/6")
        # null F8: abort aleatório do mesmo N (força exit na 8ª barra), 500 reps
        def forced_abort(g):
            s, j0, entry, sl, atr = g["s"], g["j0"], g["entry"], g["sl"], g["atr"]
            risk = entry - sl; trail = sl; r1 = False; end = min(j0 + HMAX, len(s) - 1)
            for k in range(j0 + 1, end + 1):
                if s[k]["l"] <= trail: return max(-1.0, min(RCAP, (trail - entry) / risk))
                if k - j0 >= 8: return max(-1.0, min(RCAP, (s[k]["c"] - entry) / risk))
                if (s[k]["h"] - entry) / risk >= 1: r1 = True
                if r1:
                    sw = cf_low(s, k)
                    if sw: trail = max(trail, sw - 0.1 * atr)
            return max(-1.0, min(RCAP, (s[end]["c"] - entry) / risk))
        FA = {i: forced_abort(sigs[i]) for i in range(len(sigs))}
        nd = []
        for _ in range(500):
            pick = set(random.sample(range(len(sigs)), len(aborted)))
            nd.append(sum((FA[i] if i in pick else sigs[i]["R"]) - SB / sigs[i]["risk"] for i in range(len(sigs))))
        p8 = sum(1 for d in nd if d >= st8["q"]["sum"]) / len(nd)
        print(f"      null abort-aleatório (500): p={p8:.3f} → {'CLAIM' if p8 < 0.004 else 'no-claim'}")
        ROWS_CSV.append(dict(line=line, config=f"F8{mode}_abort8", N=st8["N"], WR_liq=round(st8["q"]["wr"], 1),
                             sumNET=round(st8["q"]["sum"], 1), retention=round(ret, 1), DD=round(st8["q"]["dd"], 1),
                             rDD=round(st8["q"]["rdd"], 2), streak=st8["q"]["stkL"], runners=st8["g"]["run"],
                             blocked=len(aborted), runner_kill=rk8, top10_killed=0, losers_cut=0,
                             worst_month=round(st8["mo_worst"], 1), worst_week=round(st8["wk_worst"], 1),
                             yr2024=st8["yrs"][2024], yr2025=st8["yrs"][2025], yr2026=st8["yrs"][2026],
                             fn_pass=sum(fn8.values()), fn_fail=";".join(k for k, v in fn8.items() if not v),
                             p_random=p8, extra=f"w→l {w2l} l→w {l2w}"))

(HERE / "results").mkdir(exist_ok=True)
with open(HERE / "results" / "lab_f_episode_risk_results.csv", "w", newline="") as fh:
    allk = sorted({k for r in ROWS_CSV for k in r})
    w = csv.DictWriter(fh, fieldnames=allk); w.writeheader()
    for r in ROWS_CSV: w.writerow(r)
SUMMARY = {"rows": len(ROWS_CSV), "baselines": {nm: round(BASE_ST[nm]["q"]["sum"], 1) for nm in LINES},
           "ledger": "13 configs × 2 linhas; nulls D9; Bonferroni α≈0,004; nenhuma config extra"}
json.dump(SUMMARY, open(HERE / "results" / "lab_f_episode_risk_summary.json", "w"), indent=1)
print("\nOK → results/lab_f_episode_risk_results.csv + lab_f_episode_risk_summary.json")
