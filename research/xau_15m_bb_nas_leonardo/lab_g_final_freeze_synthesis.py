#!/usr/bin/env python3
"""
LAB G — FINAL FREEZE SYNTHESIS (2026-07-03)
Sintese propria desta sessao (nada foi delegado; o parecer adversarial DA-pre
citado abaixo ja estava REGISTRADO e chegou como material de entrada).

Materializes the synthesis checks behind the frozen final specs (Systems A/B).
STATUS: EXPLORATORY_CALIBRATION. This script performs:
  R1) Byte-exact REPRODUCTION of System A (capit S2-BULL EMA-SHAKEOUT standalone)
      — registered look, reproduction only (claim: N53 WR62.3% +29.8R).
  R2) Byte-exact REPRODUCTION of System B (PoT-Map v2, literal spec text
      downleg_eff <= 0.33) vs the DA-pre report's inverted-veto variant —
      resolves DA-pre point 1.4.1 (the DA-pre report's own re-implementation
      was the buggy one; the literal text reproduces the claimed panel).
  S3) Structural (outcome-blind) lens-redundancy check: corr(reclaim_atr,
      g_rec_speed), corr(g_cj_body, confirm_body_atr) — DA-pre point 1.4.2.
  F4) OUTCOME-BLIND frequency calibration for System B-corrected (lens-4
      removed per DA-pre mandate): k in {1,2} of 3 remaining lenses, frequency
      per regime-week ONLY (g_R never touched in F4).
Ledger impact: ZERO new outcome looks (R1/R2 reproduce already-registered
panels; F4 is frequency-only). Commit fica com o Cris/sessao principal —
esta sessao nao commita sem autorizacao.
"""
import json, statistics
from collections import Counter, defaultdict

PATH = '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results/lab_g_candidates.jsonl'
ROWS = sorted((json.loads(l) for l in open(PATH)), key=lambda r: r['cj_t'])
assert len(ROWS) == 4499, f'universe changed: {len(ROWS)}'

SB_COST = 0.8  # $0.80 spread+commission per trade, in price units -> cost_R = 0.8/g_risk

def panel(sel, name):
    Rs = [r['g_R'] for r in sel]
    net = [x - SB_COST / r['g_risk'] for x, r in zip(Rs, sel)]
    def block(v):
        wr = sum(1 for x in v if x > 0) / len(v) * 100
        eq = mx = dd = 0.0
        for x in v:
            eq += x; mx = max(mx, eq); dd = min(dd, eq - mx)
        st = w = 0
        for x in v:
            w = w - 1 if x <= 0 else 0; st = min(st, w)
        return f'N{len(v)} WR{wr:.1f}% sum{sum(v):+.1f} avg{sum(v)/len(v):+.3f} DD{dd:.1f} stk{st}'
    yr = defaultdict(list)
    for r in sel: yr[r['yr']].append(r['g_R'])
    reg = defaultdict(list)
    for r in sel: reg[r['g_v5h']].append(r['g_R'])
    print(f'[{name}]')
    print('  GROSS:', block(Rs))
    print('  NET  :', block(net))
    print('  by-yr:', {y: f'{sum(v):+.1f}(N{len(v)})' for y, v in sorted(yr.items())})
    print('  by-rg:', {g: f'{sum(v):+.1f}(N{len(v)})' for g, v in sorted(reg.items())})

# ---------------- SYSTEM A: capit S2-BULL EMA-SHAKEOUT (standalone freeze) ----
def sysA(r):
    return (r['g_v5h'] == 'BULL'
            and r['h1_trend'] == 1 and (r.get('h1_pos') or 0) >= 0.33
            and (r['above_ema21'] == 0 or r['reclaim_ema_bars'] <= 3)
            and (r['g_atr_spike'] >= 1.27 or r['g_downrun'] >= 3)
            and (r['in_demand'] == 1 or r['htf_demand_any'] == 1)
            and (r['g_rec_speed'] >= 0.69 or r['reclaim_atr'] >= 2.0)
            and r['g_knife'] == 0)

# ---------------- SYSTEM B: PoT-Map v2 (literal frozen text) ------------------
def knife_ok(r): return r['g_knife'] == 0 or (r['g_rsi_div'] == 1 or r['sell_bub_w'] >= 4)
def pot(r): return r['reclaim_atr'] >= 1.35 and (r['g_cj_body'] >= 0.40 or r['up_closes_pc'] >= 3)
def lenses4(r):
    return [r['sell_bub_w'] >= 4 or r['g_rsi_div'] == 1,
            r['h1n_choch_up_rec'] == 1 or r['nas_long_16'] >= 1,
            r['h1n_in_demand'] == 1 or r['htf_demand_confluence'] == 1,
            r['g_rec_speed'] >= 0.65]
def lenses3(r): return lenses4(r)[:3]  # lens-4 removed per DA-pre mandate (corr with core)

def sysB(r, veto='le', L=lenses4, k=2):
    reg = r['g_v5h']
    if reg == 'BEAR':
        return r['g_bear_pullback_ok'] == 1 and knife_ok(r)
    need = k + (1 if r['g_regime_flip5d'] else 0)
    if reg == 'RANGE':
        v = (r['downleg_eff'] <= 0.33) if veto == 'le' else (r['downleg_eff'] >= 0.33)
        return (pot(r) and knife_ok(r) and r['g_box96'] <= 0.60 and v
                and sum(L(r)) >= need)
    if reg == 'BULL':
        return (pot(r) and knife_ok(r) and r['h1n_trend'] == 1 and r['h4n_trend'] == 1
                and (r['g_ema21_dist'] <= 0.20 or r['in_demand'] == 1)
                and sum(L(r)) >= need)
    return False

def day_cap(ps, cap=2):
    out, c = [], Counter()
    for r in ps:
        d = r['cj_t'] // 86400
        if c[d] < cap:
            c[d] += 1; out.append(r)
    return out

def regime_weeks():
    wk = defaultdict(Counter)
    for r in ROWS: wk[r['g_week']][r['g_v5h']] += 1
    return Counter({w: c.most_common(1)[0][0] for w, c in wk.items()}.values())

NW = regime_weeks()

def freq(sel, name):
    wr = defaultdict(Counter)
    for r in ROWS: wr[r['g_week']][r['g_v5h']] += 1
    wmap = {w: c.most_common(1)[0][0] for w, c in wr.items()}
    t = Counter(wmap[r['g_week']] for r in sel)
    print(f'  freq[{name}]:', {g: f'{t[g]}/{NW[g]}wk = {t[g]/NW[g]:.2f}/wk' for g in ('RANGE', 'BULL', 'BEAR')})

if __name__ == '__main__':
    print('== R1: System A reproduction (registered look) ==')
    A = [r for r in ROWS if sysA(r)]
    panel(A, 'SYSTEM A — EMA-SHAKEOUT BULL standalone (claim N53 WR62.3 +29.8/+25.9net)')
    freq(A, 'A')

    print('\n== R2: System B veto-direction resolution (registered look) ==')
    for v in ('le', 'ge'):
        B = day_cap([r for r in ROWS if sysB(r, veto=v)], 2)
        panel(B, f'SYSTEM B — PoT-Map v2 downleg_eff veto "{v} 0.33" (claim le: N197 +51.3)')
    freq(day_cap([r for r in ROWS if sysB(r, veto='le')], 2), 'B-literal')

    print('\n== S3: lens redundancy (outcome-blind structural) ==')
    def corr(a, b):
        ma, mb = statistics.mean(a), statistics.mean(b)
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
        return num / den
    print('  corr(reclaim_atr, g_rec_speed) =', round(corr([r['reclaim_atr'] for r in ROWS], [r['g_rec_speed'] for r in ROWS]), 3))
    print('  corr(g_cj_body, confirm_body_atr) =', round(corr([r['g_cj_body'] for r in ROWS], [r['confirm_body_atr'] for r in ROWS]), 3))
    core_pass = [r for r in ROWS if pot(r)]
    l4 = sum(1 for r in core_pass if r['g_rec_speed'] >= 0.65)
    print(f'  P(lens4 | PoT core) = {l4}/{len(core_pass)} = {l4/len(core_pass):.2f}')

    print('\n== F4: OUTCOME-BLIND frequency calibration, System B-corrected (3 lenses) ==')
    for k in (1, 2):
        sel = day_cap([r for r in ROWS if sysB(r, veto='le', L=lenses3, k=k)], 2)
        freq(sel, f'B-corrected k>={k}/3')
    # FROZEN mixed config (chosen by frequency bands only): RANGE k>=2/3, BULL k>=1/3,
    # BEAR = stand-aside (outcome-informed decision from the regimemap round, carried
    # as frozen hypothesis; re-evaluate only at >=25 new BEAR pullback-ok cases).
    def sysB_frozen(r):
        if r['g_v5h'] == 'BEAR':
            return False  # stand-aside
        k = 2 if r['g_v5h'] == 'RANGE' else 1
        return sysB(r, veto='le', L=lenses3, k=k)
    selF = day_cap([r for r in ROWS if sysB_frozen(r)], 2)
    freq(selF, 'B-FROZEN (RANGE k2 / BULL k1 / BEAR stand-aside, day-cap2)')
    print(f'  B-FROZEN total picks: {len(selF)} over {sum(NW.values())} weeks = {len(selF)/sum(NW.values()):.2f}/wk overall')
    # NOTE: no g_R touched for any B-corrected/B-FROZEN variant — panel belongs to the execution round.
