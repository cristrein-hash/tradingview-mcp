#!/usr/bin/env python3
"""DA LAB F — ataque 1: F3 breaker (prereg vs código), F1 cooldown replicação independente,
F4 chain_pos causal + runner-weighted, F2 max2day/max1c. NÃO modifica o lab; exec das definições."""
import datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
BAR = 900
src = (HERE / "lab_f_episode_risk_streak_dd_wr_analysis.py").read_text()
head = src.split('print("=" * 118)')[0]  # definições, sem o loop de relatório
ns = {"__name__": "labf", "__file__": str(HERE / "lab_f_episode_risk_streak_dd_wr_analysis.py")}
exec(compile(head, "labf", "exec"), ns)
LINES, TOPO, net, panel, seq_of = ns["LINES"], ns["TOPO"], ns["net"], ns["panel"], ns["seq_of"]
simulate, r_breaker, r_cooldown = ns["simulate"], ns["r_breaker"], ns["r_cooldown"]
r_maxcluster, r_maxday = ns["r_maxcluster"], ns["r_maxday"]
BASE_ST = ns["BASE_ST"]

def mini_panel(seq_net):
    """painel independente (escrito do zero) sobre lista cronológica de NETs."""
    eq = pk = dd = 0.0; mL = cl = 0
    for x in seq_net:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x > 0: cl = 0
        else: cl += 1
        mL = max(mL, cl)
    w = sum(1 for x in seq_net if x > 0)
    return dict(N=len(seq_net), wr=100 * w / len(seq_net), sum=sum(seq_net), dd=dd, stk=mL)

print("=" * 100)
print("ATAQUE 1A — F3 BREAKER: código (só 1º trade do cluster novo reabre) vs prereg (pausa TERMINA no cluster novo)")
print("=" * 100)

def r_breaker_prereg(K, sigs, cl):
    def rule(g, i, st):
        rz = st["realized"]
        run = []
        for et, nv, c in reversed(rz):
            if nv <= 0: run.append(et)
            else: break
        if len(run) < K: return True
        lastK = sorted(run)[-K:]
        if max(lastK) - min(lastK) > 48 * BAR: return True
        fire_t = max(lastK)
        # prereg: pausa até novo cluster — qualquer boundary de cluster APÓS fire_t encerra a pausa
        for j in range(i, -1, -1):
            if sigs[j]["t"] <= fire_t: break
            if j == 0 or cl[j] != cl[j - 1]:
                return True
        return False
    return rule

for line in ("BASE", "P1"):
    sigs = LINES[line]; cl = TOPO[line][0]
    base_net = BASE_ST[line]["q"]["sum"]
    for K, name in ((2, "br2"), (3, "br3")):
        kept_lab = simulate(line, r_breaker(K))
        kept_fix = simulate(line, r_breaker_prereg(K, sigs, cl))
        s_lab, s_fix = set(kept_lab), set(kept_fix)
        extra_block = sorted(s_fix - s_lab)   # bloqueados pelo código mas permitidos pelo prereg
        extra_allow = sorted(s_lab - s_fix)
        # os extra_block são trades 2+ de cluster novo pós-breaker?
        n_newcluster_tail = sum(1 for i in extra_block if i > 0 and cl[i] == cl[i - 1])
        p_lab = mini_panel([net(sigs[i]) for i in kept_lab])
        p_fix = mini_panel([net(sigs[i]) for i in kept_fix])
        rk_lab = sum(1 for i in range(len(sigs)) if i not in s_lab and sigs[i]["R"] >= 3)
        rk_fix = sum(1 for i in range(len(sigs)) if i not in s_fix and sigs[i]["R"] >= 3)
        print(f"\n{line} F3_{name}:")
        print(f"  LAB : N{p_lab['N']} WR{p_lab['wr']:.1f} NET{p_lab['sum']:.1f} ret{100*p_lab['sum']/base_net:.1f}% "
              f"DD{p_lab['dd']:.1f} stk-{p_lab['stk']} rk{rk_lab} bloq{len(sigs)-p_lab['N']}")
        print(f"  FIX : N{p_fix['N']} WR{p_fix['wr']:.1f} NET{p_fix['sum']:.1f} ret{100*p_fix['sum']/base_net:.1f}% "
              f"DD{p_fix['dd']:.1f} stk-{p_fix['stk']} rk{rk_fix} bloq{len(sigs)-p_fix['N']}")
        print(f"  divergência: código bloqueia {len(extra_block)} a mais (dos quais {n_newcluster_tail} são trades 2+ "
              f"de cluster NOVO pós-breaker = violação direta do prereg); código permite {len(extra_allow)} que o fix bloqueia")
        if extra_block[:6]:
            ex = [dt.datetime.utcfromtimestamp(sigs[i]['t']).strftime('%Y-%m-%d %H:%M') + f" net{net(sigs[i]):+.2f}" for i in extra_block[:6]]
            print(f"  exemplos extra-bloqueados: {ex}")

print()
print("=" * 100)
print("ATAQUE 1B — F1 COOLDOWN: replicação independente (do zero) + hindsight vs cascata")
print("=" * 100)
for line in ("BASE", "P1"):
    sigs = LINES[line]
    # cluster independente (recomputado do zero)
    cl2 = []; last = None; cid = 0
    for g in sigs:
        if last is not None and g["t"] - last > 96 * BAR: cid += 1
        cl2.append(cid); last = g["t"]
    assert len(set(zip(cl2, TOPO[line][0]))) == len(set(cl2)), "cluster ids divergem"
    for X in (8, 24, 96):
        kept_lab = simulate(line, r_cooldown(X))
        # replicação independente da cascata
        kept_ind = []; realized = []  # (exit_t, net, cl)
        for i, g in enumerate(sigs):
            blocked = any(nv <= 0 and c == cl2[i] and 0 < g["t"] - et <= X * BAR
                          for et, nv, c in realized if et <= g["t"])
            if not blocked:
                kept_ind.append(i); realized.append((g["exit_t"], net(g), cl2[i]))
        # variante hindsight (estado de TODOS os candidatos, sem cascata — o que D5 proíbe)
        kept_hind = []
        for i, g in enumerate(sigs):
            blocked = any(net(h) <= 0 and cl2[j] == cl2[i] and 0 < g["t"] - h["exit_t"] <= X * BAR and h["exit_t"] <= g["t"]
                          for j, h in enumerate(sigs[:i]))
            if not blocked: kept_hind.append(i)
        match = "IDÊNTICO" if kept_ind == kept_lab else f"DIVERGE ({len(set(kept_lab) ^ set(kept_ind))} trades)"
        print(f"{line} F1_cd{X}: lab N{len(kept_lab)} vs replicação independente N{len(kept_ind)} → {match} | "
              f"hindsight (sem cascata) N{len(kept_hind)} (Δ={len(set(kept_lab) ^ set(kept_hind))} trades ⇒ cascata é real)")

print()
print("=" * 100)
print("ATAQUE 1C — F4 chain_pos causal: verificação trade-a-trade + runners ponderados")
print("=" * 100)
for line in ("BASE", "P1"):
    sigs = LINES[line]; cl, pos = TOPO[line]
    bad = 0
    for i in range(len(sigs)):
        if pos[i] >= 1:
            a, b = sigs[i - 1], sigs[i]
            ok = (cl[i] == cl[i - 1] and a["exit_t"] <= b["t"] and net(a) <= 0
                  and abs(b["flush"] - a["flush"]) <= 1.0 * a["atr"] and b["t"] - a["t"] <= 96 * BAR)
            if not ok: bad += 1
    c0, c1, c2 = pos.count(0), pos.count(1), sum(1 for p in pos if p >= 2)
    print(f"{line}: pos {c0}/{c1}/{c2} (soma {c0+c1+c2}) · violações de causalidade: {bad}")
    # prev ABERTO no entry (exit_t > t) — quantos pares mesmo-cluster foram demovidos a pos0 por isso?
    demoted = sum(1 for i in range(1, len(sigs)) if cl[i] == cl[i - 1] and sigs[i - 1]["exit_t"] > sigs[i]["t"])
    print(f"  pares mesmo-cluster com prev ainda ABERTO no entry (demovidos p/ pos0, D4): {demoted}")
    wts = [1.0 if p == 0 else (0.5 if p == 1 else 0.25) for p in pos]
    run_gross = sum(1 for g in sigs if g["R"] >= 3)
    run_weighted = sum(1 for g, w in zip(sigs, wts) if w * g["R"] >= 3)
    downw = [(i, sigs[i]["R"], wts[i]) for i in range(len(sigs)) if sigs[i]["R"] >= 3 and wts[i] * sigs[i]["R"] < 3]
    print(f"  runners gross {run_gross} vs 'run' reportado no painel ponderado {run_weighted} — "
          f"{len(downw)} runners NÃO mortos, apenas subponderados abaixo de 3R: {[(round(r,2), w) for _, r, w in downw]}")
    # aritmética independente F4 (item 8)
    seqn = [w * net(g) for g, w in zip(sigs, wts)]
    mp = mini_panel(seqn)
    tw = sum(wts)
    print(f"  painel F4 independente: N{mp['N']} WR{mp['wr']:.1f} NET{mp['sum']:.1f} ret{100*mp['sum']/BASE_ST[line]['q']['sum']:.1f}% "
          f"DD{mp['dd']:.1f} stk-{mp['stk']} R/unid {mp['sum']/tw:.3f}")

print()
print("=" * 100)
print("ATAQUE 1D — F2: max2day contagem TOMADOS + decomposição 2024 · max1c aritmética independente (P1)")
print("=" * 100)
for line in ("BASE", "P1"):
    sigs = LINES[line]
    kept = simulate(line, r_maxday(2))
    # replicação independente: máx 2 TOMADOS por dia UTC, cascata
    kept_ind = []; per_day = {}
    for i, g in enumerate(sigs):
        d = dt.datetime.utcfromtimestamp(g["t"]).date()
        if per_day.get(d, 0) < 2:
            kept_ind.append(i); per_day[d] = per_day.get(d, 0) + 1
    print(f"{line} F2_max2day: lab N{len(kept)} vs replicação N{len(kept_ind)} → "
          f"{'IDÊNTICO' if kept == kept_ind else 'DIVERGE ' + str(len(set(kept) ^ set(kept_ind)))}")
    cut = [i for i in range(len(sigs)) if i not in set(kept)]
    cut24 = [i for i in cut if sigs[i]["yr"] == 2024]
    net24_cut = sum(net(sigs[i]) for i in cut24)
    kept24 = sum(net(sigs[i]) for i in kept if sigs[i]["yr"] == 2024)
    base24 = sum(net(g) for g in sigs if g["yr"] == 2024)
    big = sorted(cut24, key=lambda i: -net(sigs[i]))[:5]
    print(f"  2024: baseline {base24:+.1f} → kept {kept24:+.1f} (corta {len(cut24)} trades, NET cortado {net24_cut:+.1f})")
    print(f"  maiores winners 2024 cortados: {[(dt.datetime.utcfromtimestamp(sigs[i]['t']).strftime('%m-%d %H:%M'), round(net(sigs[i]),2)) for i in big]}")

# F2_max1c P1 aritmética independente (item 8)
line = "P1"; sigs = LINES[line]
kept = simulate(line, r_maxcluster(1))
mp = mini_panel([net(sigs[i]) for i in kept])
cut = [i for i in range(len(sigs)) if i not in set(kept)]
rk = sum(1 for i in cut if sigs[i]["R"] >= 3)
top10 = sorted(range(len(sigs)), key=lambda i: -net(sigs[i]))[:10]
t10k = sum(1 for i in cut if i in set(top10))
runners_kept = sum(1 for i in kept if sigs[i]["R"] >= 3)
print(f"\nP1 F2_max1c independente: N{mp['N']} WR{mp['wr']:.1f} NET{mp['sum']:.1f} "
      f"ret{100*mp['sum']/BASE_ST[line]['q']['sum']:.1f}% DD{mp['dd']:.1f} stk-{mp['stk']} "
      f"runners_kept{runners_kept} rk{rk} top10k{t10k}  (CSV: 122/50.0/87.0/33.8/-5.4/5/17/39/7)")
# F5_daily3 BASE aritmética independente (item 8)
line = "BASE"; sigs = LINES[line]
kept = simulate(line, ns["r_calguard"](-3.0, ns["kday"]))
mp = mini_panel([net(sigs[i]) for i in kept])
cut = [i for i in range(len(sigs)) if i not in set(kept)]
rk = sum(1 for i in cut if sigs[i]["R"] >= 3)
runners_kept = sum(1 for i in kept if sigs[i]["R"] >= 3)
print(f"BASE F5_daily3 independente: N{mp['N']} WR{mp['wr']:.1f} NET{mp['sum']:.1f} "
      f"ret{100*mp['sum']/BASE_ST[line]['q']['sum']:.1f}% DD{mp['dd']:.1f} stk-{mp['stk']} "
      f"runners_kept{runners_kept} rk{rk}  (CSV: 423/46.1/230.7/98.8/-13.2/7/52/1)")
