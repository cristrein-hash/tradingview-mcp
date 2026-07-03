#!/usr/bin/env python3
"""DA INDEPENDENTE — LAB A RODADA 2 (2026-07-03). Ataques 1-10 do brief DA.
NÃO commitar. Não modifica engine nem lab script. Leitura+probes apenas."""
import json, math, random, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
SB_USD = 0.80
RISK_FLOOR_USD = 6.40
RISK_FLOOR_ATR = 0.35

# ---------- engine real (mesmo mecanismo do lab) ----------
ns = {"__name__": "engine", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(),
             "engine_substrate4_v5_hourcausal.py", "exec"), ns)
cand, ROWS, PRIMK = ns["cand"], ns["ROWS"], ns["PRIMK"]
letrun, cf_low, f = ns["letrun"], ns["cf_low"], ns["f"]
regime_h, QPOS, QRSI = ns["regime_hourcausal"], ns["QPOS"], ns["QRSI"]
HMAX, RCAP, ema_at = ns["HMAX"], ns["RCAP"], ns["ema_at"]

base_c = sorted([c for c in cand if c["v5h"] != "BEAR"], key=lambda z: z["cj_t"])
assert len(base_c) == 435
rmap = {r["cj_t"]: r for r in ROWS}

def letrun_from(s, j0, entry, sl, atr, end_at=None):
    """cópia do lab; end_at opcional p/ ancorar horizonte em cj (ataque 1)."""
    risk = entry - sl
    if risk <= 0: return None, None
    trail = sl; r1 = False; ex = None
    end = min((end_at if end_at is not None else j0) + HMAX, len(s) - 1)
    horizon_exit = False
    for k in range(j0 + 1, end + 1):
        if s[k]["l"] <= trail: ex = trail; break
        if (s[k]["h"] - entry) / risk >= 1: r1 = True
        if r1:
            sw = cf_low(s, k)
            if sw: trail = max(trail, sw - 0.1 * atr)
    if ex is None: ex = s[end]["c"]; horizon_exit = True
    return max(-1.0, min(RCAP, (ex - entry) / risk)), horizon_exit

SIG = []
for c in base_c:
    r = rmap[c["cj_t"]]; s = PRIMK[r["block"]]["series"]
    tmap = {b["t"]: i for i, b in enumerate(s)}
    p, cj = tmap[r["t"]], tmap[r["cj_t"]]
    atr = s[p]["atr"] or s[cj]["atr"]
    entry0 = s[cj]["c"]; sl = min(x["l"] for x in s[p:cj + 1]) - 0.1 * atr
    Rre = letrun(s, cj, entry0, sl, atr)
    assert abs(Rre - c["R"]) < 1e-9
    SIG.append({"t": c["cj_t"], "yr": c["yr"], "R0": c["R"], "s": s, "p": p, "cj": cj,
                "atr": atr, "entry0": entry0, "sl": sl, "risk0": entry0 - sl, "row": r})
def net(R, risk): return R - SB_USD / risk
BASE_NET = sum(net(g["R0"], g["risk0"]) for g in SIG)
print(f"BASE reproduzida: N{len(SIG)} bruto {sum(g['R0'] for g in SIG):.1f} NET {BASE_NET:.1f}")

# ---------- geometria estrutural: cj-p, fractal, SL causal? ----------
print("\n=== A0. ESTRUTURA cj-p / fractal / SL ===")
dist = {}
for g in SIG: dist[g["cj"] - g["p"]] = dist.get(g["cj"] - g["p"], 0) + 1
print(f"  cj-p nos 435: {dict(sorted(dist.items()))}")
distU = {}
n_frac_ok = n_slfut = 0
for r in ROWS:
    pr = PRIMK.get(r["block"])
    if not pr: continue
    s = pr["series"]; tmap = {b["t"]: i for i, b in enumerate(s)}
    p, cj = tmap.get(r["t"]), tmap.get(r["cj_t"])
    if p is None or cj is None: continue
    distU[cj - p] = distU.get(cj - p, 0) + 1
    if p >= 2 and p + 2 < len(s):
        L = [b["l"] for b in s]
        if L[p] <= min(L[p-2:p+3]): n_frac_ok += 1
print(f"  cj-p no universo: {dict(sorted(distU.items()))} | fractais k3 confirmados (low[p]=min p±2): {n_frac_ok}/{len(ROWS)}")
# SL usa min(low[p..cj]) — em quantos casos isso < low[p] (info futura na antecipação)?
for g in SIG:
    L = [b["l"] for b in g["s"]]
    if min(L[g["p"]:g["cj"] + 1]) < L[g["p"]] - 1e-12: n_slfut += 1
print(f"  SIG onde min(low[p..cj]) < low[p] (SL da antecipação usaria info futura): {n_slfut}/435")

# ---------- reproduzir seleção P1 exatamente ----------
HAS_OPEN = "o" in SIG[0]["s"][SIG[0]["cj"]]
def disp_ok(s, j, p, atr, C):
    b = s[j]
    if not (b["c"] > s[p]["h"]): return False
    body = (b["c"] - b["o"]) if HAS_OPEN else (b["c"] - s[j - 1]["c"])
    if body < 0.5 * atr: return False
    return b["c"] > ema_at(C, j, 21)
def recomp_gates(s, j, entry, sl, atr):
    risk = entry - sl
    if risk <= 0 or risk < RISK_FLOOR_USD or risk < RISK_FLOOR_ATR * atr: return False
    if regime_h(s[j]["t"]) == "BEAR": return False
    if (s[j].get("rsi") or 50) < QRSI: return False
    lo20 = min(x["l"] for x in s[max(0, j - 19):j + 1]); hi20 = max(x["h"] for x in s[max(0, j - 19):j + 1])
    return (entry - lo20) / ((hi20 - lo20) or atr) >= QPOS

ANT = []  # (g, fired_j)
for g in SIG:
    s, p, cj, atr, sl = g["s"], g["p"], g["cj"], g["atr"], g["sl"]
    C = [b["c"] for b in s]
    for j in (p + 1, p + 2):
        if j >= cj: break
        if disp_ok(s, j, p, atr, C) and recomp_gates(s, j, s[j]["c"], sl, atr):
            ANT.append((g, j)); break
print(f"\n=== A1. P1 HORIZONTE (letrun_from ancora fill vs cj) ===")
print(f"  antecipadas reproduzidas: {len(ANT)} (lab: 127)")
d_h = 0.0; n_hz_fill = n_hz_cj = 0; nd_diff = 0
for g, j in ANT:
    entry = g["s"][j]["c"]; risk = entry - g["sl"]
    R_f, hz_f = letrun_from(g["s"], j, entry, g["sl"], g["atr"])                 # como o lab
    R_c, hz_c = letrun_from(g["s"], j, entry, g["sl"], g["atr"], end_at=g["cj"])  # horizonte ancorado em cj
    n_hz_fill += hz_f; n_hz_cj += hz_c
    if abs(R_f - R_c) > 1e-12: nd_diff += 1
    d_h += (R_c - R_f)
print(f"  exits no fim do horizonte: fill-anchored {n_hz_fill} · cj-anchored {n_hz_cj} | trades com R diferente: {nd_diff}")
print(f"  Δbruto total (cj-anchored − fill-anchored) nas antecipadas: {d_h:+.3f}R")

# ---------- A1b. EMA fonte: ema_at vs bar['ema21'] ----------
n_flip = 0
for g in SIG:
    s, p, cj, atr, sl = g["s"], g["p"], g["cj"], g["atr"], g["sl"]
    C = [b["c"] for b in s]
    fired_a = fired_b = None
    for j in (p + 1, p + 2):
        if j >= cj: break
        b = s[j]; body = b["c"] - b["o"]
        base_ok = (b["c"] > s[p]["h"]) and body >= 0.5 * atr
        ok_a = base_ok and b["c"] > ema_at(C, j, 21)
        ok_b = base_ok and b["c"] > (b.get("ema21") or ema_at(C, j, 21))
        g_ok = recomp_gates(s, j, b["c"], sl, atr)
        if fired_a is None and ok_a and g_ok: fired_a = j
        if fired_b is None and ok_b and g_ok: fired_b = j
    if (fired_a is None) != (fired_b is None) or fired_a != fired_b: n_flip += 1
print(f"  sensibilidade EMA (ema_at aprox vs ema21 do bar): {n_flip}/435 decisões mudam")

# ---------- A3. NULL/LOOK-AHEAD: antecipar TODOS a p+1 ----------
print(f"\n=== A3. P1 NULL — antecipar TODOS os 435 em close(p+1) (sem gate) ===")
tot_all = 0.0; n_all = 0; n_skip = 0
for g in SIG:
    j = g["p"] + 1; entry = g["s"][j]["c"]; risk = entry - g["sl"]
    if risk > 0:
        R, _ = letrun_from(g["s"], j, entry, g["sl"], g["atr"])
        tot_all += net(R, risk); n_all += 1
    else:
        tot_all += net(g["R0"], g["risk0"]); n_skip += 1
print(f"  antecipar todos: NET {tot_all:+.1f} (base {BASE_NET:+.1f}, Δ {tot_all-BASE_NET:+.1f}) | risk<=0 fallback: {n_skip}")
# quantos dos 435 têm cj>p+2 (fractal k3 NÃO confirmado em p+1)? por definição todos com cj>=p+2
n_unconf1 = sum(1 for g in SIG if g["cj"] > g["p"] + 1)
n_unconf2 = sum(1 for g in SIG if g["cj"] > g["p"] + 2)
print(f"  fractal ainda-nao-confirmado no close p+1: {n_unconf1}/435 · no close p+2: {n_unconf2}/435")
# pareado do filtro: os 127 escolhidos vs os NÃO escolhidos, ambos antecipados a p+1
ant_idx = {id(g) for g, _ in ANT}
sel_d = unsel_d = 0.0; n_unsel = 0
for g in SIG:
    j = g["p"] + 1; entry = g["s"][j]["c"]; risk = entry - g["sl"]
    if risk <= 0: continue
    R, _ = letrun_from(g["s"], j, entry, g["sl"], g["atr"])
    dd = net(R, risk) - net(g["R0"], g["risk0"])
    if id(g) in ant_idx: sel_d += dd
    else: unsel_d += dd; n_unsel += 1
print(f"  Δ antecipação@p+1: escolhidos-pelo-filtro {sel_d:+.1f}R ({len(ANT)}) vs não-escolhidos {unsel_d:+.1f}R ({n_unsel})")

# ---------- A2. CLASSE FANTASMA NÃO-COBERTA: fractais que falham confirmação ----------
print(f"\n=== A2. CLASSE FANTASMA — proto-candidatos que NUNCA confirmam (fora do dataset) ===")
# proxy de swept_prior_low: calibrar contra o feature no universo
L20 = {}
def sweep_proxy(s, p, W):
    if p < W + 2: return False
    L = [b["l"] for b in s]
    return L[p] < min(L[p - W:p])
by_block = {}
for r in ROWS: by_block.setdefault(r["block"], []).append(r)
best = None
for W in (6, 12, 24, 48, 96):
    tp = fp = fn_ = tn = 0
    for r in ROWS:
        pr = PRIMK.get(r["block"])
        if not pr: continue
        s = pr["series"]; tmap = {b["t"]: i for i, b in enumerate(s)}
        p = tmap.get(r["t"])
        if p is None: continue
        pred = sweep_proxy(s, p, W); act = f(r, "swept_prior_low", 0) == 1
        if pred and act: tp += 1
        elif pred and not act: fp += 1
        elif act: fn_ += 1
        else: tn += 1
    acc = (tp + tn) / (tp + fp + fn_ + tn)
    print(f"  proxy sweep W={W}: acc {100*acc:.1f}% (tp{tp} fp{fp} fn{fn_} tn{tn})")
    if best is None or acc > best[1]: best = (W, acc)
WSW = best[0]
print(f"  → uso W={WSW} (melhor proxy, acc {100*best[1]:.1f}%) — ESTIMATIVA, não a definição exata do builder")
# enumerar proto-candidatos por bloco: p = low local esquerdo (low[p]<low[p-1],low[p-2]) + sweep proxy;
# antecipação live em j=p+1/p+2 com disp+recomp (mesmos gates do phantom scan do lab);
# classificar: CONFIRMA (low[p+1..p+2] > low[p]) vs FALHA (undercut antes da confirmação)
univ_pt = {}
for r in ROWS:
    pr = PRIMK.get(r["block"])
    if pr:
        tmap = {b["t"]: i for i, b in enumerate(pr["series"])}
        if tmap.get(r["t"]) is not None: univ_pt.setdefault(r["block"], set()).add(tmap[r["t"]])
n_conf = n_conf_in_univ = 0
fail_n = 0; fail_sum = 0.0; fail_R = []
for blk, pr in PRIMK.items():
    s = pr["series"]; L = [b["l"] for b in s]; C = [b["c"] for b in s]
    upts = univ_pt.get(blk, set())
    for p in range(WSW + 2, len(s) - 3):
        if not (L[p] < L[p - 1] and L[p] < L[p - 2]): continue
        if not sweep_proxy(s, p, WSW): continue
        atr = s[p]["atr"]
        if not atr: continue
        # live: tenta j=p+1; se p+1 não undercutou low[p], pode tentar p+2
        fired = None
        for j in (p + 1, p + 2):
            if j > p + 1 and L[p + 1] <= L[p]: break  # já invalidado antes de j
            slj = min(L[p:j + 1]) - 0.1 * atr
            if disp_ok(s, j, p, atr, C) and recomp_gates(s, j, s[j]["c"], slj, atr):
                fired = j; break
        if fired is None: continue
        confirmed = L[p + 1] > L[p] and L[p + 2] > L[p]
        if confirmed:
            n_conf += 1
            if p in upts: n_conf_in_univ += 1
        else:
            slj = min(L[p:fired + 1]) - 0.1 * atr
            entry = s[fired]["c"]; risk = entry - slj
            R, _ = letrun_from(s, fired, entry, slj, atr)
            if R is not None:
                fail_n += 1; fail_sum += net(R, risk); fail_R.append(net(R, risk))
print(f"  proto-candidatos c/ disp+gates: CONFIRMAM {n_conf} (destes {n_conf_in_univ} batem em p do universo)"
      f" · FALHAM confirmação {fail_n}")
if fail_n:
    fail_R.sort()
    print(f"  classe FALHA: sumR_NET {fail_sum:+.1f} · avg {fail_sum/fail_n:+.3f} · mediana {fail_R[fail_n//2]:+.3f}"
      f" · %loss {100*sum(1 for x in fail_R if x<=0)/fail_n:.0f}%")
    print(f"  razão falha/confirmada: {fail_n}/{n_conf} = {fail_n/max(1,n_conf):.2f} → por 127 antecipações live,"
      f" ~{127*fail_n/max(1,n_conf):.0f} entradas extra n/ dataset, drag estimado {127*fail_n/max(1,n_conf)*(fail_sum/fail_n):+.1f}R")

# ---------- A4. P2 same-bar física ----------
print(f"\n=== A4. P2 SAME-BAR / CANCEL ===")
def run_p2(samebar_mode):
    seq = []; miss = 0; fill = 0; samebar = 0
    for g in SIG:
        s, p, cj, atr, sl = g["s"], g["p"], g["cj"], g["atr"], g["sl"]
        stop = max(x["h"] for x in s[p:cj + 1]) + 0.05 * atr
        filled = False
        for k in range(cj + 1, min(cj + 8, len(s) - 1) + 1):
            b = s[k]
            gap_open = HAS_OPEN and b["o"] >= stop
            crossed = gap_open or b["h"] >= stop + 0.40
            if b["l"] <= sl and not crossed: break
            if crossed:
                fill_px = b["o"] if gap_open else stop
                risk = fill_px - sl
                if risk <= 0: break
                if b["l"] <= sl:
                    samebar += 1
                    if samebar_mode == "stop": R = -1.0
                    elif samebar_mode == "cancel": break
                    else: R, _ = letrun_from(s, k, fill_px, sl, atr)
                else:
                    R, _ = letrun_from(s, k, fill_px, sl, atr)
                seq.append((R, net(R, risk))); filled = True; fill += 1
                break
        if not filled: miss += 1
    return seq, fill, miss, samebar
for mode in ("stop", "cancel", "letrun"):
    seq, fill, miss, sb = run_p2(mode)
    print(f"  samebar={mode:<7} fill {fill} miss {miss} samebar-count {sb} | bruto {sum(x[0] for x in seq):+.1f} NET {sum(x[1] for x in seq):+.1f}")

# ---------- A5. P3 lentes — por que 1 corte ----------
print(f"\n=== A5. P3 LENTES no universo vs 435 ===")
sup_vals = sorted(f(r, "n_supply_overhead", 0) for r in ROWS)
q80 = sup_vals[int(0.80 * len(sup_vals))]
print(f"  n_supply_overhead: min {sup_vals[0]} q50 {sup_vals[len(sup_vals)//2]} q80 {q80} max {sup_vals[-1]}")
sig_sup = sorted(f(g['row'], 'n_supply_overhead', 0) for g in SIG)
print(f"  n_supply_overhead nos 435: min {sig_sup[0]} q50 {sig_sup[len(sig_sup)//2]} q80 {sig_sup[int(0.8*435)]} max {sig_sup[-1]}")
def lens3(r):
    return [f(r, "n_supply_overhead", 0) >= q80, f(r, "legpos90", 0) >= 0.75,
            f(r, "h1n_clean_sky_atr", 99) <= 0.35, f(r, "sell_bub_w", 0) >= 1]
names = ["supply>=q80", "legpos90>=.75", "cleansky<=.35", "sellbub>=1"]
for i, nm in enumerate(names):
    pu = sum(lens3(r)[i] for r in ROWS) / len(ROWS)
    pb = sum(lens3(g["row"])[i] for g in SIG) / len(SIG)
    print(f"  lente {nm:<14} pass-rate universo {100*pu:5.1f}% vs 435 {100*pb:5.1f}%")
votes = [sum(lens3(g["row"])) for g in SIG]
print(f"  votos 435: {[votes.count(k) for k in range(5)]} (>=3: {sum(1 for v in votes if v>=3)})")

# ---------- A6. P5 leitura risco-normalizada + streak por construção ----------
print(f"\n=== A6. P5 CONTABILIDADE ===")
EP_GAP = 96
eps = []; last_t = None
for i, g in enumerate(SIG):
    if last_t is not None and (g["t"] - last_t) <= EP_GAP * 900: eps[-1].append(i)
    else: eps.append([i])
    last_t = g["t"]
chain_pos = [0] * len(SIG)
for i in range(1, len(SIG)):
    a, b = SIG[i - 1], SIG[i]
    fl_a, fl_b = a["sl"] + 0.1 * a["atr"], b["sl"] + 0.1 * b["atr"]
    if (b["t"] - a["t"]) <= EP_GAP * 900 and a["R0"] <= 0 and abs(fl_b - fl_a) <= 1.0 * a["atr"]:
        chain_pos[i] = chain_pos[i - 1] + 1
W = {0: 0.5, 1: 0.3}
wts = [W.get(cp, 0.2) for cp in chain_pos]
def eqstats(vals):
    eq = pk = dd = 0.0
    for x in vals: eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
    return sum(vals), dd
nb = [net(g["R0"], g["risk0"]) for g in SIG]
sb_, db = eqstats(nb); sw_, dw = eqstats([w * x for w, x in zip(wts, nb)])
risk_alloc_b = len(SIG) * 1.0; risk_alloc_w = sum(wts)
print(f"  base:   sumNET {sb_:.1f} DDobs {db:.1f} sum/|DD| {abs(sb_/db):.2f} | risco alocado {risk_alloc_b:.0f}R → ret/riscoAlocado {sb_/risk_alloc_b:.3f}")
print(f"  budget: sumNET {sw_:.1f} DDobs {dw:.1f} sum/|DD| {abs(sw_/dw):.2f} | risco alocado {risk_alloc_w:.1f}R → ret/riscoAlocado {sw_/risk_alloc_w:.3f}")
print(f"  sum/DDq95 (boot do lab): base 233.6/22.2={233.6/22.2:.2f} vs budget 113.8/10.0={113.8/10.0:.2f}")
same_streak = all((x <= 0) == (w * x <= 0) for w, x in zip(wts, nb))
print(f"  streak: sinais(w*x)=sinais(x) para todos? {same_streak} → streak q95 igual é POR CONSTRUÇÃO (pesos>0 não mudam W/L)")

# ---------- A10. FN-gate aritmética base e P1 ----------
print(f"\n=== A10. FN-GATE ARITMÉTICA ===")
def panel(seq_net, seq_gross, yrs_net, costs):
    n = len(seq_net); w = sum(1 for x in seq_net if x > 0)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in seq_net:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    runners = sum(1 for x in seq_gross if x >= 3)
    cm = sorted(costs)[len(costs) // 2]
    return {"WR": 100 * w / n, "stk": mL, "run": runners, "sum": sum(seq_net), "yrs": yrs_net, "cm": cm}
def gate_line(tag, P):
    checks = {"WR>=50": P["WR"] >= 50, "stk<=6": P["stk"] <= 6, "run>=48": P["run"] >= 48,
              "sum>=200": P["sum"] >= 200, "anos+2024>=10": all(v > 0 for v in P["yrs"].values()) and P["yrs"][2024] >= 10,
              "cost<=0.15": P["cm"] <= 0.15}
    print(f"  {tag}: WR {P['WR']:.1f} stk {P['stk']} run {P['run']} sum {P['sum']:.1f} anos {P['yrs']} cost_med {P['cm']:.3f}"
          f" → {sum(checks.values())}/6 falha={[k for k,v in checks.items() if not v]}")
seqB = sorted((g["t"], g["yr"], g["R0"], net(g["R0"], g["risk0"])) for g in SIG)
yrsB = {y: sum(x[3] for x in seqB if x[1] == y) for y in (2024, 2025, 2026)}
gate_line("BASE", panel([x[3] for x in seqB], [x[2] for x in seqB], yrsB, [SB_USD / g["risk0"] for g in SIG]))
p1s = []; p1c = []
for g in SIG:
    hit = next((j for gg, j in ANT if gg is g), None)
    if hit is not None:
        entry = g["s"][hit]["c"]; risk = entry - g["sl"]
        R, _ = letrun_from(g["s"], hit, entry, g["sl"], g["atr"])
        p1s.append((g["s"][hit]["t"], g["yr"], R, net(R, risk))); p1c.append(SB_USD / risk)
    else:
        p1s.append((g["t"], g["yr"], g["R0"], net(g["R0"], g["risk0"]))); p1c.append(SB_USD / g["risk0"])
p1s.sort()
yrs1 = {y: sum(x[3] for x in p1s if x[1] == y) for y in (2024, 2025, 2026)}
gate_line("P1  ", panel([x[3] for x in p1s], [x[2] for x in p1s], yrs1, p1c))
print(f"  P1 NET aqui: {sum(x[3] for x in p1s):.1f} (lab: 257.1) | pareado Δ: "
      f"{sum(x[3] for x in p1s) - BASE_NET:+.1f}")

# ---------- A8b. seed-sensibilidade do null P1 ----------
print(f"\n=== A8b. NULL P1 com seeds alternativas (200 reps cada) ===")
obs_delta = sum(x[3] for x in p1s) - BASE_NET
for seed in (7, 99, 2024):
    rng = random.Random(seed); nd = []
    for _ in range(200):
        pick = set(rng.sample(range(len(SIG)), len(ANT)))
        tot = 0.0
        for i, g in enumerate(SIG):
            if i in pick:
                j = g["p"] + 1; entry = g["s"][j]["c"]; risk = entry - g["sl"]
                if risk > 0:
                    R, _ = letrun_from(g["s"], j, entry, g["sl"], g["atr"])
                    tot += net(R, risk); continue
            tot += net(g["R0"], g["risk0"])
        nd.append(tot - BASE_NET)
    nd.sort()
    p = sum(1 for d in nd if d >= obs_delta) / len(nd)
    print(f"  seed {seed}: null med {nd[100]:+.1f} q05 {nd[10]:+.1f} q95 {nd[190]:+.1f} → p={p:.3f} (obs Δ {obs_delta:+.1f})")

print("\nDA attack probes done.")
