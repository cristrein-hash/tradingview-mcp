#!/usr/bin/env python3
"""DA3 — auditoria adversarial da cadeia em-banda (D1/D3). NÃO modifica nada; só lê.
Vetores: 1 fi-mislocation · 2 null time-matched/por-janela · 3 multiplicidade binomial exata
+ episódios · 4 jackknife de rótulos GT · 5 D3 GT-precisão/circles distintos · 6 streak/pior mês.
"""
import json, bisect, random, math
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent

# ── replica exata da cadeia (mesmo mecanismo de exec do composite) ──
exec((HERE / "inband_wave_structure_20260705.py").read_text().split('panel3(BAND, "BANDA (base)")')[0])

# bandas snapshot (mesma regra do composite)
def qgt_s(f, p):
    v = sorted(fv(u, f) for u in Bgt if fv(u, f) is not None)
    return v[int(p * (len(v) - 1))]
SB = {f: (qgt_s(f, 0.25), qgt_s(f, 0.75)) for f in
      ("g_atr_spike", "g_sweep_depth", "legpos60", "n_supply_overhead", "rsi_low")}
W = {f: (qgt(f, 0.25), qgt(f, 0.75)) for f in FEATS}
C2f = lambda u: inb(u, "W1_n_waves", *W["W1_n_waves"]) and inb(u, "W5_bottom_time", *W["W5_bottom_time"])
C3f = lambda u: C2f(u) and inb(u, "W7_vol_dryup", *W["W7_vol_dryup"])
D1f = lambda u: C2f(u) and fv(u, "g_atr_spike", 0) >= SB["g_atr_spike"][0] and fv(u, "g_sweep_depth", -9) >= SB["g_sweep_depth"][0]
D3f = lambda u: C3f(u) and fv(u, "g_atr_spike", 0) >= SB["g_atr_spike"][0]
D1 = sorted([u for u in BAND if D1f(u)], key=lambda x: x["cj_t"])
D3 = sorted([u for u in BAND if D3f(u)], key=lambda x: x["cj_t"])
hits = lambda rows: sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3)
net = lambda rows: sum(R3[u["cj_t"]]["net3"] for u in rows)
nB, hB = len(BAND), hits(BAND)
print(f"REPRO: BAND N{nB} hit {100*hB/nB:.1f}% GT {sum(u['_gt'] for u in BAND)} | "
      f"D1 N{len(D1)} hit {100*hits(D1)/len(D1):.1f}% NET {net(D1):+.1f} GTp {sum(u['_gt'] for u in D1)} | "
      f"D3 N{len(D3)} hit {100*hits(D3)/len(D3):.1f}% GTp {sum(u['_gt'] for u in D3)}")

# ═══ V1: fi mislocation ═══
print("\n═══ V1 fi (barra do flush por preço) ═══")
mis = {"n": 0, "diff": 0, "diff_d1": 0, "n_d1": 0, "fi_above_min": 0, "below_flo": 0, "gaps": []}
d1set = {u["cj_t"] for u in D1}
for u in UNIV:
    if not u.get("_w"): continue
    ci = bisect.bisect_right(TS, u["cj_t"]) - 1
    a = u.get("g_atr") or 5.0
    flo = u["g_sl"] + 0.1 * a
    j = bisect.bisect_right(KLOW, ci) - 1
    ki, l0i = LOWS[j]
    h1i = max(range(l0i, ci + 1), key=lambda k: HI[k])
    fi = None
    for k in range(ci, max(ci - 96, h1i) - 1, -1):
        if abs(LO[k] - flo) <= 0.2 * a:
            fi = k; break
    if fi is None: continue
    am = min(range(max(0, ci - 96), ci + 1), key=lambda k: LO[k])
    mis["n"] += 1
    isd1 = u["cj_t"] in d1set
    if isd1: mis["n_d1"] += 1
    if fi != am:
        mis["diff"] += 1
        if isd1: mis["diff_d1"] += 1
        mis["gaps"].append(abs(am - fi))
    if LO[fi] - LO[am] > 0.2 * a: mis["fi_above_min"] += 1
    if LO[am] < flo - 0.2 * a: mis["below_flo"] += 1
g = sorted(mis["gaps"])
print(f"fi != argmin(LO[ci-96..ci]): {mis['diff']}/{mis['n']} = {100*mis['diff']/mis['n']:.1f}%  "
      f"(D1: {mis['diff_d1']}/{mis['n_d1']} = {100*mis['diff_d1']/max(1,mis['n_d1']):.1f}%)")
if g: print(f"  |fi-argmin| barras: med {g[len(g)//2]} q90 {g[int(.9*len(g))]} max {g[-1]}")
print(f"  LO[fi] > LO[argmin]+0.2ATR (barra materialmente errada): {mis['fi_above_min']}/{mis['n']} = {100*mis['fi_above_min']/mis['n']:.1f}%")
print(f"  argmin < flo-0.2ATR (flush_low do candidato NÃO é o low da janela): {mis['below_flo']}/{mis['n']} = {100*mis['below_flo']/mis['n']:.1f}%")

# ═══ V2: sub-janelas + null time-matched ═══
print("\n═══ V2 sub-janelas + null dentro-de-estrato ═══")
T25H2 = int(dt.datetime(2025, 7, 1, tzinfo=dt.timezone.utc).timestamp())
def stratum(u):
    if u["yr"] == 2024: return "2024"
    if u["yr"] == 2026: return "2026"
    return "2025H1" if u["cj_t"] < T25H2 else "2025H2"
strata = {}
for u in BAND: strata.setdefault(stratum(u), []).append(u)
d1s = {}
for u in D1: d1s.setdefault(stratum(u), []).append(u)
for s in ("2024", "2025H1", "2025H2", "2026"):
    b = strata.get(s, []); d = d1s.get(s, [])
    hb = hits(b); hd = hits(d)
    # p por estrato (hipergeom via permutação)
    random.seed(101)
    H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in b]
    pd = sum(1 for _ in range(4000) if sum(random.sample(H0, len(d))) >= hd) / 4000 if d else None
    print(f"  {s:<7} banda N{len(b):>4} hit {100*hb/len(b):>5.1f}% | D1 N{len(d):>3} hit "
          f"{100*hd/max(1,len(d)):>5.1f}% NET {net(d):>+7.1f} p_estrato={pd if pd is None else f'{pd:.3f}'}")
# null time-matched global (amostra n_s de cada estrato)
random.seed(202)
obs_h, obs_net = hits(D1), net(D1)
cnt_h = cnt_net = 0
NIT = 4000
for _ in range(NIT):
    th = tn = 0.0
    for s, d in d1s.items():
        samp = random.sample(strata[s], len(d))
        th += hits(samp); tn += net(samp)
    if th >= obs_h: cnt_h += 1
    if tn >= obs_net: cnt_net += 1
print(f"  NULL TIME-MATCHED (estratos fixos): P(hit)={cnt_h/NIT:.4f} · P(NET)={cnt_net/NIT:.4f}"
      f"  [obs hit {obs_h}/{len(D1)}, NET {obs_net:+.1f}]")
# null ingênuo p/ comparação (replica o da cadeia)
random.seed(303)
H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in BAND]
NETS0 = [R3[u["cj_t"]]["net3"] for u in BAND]
idx = list(range(nB)); ch = cn = 0
for _ in range(NIT):
    smp = random.sample(idx, len(D1))
    if sum(H0[i] for i in smp) >= obs_h: ch += 1
    if sum(NETS0[i] for i in smp) >= obs_net: cn += 1
print(f"  NULL INGÊNUO (replica):        P(hit)={ch/NIT:.4f} · P(NET)={cn/NIT:.4f}")

# ═══ V3: binomial exata + multiplicidade + episódios ═══
print("\n═══ V3 multiplicidade + episódios ═══")
def binom_sf(k, n, p):
    return sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k, n+1))
p0 = hB / nB
p0x = (hB - obs_h) / (nB - len(D1))
pb = binom_sf(obs_h, len(D1), p0)
pbx = binom_sf(obs_h, len(D1), p0x)
print(f"binomial exata {obs_h}/{len(D1)}: vs banda {100*p0:.1f}% → p={pb:.5f} · vs complemento {100*p0x:.1f}% → p={pbx:.5f}")
for m in (12, 22, 27):
    print(f"  Bonferroni ×{m}: {min(1, pb*m):.4f}")
# episódios (gap >= 8h entre cj consecutivos)
def episodes(rows, gap_h=8):
    eps = []; cur = []
    for u in sorted(rows, key=lambda x: x["cj_t"]):
        if cur and u["cj_t"] - cur[-1]["cj_t"] > gap_h * 3600:
            eps.append(cur); cur = []
        cur.append(u)
    if cur: eps.append(cur)
    return eps
epB = episodes(BAND); epD = episodes(D1)
hit_eps = sum(1 for e in epD if any(R3[u["cj_t"]]["R3"] >= 3 for u in e))
same = [e for e in epD if len(e) >= 2]
homog = sum(1 for e in same if len({R3[u["cj_t"]]["R3"] >= 3 for u in e}) == 1)
print(f"episódios: banda {len(epB)} · D1 {len(epD)} (N202 → {len(epD)} indep.) · episódios c/ hit {hit_eps} · "
      f"multi-membro homogêneos {homog}/{len(same)}")
# null em nível de episódio: amostra episódios da banda até atingir >= |D1| membros
random.seed(404)
ep_all = epB[:]
ce = 0
for _ in range(NIT):
    random.shuffle(ep_all)
    n = h = 0; k = 0
    while n < len(D1) and k < len(ep_all):
        e = ep_all[k]; k += 1
        n += len(e); h += hits(e)
    if h / n >= obs_h / len(D1): ce += 1
print(f"  NULL EPISÓDIO-BLOCO: P(hit-rate)={ce/NIT:.4f}")
# concentração: NET por episódio
epn = sorted((net(e) for e in epD), reverse=True)
print(f"  top-3 episódios NET: {[f'{x:+.1f}' for x in epn[:3]]} de {obs_net:+.1f} "
      f"({100*sum(epn[:3])/max(0.01,obs_net):.0f}%)")

# ═══ V4: jackknife de rótulos GT (bandas re-derivadas sem 20% dos GT) ═══
print("\n═══ V4 jackknife GT 5× (remove 20% dos 60 círculos) ═══")
def gtflag(circles):
    flags = {id(v): 0 for v in US}
    for gci, gg in enumerate(GT_60):
        if gci not in circles: continue
        j = bisect.bisect_left(UT, gg["flush_t"] - 8 * 3600)
        while j < len(UT) and UT[j] <= gg["flush_t"] + 8 * 3600:
            v = US[j]
            if abs((v["g_sl"] + 0.1 * (v.get("g_atr") or 5.0)) - gg["flush_low"]) <= (v.get("g_atr") or 5.0):
                flags[id(v)] = 1
            j += 1
    return flags
base_ids = {id(u) for u in D1}
for seed in range(5):
    rng = random.Random(1000 + seed)
    keep = set(rng.sample(range(60), 48))
    fl = gtflag(keep)
    Bg2 = [u for u in BAND if fl[id(u)]]
    def q2w(f, p):
        v = sorted(u["_w"][f] for u in Bg2 if u["_w"][f] is not None)
        return v[int(p * (len(v) - 1))]
    def q2s(f, p):
        v = sorted(fv(u, f) for u in Bg2 if fv(u, f) is not None)
        return v[int(p * (len(v) - 1))]
    # top-3 re-derivado (estabilidade da seleção de features)
    import statistics as st2
    sep2 = {}
    Bn2 = [u for u in BAND if not fl[id(u)]]
    for f in FEATS:
        A = sorted(u["_w"][f] for u in Bg2 if u["_w"][f] is not None)
        Bv = sorted(u["_w"][f] for u in Bn2 if u["_w"][f] is not None)
        if not A or not Bv: continue
        iqr = max(0.01, (sorted(A + Bv)[3*len(A+Bv)//4] - sorted(A + Bv)[len(A+Bv)//4]))
        sep2[f] = abs(st2.median(A) - st2.median(Bv)) / iqr
    top2 = sorted(sep2, key=lambda f: -sep2[f])[:3]
    w1 = (q2w("W1_n_waves", .25), q2w("W1_n_waves", .75))
    w5 = (q2w("W5_bottom_time", .25), q2w("W5_bottom_time", .75))
    sp = q2s("g_atr_spike", .25); sw = q2s("g_sweep_depth", .25)
    D1j = [u for u in BAND if w1[0] <= u["_w"]["W1_n_waves"] <= w1[1]
           and u["_w"]["W5_bottom_time"] is not None and w5[0] <= u["_w"]["W5_bottom_time"] <= w5[1]
           and fv(u, "g_atr_spike", 0) >= sp and fv(u, "g_sweep_depth", -9) >= sw]
    ids = {id(u) for u in D1j}
    jac = len(ids & base_ids) / max(1, len(ids | base_ids))
    hj = hits(D1j)
    print(f"  seed{seed}: |GT'|={len(Bg2):>3} W1[{w1[0]},{w1[1]}] W5[{w5[0]:.2f},{w5[1]:.2f}] spike>={sp:.2f} sweep>={sw:.2f} "
          f"→ N{len(D1j):>3} hit {100*hj/max(1,len(D1j)):>5.1f}% NET {net(D1j):>+7.1f} jac {jac:.2f} top3={'IGUAL' if top2==top else top2}")

# ═══ V5: D3 GT-precisão — círculos distintos + binomial ═══
print("\n═══ V5 D3 (N26, GTp 6) ═══")
# mapa candidato→círculos
cmap = {}
for gci, gg in enumerate(GT_60):
    j = bisect.bisect_left(UT, gg["flush_t"] - 8 * 3600)
    while j < len(UT) and UT[j] <= gg["flush_t"] + 8 * 3600:
        v = US[j]
        if abs((v["g_sl"] + 0.1 * (v.get("g_atr") or 5.0)) - gg["flush_low"]) <= (v.get("g_atr") or 5.0):
            cmap.setdefault(id(v), set()).add(gci)
        j += 1
d3gt = [u for u in D3 if u["_gt"]]
circ = set()
for u in d3gt: circ |= cmap.get(id(u), set())
gt_band = sum(u["_gt"] for u in BAND)
pgt = gt_band / nB
pb3 = binom_sf(len(d3gt), len(D3), pgt)
# círculos por candidato GT na banda (inflação)
percand = [len(cmap.get(id(u), set())) for u in BAND if u["_gt"]]
candpercirc = {}
for u in BAND:
    for c in cmap.get(id(u), set()): candpercirc[c] = candpercirc.get(c, 0) + 1
cpc = sorted(candpercirc.values())
print(f"D3 GT: {len(d3gt)} candidatos → {len(circ)} círculos DISTINTOS: {sorted(circ)}")
for u in d3gt:
    print(f"  {dt.datetime.utcfromtimestamp(u['cj_t']).strftime('%Y-%m-%d %H:%M')} circles {sorted(cmap.get(id(u), set()))} "
          f"{'WIN' if R3[u['cj_t']]['R3']>=3 else 'loss'} net {R3[u['cj_t']]['net3']:+.1f}")
print(f"binomial {len(d3gt)}/{len(D3)} vs taxa-GT banda {100*pgt:.1f}% → p={pb3:.5f} (×12 Bonf: {min(1,pb3*12):.4f})")
print(f"candidatos por círculo (banda): med {cpc[len(cpc)//2] if cpc else 0} max {cpc[-1] if cpc else 0} · "
      f"círculos na banda {len(candpercirc)}/60")
d3hits_gt = sum(1 for u in d3gt if R3[u["cj_t"]]["R3"] >= 3)
print(f"dos 6 GT em D3: {d3hits_gt} WIN · D3 não-GT: {hits([u for u in D3 if not u['_gt']])}/{len(D3)-len(d3gt)} hit")

# ═══ V6: streak / pior mês D1 ═══
print("\n═══ V6 streak + pior mês (D1) ═══")
nets = [(u["cj_t"], R3[u["cj_t"]]["net3"]) for u in D1]
eq = pk = dd = 0.0; mL = cl = 0
mon = {}
for t, x in nets:
    eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
    cl = cl + 1 if x <= 0 else 0; mL = max(mL, cl)
    m = dt.datetime.utcfromtimestamp(t).strftime("%Y-%m")
    mon[m] = mon.get(m, 0) + x
worst = sorted(mon.items(), key=lambda kv: kv[1])[:5]
neg = sum(1 for v in mon.values() if v < 0)
print(f"streak obs -{mL} · DD {dd:+.1f} · meses {len(mon)} ({neg} negativos)")
print(f"piores meses: {[(m, f'{v:+.1f}') for m, v in worst]}")
# pior janela rolante 30d
ts = [t for t, _ in nets]; xs = [x for _, x in nets]
worst30 = 0.0
for i in range(len(ts)):
    s = 0.0
    for j2 in range(i, len(ts)):
        if ts[j2] - ts[i] > 30 * 86400: break
        s += xs[j2]
        worst30 = min(worst30, s)
print(f"pior janela 30d: {worst30:+.1f}R")
# streak distribucional (mesma métrica do composite)
random.seed(505)
q = []
for _ in range(2000):
    sq = random.choices(xs, k=len(xs)); c2 = m2 = 0
    for x in sq:
        c2 = c2 + 1 if x <= 0 else 0; m2 = max(m2, c2)
    q.append(m2)
q.sort()
print(f"streak dist (boot): q50 {q[1000]} q95 {q[1900]} P(>5)={sum(1 for x in q if x>5)/2000:.2f} "
      f"P(>12)={sum(1 for x in q if x>12)/2000:.2f}")
print("\nDA3 OK")
