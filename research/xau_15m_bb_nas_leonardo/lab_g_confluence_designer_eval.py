#!/usr/bin/env python3
"""
LAB G — DESIGNER DE CONFLUÊNCIA ESTRUTURAL (2026-07-03)
Avaliação reprodutível dos 2 sistemas FROZEN (S1 Doca Convergente, S2 Segundo Mergulho)
sobre results/lab_g_candidates.jsonl (4499 flush-lows causais, 2024-05→2026-05).

DISCIPLINA / LEDGER:
- Predicados congelados por TESE + calibração de FREQUÊNCIA (quantis), SEM olhar g_R.
- Variantes de frequência olhadas antes do freeze: S1=3 (K>=2/3/4), S2=4 (v1..v4).
- Olhadas de outcome pós-freeze: 1 painel por sistema + diagnósticos de falha
  (null aleatório + polaridade box96) DECLARADOS como outcome-informed.
- Status da rodada: EXPLORATORY_CALIBRATION. Nunca OOS/cross-asset.
"""
import json, random, datetime as dt
from collections import Counter
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "results", "lab_g_candidates.jsonl")

rows = [json.loads(l) for l in open(DATA)]
rows.sort(key=lambda r: r["t"])

# ---------------- FROZEN SYSTEM 1: DOCA CONVERGENTE ----------------
# Core duro: fundo do box96 (<=0.25) + doca de demanda nested; overlay por regime.
# Lentes (>=3 de 5): capitulação, exaustão, céu, viragem, sweep.
def lens_capit(r): return (r["sell_bub_w"] > 0) or (r["g_rsi_div"] == 1) or (r["g_flush_wick"] >= 0.59)
def lens_exh(r):   return (r["downleg_decel"] == 1) or (r["downleg_eff"] is not None and r["downleg_eff"] <= 0.09)
def lens_sky(r):   return (r["clean_sky_atr"] >= 0.19) or (r["n_supply_overhead"] <= 14)
def lens_turn(r):  return (r["h1n_choch_up_rec"] > 0) or (r["h4n_nas_long_rec"] > 0) or (r["reclaim_atr"] >= 1.37)
def lens_sweep(r): return (r["swept_prior_low"] == 1) and (r["g_sweep_depth"] is not None and r["g_sweep_depth"] >= 0.17)

def s1_core(r):
    if r["g_box96"] > 0.25: return False
    if not (r["in_demand"] == 1 and (r["h1n_in_demand"] or r["h4n_in_demand"])): return False
    reg = r["g_v5h"]
    if reg == "RANGE": return r["g_box480"] <= 0.40
    if reg == "BULL":  return 0.20 <= r["g_box480"] <= 0.80
    # BEAR: só pullback-bull confirmado
    return (r["h1_trend"] == 1 or r["h1n_trend"] == 1) and r["htf_demand_confluence"] == 1 and r["g_knife"] == 0

def s1_score(r): return sum([lens_capit(r), lens_exh(r), lens_sky(r), lens_turn(r), lens_sweep(r)])

def select_s1():
    sel, last, dayc = [], -10**12, {}
    for r in rows:
        if s1_core(r) and s1_score(r) >= 3 and r["t"] - last >= 16 * 900:  # dedupe 4h
            d = dt.datetime.utcfromtimestamp(r["t"]).strftime("%Y-%m-%d")
            if dayc.get(d, 0) >= 2: continue                                # cap 2/dia
            sel.append(r); last = r["t"]; dayc[d] = dayc.get(d, 0) + 1
    return sel

# ---------------- FROZEN SYSTEM 2: SEGUNDO MERGULHO (fail-then-fire) ----------------
def flush_low(r): return r["g_sl"] + 0.1 * r["g_atr"]

def s2_pred(r, prior):
    fl = flush_low(r); hit = None
    for j in prior:
        if abs(flush_low(j) - fl) <= 0.35 * r["g_atr"]: hit = j; break
    if hit is None: return False
    if r["g_box96"] > 0.40 or r["in_demand"] != 1: return False
    if not ((r["rsi_min8"] >= hit["rsi_low"] + 2.0) or (r["g_rsi_div"] == 1)): return False
    if not ((r["clean_sky_atr"] >= 0.19) or (r["n_supply_overhead"] <= 51)): return False
    if r["g_v5h"] == "BEAR" and not (r["h1_trend"] == 1 or r["h1n_trend"] == 1): return False
    return True

def select_s2():
    sel, last = [], -10**12
    for i, r in enumerate(rows):
        prior = [j for j in rows[max(0, i - 250):i] if 4 <= (r["t"] - j["t"]) / 900 <= 96]
        if s2_pred(r, prior) and r["t"] - last >= 16 * 900:
            sel.append(r); last = r["t"]
    return sel

# ---------------- PAINEL COMPLETO ----------------
def panel(sel, name):
    Rs = [r["g_R"] for r in sel]
    n = len(Rs); wr = sum(1 for x in Rs if x > 0) / n
    s = sum(Rs); eq = peak = dd = 0.0
    for x in Rs:
        eq += x; peak = max(peak, eq); dd = max(dd, peak - eq)
    streak = worst = 0
    for x in Rs:
        streak = streak + 1 if x <= 0 else 0
        worst = max(worst, streak)
    print(f"\n=== {name} ===")
    print(f"N={n} WR={wr:.1%} sumR={s:+.1f} avgR={s/n:+.3f} maxDD={dd:.1f}R ret/DD={s/dd:.2f} worst_loss_streak={worst}")
    for yr in sorted(set(r["yr"] for r in sel)):
        Ry = [r["g_R"] for r in sel if r["yr"] == yr]
        print(f"  {yr}: N={len(Ry)} WR={sum(1 for x in Ry if x>0)/len(Ry):.1%} sumR={sum(Ry):+.1f} avgR={sum(Ry)/len(Ry):+.3f}")
    for reg in ["RANGE", "BULL", "BEAR"]:
        Rg = [r["g_R"] for r in sel if r["g_v5h"] == reg]
        if Rg:
            print(f"  {reg}: N={len(Rg)} WR={sum(1 for x in Rg if x>0)/len(Rg):.1%} sumR={sum(Rg):+.1f} avgR={sum(Rg)/len(Rg):+.3f}")
    print(f"  overlap_base435={sum(1 for r in sel if r['g_in_base435'])}/{n}")
    wks = Counter(r["g_week"] for r in sel)
    print(f"  weeks_active={len(wks)} max/wk={max(wks.values())} avg/wk={n/104:.2f}")
    return Rs

# ---------------- NULL: sorteios aleatórios de mesmo N (mesmo mix de regime) ----------------
def null_test(sel, n_draws=1000, seed=7):
    rnd = random.Random(seed)
    mix = Counter(r["g_v5h"] for r in sel)
    pool = {reg: [r["g_R"] for r in rows if r["g_v5h"] == reg] for reg in mix}
    obs_sum = sum(r["g_R"] for r in sel)
    obs_wr = sum(1 for r in sel if r["g_R"] > 0) / len(sel)
    sums, wrs = [], []
    for _ in range(n_draws):
        draw = []
        for reg, k in mix.items():
            draw += rnd.sample(pool[reg], k)
        sums.append(sum(draw)); wrs.append(sum(1 for x in draw if x > 0) / len(draw))
    p_sum = sum(1 for x in sums if x >= obs_sum) / n_draws
    p_wr = sum(1 for x in wrs if x >= obs_wr) / n_draws
    print(f"  NULL(regime-matched, {n_draws} draws): obs_sumR={obs_sum:+.1f} p(sum>=obs)={p_sum:.3f} | obs_WR={obs_wr:.1%} p(WR>=obs)={p_wr:.3f}")

# ---------------- DIAGNÓSTICO DE FALHA (outcome-informed, declarado) ----------------
def box96_polarity():
    print("\n--- DIAGNÓSTICO (outcome-informed, NÃO usar como predicado sem novo freeze) ---")
    print("WR e avgR por bin de g_box96 (população toda):")
    bins = [(0, .2), (.2, .4), (.4, .6), (.6, .8), (.8, 1.01)]
    for lo, hi in bins:
        Rs = [r["g_R"] for r in rows if lo <= r["g_box96"] < hi]
        if Rs:
            print(f"  box96 [{lo:.1f},{hi:.1f}): N={len(Rs)} WR={sum(1 for x in Rs if x>0)/len(Rs):.1%} avgR={sum(Rs)/len(Rs):+.3f}")
    base = [r["g_R"] for r in rows if r["g_in_base435"]]
    print(f"  ref base435: N={len(base)} WR={sum(1 for x in base if x>0)/len(base):.1%} avgR={sum(base)/len(base):+.3f}")
    allR = [r["g_R"] for r in rows]
    print(f"  populacao:   N={len(allR)} WR={sum(1 for x in allR if x>0)/len(allR):.1%} avgR={sum(allR)/len(allR):+.3f}")

if __name__ == "__main__":
    s1 = select_s1(); s2 = select_s2()
    panel(s1, "S1 DOCA CONVERGENTE (frozen)"); null_test(s1)
    panel(s2, "S2 SEGUNDO MERGULHO (frozen)"); null_test(s2)
    t1 = {r["t"] for r in s1}
    print(f"\nS1∩S2 = {sum(1 for r in s2 if r['t'] in t1)}")
    box96_polarity()
