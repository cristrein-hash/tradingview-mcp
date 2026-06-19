#!/usr/bin/env python3
"""AGGREGATOR v1 — DIAGNÓSTICO (laboratório, NÃO promoção). Escopo XAU_4H_L2_BPT_BOS_CHOCH.
Corrige os 6 erros do v0. Lógica = docs/XAU_4H_L2_BPT_AGGREGATOR_V1_DIAGNOSTIC_SPEC.md (definida ANTES).
Roda sobre a população COMPLETA 276. Outcome só pós-hoc. NÃO altera engine/decisions_merged/registry-promoted.
Produz: decisions(ledger), summary, vs_old_v0, error_analysis, frequency_report, da.
"""
import csv, json, glob, os, math
from collections import Counter, defaultdict
D = "results"
mat = {(int(r['episode_id']), r['specialist_id']): r for r in csv.DictReader(open(f"{D}/l2_bpt_specialist_ablation_ready_matrix.csv"))}
net = {}
for fp in glob.glob(f"{D}/specialist_out/*.jsonl"):
    fam = os.path.basename(fp)[:-6]
    for l in open(fp):
        if l.strip():
            r = json.loads(l); net[(int(r['episode_id']), fam)] = r.get('net_read')
out = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
dec = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_decisions_merged.csv"))}
sa = {int(json.loads(l)['_bar_idx']): json.loads(l).get('context_label') for l in open(f"{D}/l2_bpt_stage_a_context_labels.jsonl")}
v0 = {}
fp0 = f"{D}/l2_bpt_aggregator_v0_decisions.csv"
if os.path.exists(fp0):
    v0 = {int(r['bar_idx']): r['agg_decision'] for r in csv.DictReader(open(fp0))}
SPECS = ["nas", "demand_supply", "risk_sl", "exhaustion_top", "capitulation", "rsi_momentum", "bubbles", "bull_beta", "volume_vp", "devils_advocate"]
EP = sorted(set(i for i, _ in mat if i in out))
def veto(i, s): return int(mat.get((i, s), {}).get('veto_count', '0') or 0) > 0
def review(i, s): return int(mat.get((i, s), {}).get('review_flag_count', '0') or 0) > 0
def state(i, s):
    if veto(i, s): return 'veto'
    st = net.get((i, s), 'neutral')
    if review(i, s) and st == 'neutral': return 'review_flag'
    return st
def R(i): return float(out[i]['realR'])
def Rd(i): return 6.0 if out[i]['exitype'] == 'WIN_RUNNER' else R(i)
def hit2(i): return out[i]['exitype'].startswith('WIN')
def runner(i): return out[i]['exitype'] == 'WIN_RUNNER'
def stop(i): return out[i]['exitype'] == 'STOP_LOSS'
def scratch(i): return out[i]['exitype'] == 'SCRATCH'
def dt(i): return out[i]['datetime']
PERMITTED = {'bottom_reversal_capitulation', 'demand_reclaim', 'bull_pullback_continuation', 'liquidity_sweep_reversal'}

def v1(i):
    st = {s: state(i, s) for s in SPECS}; ctx = sa.get(i, '')
    nas_sup = st['nas'] == 'supportive'; ds_sup = st['demand_supply'] == 'supportive'; rs_sup = st['risk_sl'] == 'supportive'
    ds_hos = st['demand_supply'] == 'hostile'; rs_bad = st['risk_sl'] in ('hostile', 'veto'); exh_hos = st['exhaustion_top'] == 'hostile'
    da_veto = st['devils_advocate'] == 'veto'; capit_rsi = st['capitulation'] == 'supportive' and st['rsi_momentum'] == 'supportive'
    anchor = nas_sup or (ds_sup and rs_sup)
    supports = [s for s in ('nas', 'demand_supply', 'risk_sl', 'exhaustion_top') if st[s] == 'supportive']
    if capit_rsi: supports.append('capit+rsi')
    conflicts = [s for s in SPECS if st[s] in ('hostile', 'veto')]
    # FATAL -> SKIP
    fatal = None
    if ctx == 'late_top_exhaustion': fatal = 'late_top_context'
    elif exh_hos and not nas_sup: fatal = 'exhaustion_hostile_no_bottom'
    elif ds_hos and rs_bad: fatal = 'no_demand_bad_risk'
    elif (not anchor) and ctx in ('bear_bounce', 'late_top_exhaustion') and not capit_rsi: fatal = 'no_anchor_adverse_ctx'
    if fatal: return 'SKIP', f"FATAL:{fatal}", supports, conflicts, st, ctx
    common_veto = da_veto or st['risk_sl'] == 'veto' or exh_hos
    if anchor:
        if common_veto: d, why = 'REVIEW', 'anchor_but_common_veto'
        elif ctx in ('bear_bounce', 'mid_range_noise') and not capit_rsi: d, why = 'REVIEW', 'anchor_but_ctx_conflict'
        else: d, why = 'TAKE', 'anchor_clean'
    else:
        permitted = ctx not in ('bear_bounce', 'late_top_exhaustion') and not rs_bad and not ds_hos
        if (capit_rsi and permitted and (ds_sup or rs_sup or nas_sup)): d, why = 'REVIEW', 'no_anchor_capit_rsi_refine'
        elif (ds_sup or rs_sup or nas_sup): d, why = 'REVIEW', 'no_anchor_partial_support'
        else: d, why = 'SKIP', 'no_anchor_no_support'
    # elevação capit+rsi REVIEW->TAKE (regime-bound)
    if d == 'REVIEW' and capit_rsi and anchor and ctx in PERMITTED and not common_veto and not ds_hos and not rs_bad:
        d, why = 'TAKE', 'capit_rsi_elevated_permitted_ctx'
    return d, why, supports, conflicts, st, ctx

# ---- ledger ----
led = []
for i in EP:
    d, why, sup, conf, st, ctx = v1(i)
    led.append(dict(episode_id=i, datetime=dt(i), old_decision=dec.get(i, {}).get('decision', ''),
        agg_v0_decision=v0.get(i, ''), agg_v1_decision=d, stage_a_context=ctx,
        nas_state=st['nas'], demand_supply_state=st['demand_supply'], risk_sl_state=st['risk_sl'],
        exhaustion_top_state=st['exhaustion_top'], capit_rsi_layer_state=('supportive' if (st['capitulation'] == 'supportive' and st['rsi_momentum'] == 'supportive') else 'no'),
        da_veto_state=st['devils_advocate'], main_supports='|'.join(sup), main_conflicts='|'.join(conf),
        final_reason=why, outcome=('WIN' if hit2(i) else ('STOP' if stop(i) else 'SCRATCH')),
        realR=out[i]['realR'], de_capped_R=round(Rd(i), 2), exit_type=out[i]['exitype']))
lc = list(led[0].keys())
with open(f"{D}/l2_bpt_aggregator_v1_decisions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=lc); w.writeheader(); w.writerows(led)

# ---- métricas ----
def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k/n; den = 1+z*z/n; c = (p+z*z/(2*n))/den; h = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return (max(0, c-h), min(1, c+h))
def pf(ids):
    pos = sum(Rd(i) for i in ids if Rd(i) > 0); neg = -sum(Rd(i) for i in ids if Rd(i) < 0)
    return round(pos/neg, 2) if neg > 0 else (float('inf') if pos > 0 else 0)
def maxdd(ids):
    seq = [Rd(i) for i in sorted(ids, key=dt)]; peak = cum = ddv = 0
    for r in seq: cum += r; peak = max(peak, cum); ddv = min(ddv, cum-peak)
    return round(ddv, 2)
def streak(ids):
    cur = mx = 0
    for i in sorted(ids, key=dt):
        if not hit2(i): cur += 1; mx = max(mx, cur)
        else: cur = 0
    return mx
YEARS = 6.34
def m(ids, label):
    ids = list(ids); n = len(ids)
    if not n: return dict(bucket=label, n=0)
    Rds = sorted(Rd(i) for i in ids); d2 = sum(Rds[:-2])/(n-2) if n > 2 else sum(Rds)/n
    k2 = sum(1 for i in ids if hit2(i)); lo, hi = wilson(k2, n)
    return dict(bucket=label, n=n, per_year=round(n/YEARS, 1), exp_decap=round(sum(Rd(i) for i in ids)/n, 3),
        sumR_decap=round(sum(Rd(i) for i in ids), 1), pf=pf(ids), hit2R=round(100*k2/n),
        hit3R=round(100*sum(1 for i in ids if runner(i))/n), stop=round(100*sum(1 for i in ids if stop(i))/n),
        scratch=round(100*sum(1 for i in ids if scratch(i))/n), drop2=round(d2, 3), maxDD=maxdd(ids),
        streak=streak(ids), wilson=f"[{lo:.2f},{hi:.2f}]")
agg = {d: [i for i in EP if v1(i)[0] == d] for d in ("TAKE", "REVIEW", "SKIP")}
old = {d: [i for i in EP if dec.get(i, {}).get('decision') == d] for d in ("TAKE", "REVIEW", "SKIP")}
v0t = [i for i in EP if v0.get(i) == 'TAKE']
summ = [m(agg["TAKE"], "V1_TAKE"), m(agg["REVIEW"], "V1_REVIEW"), m(agg["SKIP"], "V1_SKIP"),
        m(old["TAKE"], "OLD_TAKE"), m(v0t, "V0_TAKE"), m(EP, "ALL_276")]
mc = ['bucket', 'n', 'per_year', 'exp_decap', 'sumR_decap', 'pf', 'hit2R', 'hit3R', 'stop', 'scratch', 'drop2', 'maxDD', 'streak', 'wilson']
with open(f"{D}/l2_bpt_aggregator_v1_summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=mc, extrasaction='ignore'); w.writeheader(); w.writerows(summ)

# ---- vs old/v0 ----
at = set(agg["TAKE"])
old_take = set(old["TAKE"])
kept = at & old_take; dropped = old_take - at; new_take = at - old_take
new_from = Counter(dec.get(i, {}).get('decision', '') for i in new_take)
new_take_win = sum(1 for i in new_take if hit2(i)); new_take_stop = sum(1 for i in new_take if stop(i))
dropped_win = sum(1 for i in dropped if hit2(i))
with open(f"{D}/l2_bpt_aggregator_v1_vs_old_v0.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["question", "value", "detail"])
    w.writerow(["v1_TAKE_vs_v0", f"{len(at)} vs {len(v0t)}", "frequência"])
    w.writerow(["v1_TAKE_vs_old", f"{len(at)} vs {len(old_take)}", ""])
    w.writerow(["old_TAKE_kept", len(kept), f"de {len(old_take)}"])
    w.writerow(["old_TAKE_dropped", len(dropped), f"dos quais {dropped_win} eram winners"])
    w.writerow(["new_TAKE(not old)", len(new_take), f"vindos de {dict(new_from)}"])
    w.writerow(["new_TAKE_quality", f"{new_take_win}W/{new_take_stop}stop", f"de {len(new_take)} novos"])
    w.writerow([])
    w.writerow(["bucket", "n", "exp_decap", "pf", "hit2R"])
    for r in summ:
        if r['n']: w.writerow([r['bucket'], r['n'], r.get('exp_decap'), r.get('pf'), r.get('hit2R')])

# ---- error analysis (trade-a-trade, classificado) ----
def classify_error(i):
    d, why, sup, conf, st, ctx = v1(i)
    errs = []
    if d == 'TAKE' and stop(i):
        if ctx in ('bear_bounce',): errs.append('BEAR_CONTINUATION_ACCEPTED')
        elif ctx == 'late_top_exhaustion' or st['exhaustion_top'] == 'hostile': errs.append('LATE_TOP_ACCEPTED')
        elif st['demand_supply'] == 'supportive': errs.append('DEMAND_SUPPLY_FALSE_POSITIVE')
        else: errs.append('OTHER')
    if d == 'SKIP' and hit2(i):
        if why.startswith('FATAL'): errs.append('VETO_TOO_HARD')
        elif st['nas'] != 'supportive': errs.append('NAS_OVERREQUIRED')
        else: errs.append('GOOD_REVIEW_NOT_TAKE')
    if d == 'REVIEW' and hit2(i) and runner(i):
        errs.append('GOOD_REVIEW_NOT_TAKE')  # winner-runner ficou em review
    if d == 'TAKE' and (st['capitulation'] == 'supportive' and st['rsi_momentum'] == 'supportive') and stop(i) and ctx not in PERMITTED:
        errs.append('CAPIT_RSI_CONTEXT_MISUSED')
    return errs
erows = []
ecount = Counter()
for i in EP:
    es = classify_error(i)
    for e in es:
        ecount[e] += 1
        d, why, sup, conf, st, ctx = v1(i)
        erows.append(dict(episode_id=i, datetime=dt(i), agg_v1=d, error=e, stage_a=ctx,
            realR=out[i]['realR'], exit=out[i]['exitype'], reason=why))
with open(f"{D}/l2_bpt_aggregator_v1_error_analysis.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=['episode_id', 'datetime', 'agg_v1', 'error', 'stage_a', 'realR', 'exit', 'reason'])
    w.writeheader(); w.writerows(erows)

# ---- frequency report ----
def yr(i): return dt(i)[:4]
fr = []
for d in ("TAKE", "REVIEW", "SKIP"):
    yc = Counter(yr(i) for i in agg[d])
    fr.append(dict(bucket=f"V1_{d}", per_year=round(len(agg[d])/YEARS, 1), by_year=json.dumps(dict(sorted(yc.items())))))
tr = agg["TAKE"] + agg["REVIEW"]
fr.append(dict(bucket="V1_TAKE+REVIEW", per_year=round(len(tr)/YEARS, 1), by_year=json.dumps(dict(sorted(Counter(yr(i) for i in tr).items())))))
ctx_take = Counter(sa.get(i, '') for i in agg["TAKE"])
fr.append(dict(bucket="V1_TAKE_by_context", per_year="", by_year=json.dumps(dict(ctx_take))))
with open(f"{D}/l2_bpt_aggregator_v1_frequency_report.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=['bucket', 'per_year', 'by_year']); w.writeheader(); w.writerows(fr)

# ---- DA ----
da = [
 ("v1_diagnostico_nao_promocao", "YES", "simulado; registry/library NÃO promoted"),
 ("engine_oficial_intocado", "YES", "0 builder/decisions_merged alterado"),
 ("decisions_merged_intocado", "YES", "só lido p/ comparação"),
 ("sem_telegram_producao", "YES", "nada vai a sinal real"),
 ("sem_registry_library_promoted", "YES", "status capit+rsi segue CONTEXT_ONLY"),
 ("sem_subset_amostra", "YES", f"rodou sobre TODOS os {len(EP)} (população completa)"),
 ("comparou_old_e_v0", "YES", "OLD_TAKE + V0_TAKE no summary/vs"),
 ("avaliou_lucro_freq_dd_streak", "YES", "expectancy/PF/sumR/DD/streak/freq, não só hit-rate"),
 ("identificou_erros", "YES", f"error_analysis: {dict(ecount)}"),
 ("producao_intacta", "YES", "sem chart/MCP/plot/SLIM/receiver"),
]
with open(f"{D}/l2_bpt_aggregator_v1_da.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["check", "result", "detail"]); [w.writerow(r) for r in da]

print("=== AGGREGATOR v1 DIAGNÓSTICO (276, SIMULADO) ===")
for r in summ:
    if r['n']: print(f"  {r['bucket']:<11} n={r['n']:<3} ({r['per_year']}/y) exp={r.get('exp_decap'):>6} sumR={r.get('sumR_decap'):>6} pf={r.get('pf'):>5} hit2={r.get('hit2R')}% maxDD={r.get('maxDD')} streak={r.get('streak')} wilson={r.get('wilson')}")
print(f"\n  old_TAKE kept {len(kept)}/{len(old_take)} | dropped {len(dropped)} (winners {dropped_win}) | new_TAKE {len(new_take)} ({new_take_win}W/{new_take_stop}stop) from {dict(new_from)}")
print(f"  errors: {dict(ecount)}")
