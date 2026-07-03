#!/usr/bin/env python3
"""DA LAB F — ataque 2: F5 (bounds entry-time D12 + calendar-shuffle null ausente no lab),
F8 (identidade letrun, runner-kill, w→l, fairness do null), concorrência D11 (lente exit-order),
pool do episode-aware null, scan FN WR/streak."""
import datetime as dt, random
from pathlib import Path

HERE = Path(__file__).parent
BAR = 900
src = (HERE / "lab_f_episode_risk_streak_dd_wr_analysis.py").read_text()
head = src.split('print("=" * 118)')[0]
ns = {"__name__": "labf", "__file__": str(HERE / "lab_f_episode_risk_streak_dd_wr_analysis.py")}
exec(compile(head, "labf", "exec"), ns)
LINES, TOPO, net, BASE_ST = ns["LINES"], ns["TOPO"], ns["net"], ns["BASE_ST"]
simulate, letrun_abort, SB, HMAX = ns["simulate"], ns["letrun_abort"], ns["SB"], ns["HMAX"]
kday, kweek, r_calguard = ns["kday"], ns["kweek"], ns["r_calguard"]

def mini(seqn):
    eq = pk = dd = 0.0; mL = cl = 0
    for x in seqn:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        cl = 0 if x > 0 else cl + 1; mL = max(mL, cl)
    return dict(N=len(seqn), sum=sum(seqn), dd=dd, stk=mL,
                wr=100 * sum(1 for x in seqn if x > 0) / len(seqn))

print("=" * 100)
print("ATAQUE 2A — F5: attribution exit-time (lab) vs ENTRY-time (bound D12) + calendar-shuffle null")
print("=" * 100)
def sim_guard(line, thresh, keyfn, attr):  # attr: 'exit' ou 'entry'
    sigs = LINES[line]; kept = []; pend = []  # (exit_t, net, key_da_attr)
    for i, g in enumerate(sigs):
        pend.sort()
        realized = []
        while pend and pend[0][0] <= g["t"]:
            realized.append(pend.pop(0))
        sim_guard.done.extend(realized)
        tot = sum(nv for et, nv, ky in sim_guard.done if ky == keyfn(g["t"]))
        if tot > thresh:
            kept.append(i)
            ky = keyfn(g["exit_t"]) if attr == "exit" else keyfn(g["t"])
            pend.append((g["exit_t"], net(g), ky))
    return kept
for line in ("BASE", "P1"):
    base_net = BASE_ST[line]["q"]["sum"]
    for nmc, thresh, keyfn in (("daily3", -3.0, kday), ("wk5", -5.0, kweek)):
        res = {}
        for attr in ("exit", "entry"):
            sim_guard.done = []
            kept = sim_guard(line, thresh, keyfn, attr)
            p = mini([net(LINES[line][i]) for i in kept])
            res[attr] = p
        # sanity: exit-attr deve reproduzir o lab
        kept_lab = simulate(line, r_calguard(thresh, keyfn))
        p_lab = mini([net(LINES[line][i]) for i in kept_lab])
        ok = abs(p_lab["sum"] - res["exit"]["sum"]) < 1e-9 and p_lab["N"] == res["exit"]["N"]
        print(f"{line} F5_{nmc}: exit-attr N{res['exit']['N']} NET{res['exit']['sum']:.1f} (Δ{res['exit']['sum']-base_net:+.1f}) "
              f"{'=lab OK' if ok else '≠LAB!!'} | ENTRY-attr N{res['entry']['N']} NET{res['entry']['sum']:.1f} "
              f"(Δ{res['entry']['sum']-base_net:+.1f}) DD{res['entry']['dd']:.1f} stk-{res['entry']['stk']}")

print("\ncalendar-shuffle null (prereg §6, AUSENTE no lab) — 500 reps, labels de dia/semana permutados entre trades:")
random.seed(7)
for line in ("BASE", "P1"):
    sigs = LINES[line]
    for nmc, thresh, keyfn in (("daily3", -3.0, kday), ("wk5", -5.0, kweek)):
        keys = [keyfn(g["t"]) for g in sigs]
        kept_obs = simulate(line, r_calguard(thresh, keyfn))
        obs = sum(net(sigs[i]) for i in kept_obs)
        nulls = []
        for _ in range(500):
            perm = keys[:]; random.shuffle(perm)
            kept = []; done = []; pend = []
            for i, g in enumerate(sigs):
                pend.sort()
                while pend and pend[0][0] <= g["t"]: done.append(pend.pop(0))
                tot = sum(nv for et, nv, ky in done if ky == perm[i])
                if tot > thresh:
                    kept.append(i); pend.append((g["exit_t"], net(g), perm[i]))
            nulls.append(sum(net(sigs[i]) for i in kept))
        p = sum(1 for v in nulls if v >= obs) / len(nulls)
        med = sorted(nulls)[250]
        print(f"  {line} F5_{nmc}: obs NET {obs:.1f} · null shuffle mediana {med:.1f} · p(null>=obs)={p:.3f} "
              f"→ {'CLAIM' if p < 0.004 else 'no-claim'}")

print()
print("=" * 100)
print("ATAQUE 2B — F8: identidade letrun p/ crossed, runner-kill, w→l, edge-cases, fairness do null")
print("=" * 100)
random.seed(42)
for line in ("BASE", "P1"):
    sigs = LINES[line]; st0 = BASE_ST[line]
    for mode in ("a", "b"):
        res = [letrun_abort(g, mode) for g in sigs]
        # 1) crossed ⇒ R idêntico ao engine
        mism = sum(1 for g, (R, ek, cr) in zip(sigs, res) if cr and abs(R - g["R"]) > 1e-9)
        # 2) aborted set (definição do lab)
        aborted = [i for i, (R, ek, cr) in enumerate(res) if not cr and ek < min(sigs[i]["j0"] + HMAX, len(sigs[i]["s"]) - 1)
                   and ek - sigs[i]["j0"] >= 8 and abs(R - sigs[i]["R"]) > 1e-9]
        # edge: abort real com R coincidente (excluído do set do lab)
        coinc = [i for i, (R, ek, cr) in enumerate(res) if not cr and ek == sigs[i]["j0"] + 8
                 and abs(R - sigs[i]["R"]) <= 1e-9 and sigs[i]["exit_k"] != ek]
        # 3) runner-kills
        rkill = [(dt.datetime.utcfromtimestamp(sigs[i]["t"]).strftime("%y-%m-%d %H:%M"), round(sigs[i]["R"], 2),
                  round(res[i][0], 2)) for i in aborted if sigs[i]["R"] >= 3]
        # 4) w→l / l→w recontagem
        w2l = sum(1 for i in aborted if net(sigs[i]) > 0 and res[i][0] - SB / sigs[i]["risk"] <= 0)
        l2w = sum(1 for i in aborted if net(sigs[i]) <= 0 and res[i][0] - SB / sigs[i]["risk"] > 0)
        # 5) F8b: todo abort tem close<entry na barra 8?
        if mode == "b":
            viol = sum(1 for i in aborted if sigs[i]["s"][res[i][1]]["c"] >= sigs[i]["entry"])
        else: viol = "-"
        # 6) universo abortável: vivo na barra 8 (sem SL antes) e sem cross antes da barra 8
        alive8 = sum(1 for g in sigs if g["exit_k"] - g["j0"] >= 8 or g["R"] > 0)  # aprox p/ display
        print(f"{line} F8{mode}: crossed-R-mismatch {mism} · aborts {len(aborted)} (+{len(coinc)} R-coincidente excluído) · "
              f"w→l {w2l} l→w {l2w} · F8b-violações-close>=entry {viol}")
        if mode == "a":
            print(f"   runner-kills (R_orig→R_abort): {rkill}")
    # fairness do null: null do lab sorteia dos 435; quantos picks são no-op (exit < barra 8)?
    early_exit = [i for i, g in enumerate(sigs) if g["exit_k"] - g["j0"] < 8]
    print(f"   {line}: {len(early_exit)}/435 trades saem ANTES da barra 8 (picks no-op no null do lab)")
    # null restrito ao universo vivo-na-barra-8
    def forced_abort(g):
        s, j0, entry, sl, atr = g["s"], g["j0"], g["entry"], g["sl"], g["atr"]
        risk = entry - sl; trail = sl; r1 = False; end = min(j0 + HMAX, len(s) - 1)
        for k in range(j0 + 1, end + 1):
            if s[k]["l"] <= trail: return max(-1.0, min(ns["RCAP"], (trail - entry) / risk))
            if k - j0 >= 8: return max(-1.0, min(ns["RCAP"], (s[k]["c"] - entry) / risk))
            if (s[k]["h"] - entry) / risk >= 1: r1 = True
            if r1:
                sw = ns["cf_low"](g["s"], k)
                if sw: trail = max(trail, sw - 0.1 * atr)
        return max(-1.0, min(ns["RCAP"], (s[end]["c"] - entry) / risk))
    FA = {i: forced_abort(sigs[i]) for i in range(len(sigs))}
    alive = [i for i, g in enumerate(sigs) if g["exit_k"] - g["j0"] >= 8]
    for mode in ("a", "b"):
        res = [letrun_abort(g, mode) for g in sigs]
        aborted = [i for i, (R, ek, cr) in enumerate(res) if not cr and ek < min(sigs[i]["j0"] + HMAX, len(sigs[i]["s"]) - 1)
                   and ek - sigs[i]["j0"] >= 8 and abs(R - sigs[i]["R"]) > 1e-9]
        obs = sum((res[i][0] if i in set(aborted) else sigs[i]["R"]) - SB / sigs[i]["risk"] for i in range(len(sigs)))
        nd = []
        for _ in range(500):
            pick = set(random.sample(alive, len(aborted)))
            nd.append(sum((FA[i] if i in pick else sigs[i]["R"]) - SB / sigs[i]["risk"] for i in range(len(sigs))))
        p = sum(1 for d in nd if d >= obs) / len(nd)
        print(f"   {line} F8{mode} null RESTRITO a vivos-na-barra-8 (n={len(alive)}): p={p:.3f} (lab: sorteio dos 435)")

print()
print("=" * 100)
print("ATAQUE 2C — CONCORRÊNCIA D11: verificação máx-open/overlap + lente conta (ordem por EXIT)")
print("=" * 100)
for line in ("BASE", "P1"):
    sigs = LINES[line]
    evs = sorted([(g["t"], 1) for g in sigs] + [(g["exit_t"], -1) for g in sigs])
    cur = mx = 0
    for t, d in evs: cur += d; mx = max(mx, cur)
    full_overlap = sum(1 for i, g in enumerate(sigs) if any(h["t"] < g["t"] < h["exit_t"] for h in sigs[:i]))
    win6 = sum(1 for i, g in enumerate(sigs) if any(h["t"] < g["t"] < h["exit_t"] for h in sigs[max(0, i - 6):i]))
    print(f"{line}: máx aberto {mx} · overlaps full-scan {full_overlap} vs janela-6 do lab {win6}")
    # lente exit-order por config
    from types import SimpleNamespace
    cfgs = [("BASELINE", list(range(len(sigs)))), ]
    for nm, rule in (("F1_cd8", ns["r_cooldown"](8)), ("F1_cd24", ns["r_cooldown"](24)), ("F1_cd96", ns["r_cooldown"](96)),
                     ("F2_max1c", ns["r_maxcluster"](1)), ("F2_max2c", ns["r_maxcluster"](2)), ("F2_max2day", ns["r_maxday"](2)),
                     ("F3_br2", ns["r_breaker"](2)), ("F3_br3", ns["r_breaker"](3)),
                     ("F5_daily3", r_calguard(-3.0, kday)), ("F5_wk5", r_calguard(-5.0, kweek))):
        cfgs.append((nm, simulate(line, rule)))
    print(f"  {'config':<12} {'DD_entry':>8} {'DD_exit':>8} {'stk_entry':>9} {'stk_exit':>8}")
    for nm, kept in cfgs:
        by_entry = [net(sigs[i]) for i in sorted(kept, key=lambda i: sigs[i]["t"])]
        by_exit = [net(sigs[i]) for i in sorted(kept, key=lambda i: (sigs[i]["exit_t"], sigs[i]["t"]))]
        pe, px = mini(by_entry), mini(by_exit)
        flag = " ←" if abs(px["dd"] - pe["dd"]) >= 1.5 or px["stk"] != pe["stk"] else ""
        print(f"  {nm:<12} {pe['dd']:>8.1f} {px['dd']:>8.1f} {pe['stk']:>9} {px['stk']:>8}{flag}")

print()
print("=" * 100)
print("ATAQUE 2D — pool do episode-aware null + scan WR≥50 & stk≤6 no CSV")
print("=" * 100)
from collections import Counter
for line in ("BASE", "P1"):
    cl = TOPO[line][0]; csz = Counter(cl)
    pool = [i for i in range(len(LINES[line])) if csz[cl[i]] >= 2]
    print(f"{line}: pool episode-aware = {len(pool)}/435 (blocked_n máx nas configs = 313 F2_max1c → "
          f"{'OK' if len(pool) >= 313 else 'POOL MENOR QUE blocked_n: null drop só ' + str(len(pool))})")
import csv as csvm
rows = list(csvm.DictReader(open(HERE / "results" / "lab_f_episode_risk_results.csv")))
hits = [(r["line"], r["config"], r["WR_liq"], r["streak"], r["retention"], r["runner_kill"], r["top10_killed"])
        for r in rows if float(r["WR_liq"]) >= 50 and int(r["streak"]) <= 6]
print(f"configs com WR≥50 E stk≤6 (eixos FN): {hits if hits else 'NENHUMA'}")
near = [(r["line"], r["config"], r["WR_liq"], r["streak"]) for r in rows if float(r["WR_liq"]) >= 49 or int(r["streak"]) <= 6]
print(f"vizinhança (WR≥49 ou stk≤6): {near}")
