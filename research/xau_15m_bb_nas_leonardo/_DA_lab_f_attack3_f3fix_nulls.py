#!/usr/bin/env python3
"""DA LAB F — ataque 3: F3 sob a regra CORRETA do prereg — painel completo + nulls D9 + lente exit-order.
Responde: o veredito da família F3 muda materialmente sob a regra 'pausa termina quando novo cluster começa'?"""
import random, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
BAR = 900
src = (HERE / "lab_f_episode_risk_streak_dd_wr_analysis.py").read_text()
head = src.split('print("=" * 118)')[0]
ns = {"__name__": "labf", "__file__": str(HERE / "lab_f_episode_risk_streak_dd_wr_analysis.py")}
exec(compile(head, "labf", "exec"), ns)
LINES, TOPO, net, BASE_ST, simulate = ns["LINES"], ns["TOPO"], ns["net"], ns["BASE_ST"], ns["simulate"]

def mini(seqn):
    eq = pk = dd = 0.0; mL = cl = 0
    for x in seqn:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        cl = 0 if x > 0 else cl + 1; mL = max(mL, cl)
    return dict(N=len(seqn), sum=sum(seqn), dd=dd, stk=mL,
                wr=100 * sum(1 for x in seqn if x > 0) / len(seqn))

def r_breaker_prereg(K, sigs, cl):
    def rule(g, i, st):
        rz = st["realized"]; run = []
        for et, nv, c in reversed(rz):
            if nv <= 0: run.append(et)
            else: break
        if len(run) < K: return True
        lastK = sorted(run)[-K:]
        if max(lastK) - min(lastK) > 48 * BAR: return True
        fire_t = max(lastK)
        for j in range(i, -1, -1):
            if sigs[j]["t"] <= fire_t: break
            if j == 0 or cl[j] != cl[j - 1]: return True
        return False
    return rule

random.seed(42)
from collections import Counter
for line in ("BASE", "P1"):
    sigs = LINES[line]; cl = TOPO[line][0]; base_net = BASE_ST[line]["q"]["sum"]
    nets = [net(g) for g in sigs]
    csz = Counter(cl); pool = [i for i in range(len(sigs)) if csz[cl[i]] >= 2]
    for K in (2, 3):
        kept = simulate(line, r_breaker_prereg(K, sigs, cl))
        s_k = set(kept); cut = [i for i in range(len(sigs)) if i not in s_k]
        pe = mini([nets[i] for i in kept])
        px = mini([nets[i] for i in sorted(kept, key=lambda i: (sigs[i]["exit_t"], sigs[i]["t"]))])
        rk = sum(1 for i in cut if sigs[i]["R"] >= 3)
        rk_net = sum(nets[i] for i in cut if sigs[i]["R"] >= 3)
        top10 = set(sorted(range(len(sigs)), key=lambda i: -nets[i])[:10])
        runners_kept = sum(1 for i in kept if sigs[i]["R"] >= 3)
        yr = {y: sum(nets[i] for i in kept if sigs[i]["yr"] == y) for y in (2024, 2025, 2026)}
        # nulls D9
        obs = pe["sum"]; nd_r = []; nd_e = []
        for _ in range(500):
            drop = set(random.sample(range(len(sigs)), len(cut)))
            nd_r.append(sum(nets[i] for i in range(len(sigs)) if i not in drop))
            drop = set(random.sample(pool, min(len(cut), len(pool))))
            nd_e.append(sum(nets[i] for i in range(len(sigs)) if i not in drop))
        p_r = sum(1 for d in nd_r if d >= obs) / 500
        p_e = sum(1 for d in nd_e if d >= obs) / 500
        print(f"{line} F3_br{K} FIX(prereg): N{pe['N']} WR{pe['wr']:.1f} NET{pe['sum']:.1f} ret{100*pe['sum']/base_net:.1f}% "
              f"DD{pe['dd']:.1f} (exit-lens {px['dd']:.1f}) stk-{pe['stk']} (exit-lens -{px['stk']}) "
              f"run{runners_kept} rk{rk}({rk_net:+.0f}) top10k{sum(1 for i in cut if i in top10)} | "
              f"yr {yr[2024]:+.1f}/{yr[2025]:+.1f}/{yr[2026]:+.1f} | nulls p_r={p_r:.3f} p_e={p_e:.3f} → "
              f"{'CLAIM' if p_r < 0.004 and p_e < 0.004 else 'no-claim'}")
