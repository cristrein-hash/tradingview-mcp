#!/usr/bin/env python3
"""AGGREGATOR v0 — DIAGNÓSTICO (laboratório, NÃO promoção). Escopo XAU_4H_L2_BPT_BOS_CHOCH.
Simula como um aggregator combinaria os 10 especialistas em TAKE/REVIEW/SKIP hipotético sobre os 276
episódios (população COMPLETA — anti-amostra). Mede frequência/lucro/DD/streak, compara com o engine
antigo, e expõe a matriz inteira para ver erros. NÃO vira regra/produção/Telegram, NÃO promove,
NÃO altera registry/decisions_merged. PESOS = escolhas de design v0 EXPLÍCITAS e revisáveis (ancoradas
nos achados Fase 2B/2B.5), NÃO tunadas ao outcome. Outcome cruzado só pós-hoc.
"""
import csv, json, glob, os, math
from collections import Counter, defaultdict
D = "results"

# ---- PESOS v0 (DESIGN CHOICE — revisar; ancorados em Fase 2B: nas decisive, demand/risk supporting,
#      capit+rsi context/refutado-OOS, volume noisy, bubbles/bull_beta context, DA/exhaustion veto) ----
W_SUPPORT = {"nas": 2.0, "demand_supply": 1.0, "risk_sl": 1.0, "exhaustion_top": 1.0,
             "capitulation": 0.5, "rsi_momentum": 0.5, "bubbles": 0.5, "bull_beta": 0.5, "volume_vp": 0.0}
W_HOSTILE = {"nas": 2.0, "demand_supply": 1.0, "risk_sl": 1.0}   # hostil desconta só os credíveis
CONFLUENCE_BONUS = 0.5     # capit & rsi ambos supportive
TAKE_THRESHOLD = 3.0       # score >= -> TAKE
# VETO -> SKIP:
def is_veto(st):
    return (st.get("devils_advocate") == "veto" or st.get("risk_sl") == "veto"
            or st.get("exhaustion_top") == "hostile")

# ---- dados ----
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
def stop(i): return out[i]['exitype'] == 'STOP_LOSS'
def dt(i): return out[i]['datetime']

def aggregate(i):
    st = {s: state(i, s) for s in SPECS}
    if is_veto(st):
        return "SKIP", 0.0, "VETO", st
    score = 0.0
    for s, w in W_SUPPORT.items():
        if st.get(s) == "supportive": score += w
    for s, w in W_HOSTILE.items():
        if st.get(s) == "hostile": score -= w
    if st.get("capitulation") == "supportive" and st.get("rsi_momentum") == "supportive":
        score += CONFLUENCE_BONUS
    if score <= 0: d = "SKIP"
    elif score >= TAKE_THRESHOLD: d = "TAKE"
    else: d = "REVIEW"
    return d, round(score, 2), "SCORE", st

# ---- ledger completo (276) ----
ledger = []
for i in EP:
    d, sc, why, st = aggregate(i)
    ledger.append(dict(bar_idx=i, datetime=dt(i), direction=dec.get(i, {}).get('direction', ''),
        stage_a=sa.get(i, ''), agg_decision=d, agg_score=sc, agg_reason=why,
        old_decision=dec.get(i, {}).get('decision', ''), realR=out[i]['realR'], exitype=out[i]['exitype'],
        **{f"st_{s}": st[s] for s in SPECS}))
cols = ['bar_idx', 'datetime', 'direction', 'stage_a', 'agg_decision', 'agg_score', 'agg_reason',
        'old_decision', 'realR', 'exitype'] + [f"st_{s}" for s in SPECS]
with open(f"{D}/l2_bpt_aggregator_v0_decisions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(ledger)

# ---- métricas por decisão ----
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
    k2 = sum(1 for i in ids if hit2(i)); lo, hi = wilson(k2, n)
    return dict(bucket=label, n=n, per_year=round(n/YEARS, 1), exp_decap=round(sum(Rd(i) for i in ids)/n, 3),
        sumR_decap=round(sum(Rd(i) for i in ids), 1), pf=pf(ids), hit2R=round(100*k2/n),
        stop=round(100*sum(1 for i in ids if stop(i))/n), maxDD=maxdd(ids), streak=streak(ids),
        wilson_hit2=f"[{lo:.2f},{hi:.2f}]", longs=sum(1 for i in ids if dec.get(i, {}).get('direction') == 'LONG'))
agg = {d: [i for i in EP if aggregate(i)[0] == d] for d in ("TAKE", "REVIEW", "SKIP")}
old = {d: [i for i in EP if dec.get(i, {}).get('decision') == d] for d in ("TAKE", "REVIEW", "SKIP")}
summ = [m(agg["TAKE"], "AGG_TAKE"), m(agg["REVIEW"], "AGG_REVIEW"), m(agg["SKIP"], "AGG_SKIP"),
        m(EP, "ALL_276"), m(old["TAKE"], "OLD_TAKE"), m(old["REVIEW"], "OLD_REVIEW"), m(old["SKIP"], "OLD_SKIP")]
mcols = ['bucket', 'n', 'per_year', 'exp_decap', 'sumR_decap', 'pf', 'hit2R', 'stop', 'maxDD', 'streak', 'wilson_hit2', 'longs']
with open(f"{D}/l2_bpt_aggregator_v0_summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=mcols, extrasaction='ignore'); w.writeheader(); w.writerows(summ)

# ---- comparação cruzada agg vs old + drivers ----
cross = Counter((l['agg_decision'], l['old_decision']) for l in ledger)
# winners cortados: agg SKIP mas é winner; lixo aceito: agg TAKE mas stop
agg_take = set(agg["TAKE"])
cut_winners = [i for i in EP if i not in agg_take and i not in set(agg["REVIEW"]) and hit2(i)]  # SKIP de winner
take_stops = [i for i in agg_take if stop(i)]
# quais especialistas mais "mandam" no TAKE
drive = Counter()
for i in agg_take:
    for s in SPECS:
        if state(i, s) == 'supportive': drive[s] += 1
# veto agressividade
veto_skips = [i for i in EP if aggregate(i)[2] == 'VETO']
veto_skip_winners = [i for i in veto_skips if hit2(i)]
with open(f"{D}/l2_bpt_aggregator_v0_vs_old.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["agg_decision", "old_decision", "n"])
    for (a, o), n in sorted(cross.items()): w.writerow([a, o, n])
    w.writerow([]); w.writerow(["metric", "value", "detail"])
    w.writerow(["agg_TAKE_drives", json.dumps(dict(drive.most_common())), "# supportive por especialista nos TAKE"])
    w.writerow(["cut_winners(agg SKIP & winner)", len(cut_winners), "winners que o agg jogaria fora"])
    w.writerow(["take_that_stopped", len(take_stops), f"de {len(agg_take)} TAKE"])
    w.writerow(["veto_skips_total", len(veto_skips), f"dos quais {len(veto_skip_winners)} eram winners (veto agressivo?)"])

print("=== AGGREGATOR v0 DIAGNÓSTICO (276 episódios, SIMULADO, NÃO oficial) ===")
for r in summ:
    if r['n']: print(f"  {r['bucket']:<11} n={r['n']:<3} ({r['per_year']}/ano) exp_decap={r.get('exp_decap'):>6} sumR={r.get('sumR_decap'):>6} pf={r.get('pf'):>5} hit2R={r.get('hit2R')}% maxDD={r.get('maxDD')} streak={r.get('streak')} wilson={r.get('wilson_hit2')}")
print(f"\n  AGG vs OLD (cross): {dict(cross)}")
print(f"  TAKE drivers (supportive count): {dict(drive.most_common())}")
print(f"  cut_winners (agg descarta winner): {len(cut_winners)} | TAKE que stoparam: {len(take_stops)}/{len(agg_take)}")
print(f"  veto->SKIP: {len(veto_skips)} (winners vetados: {len(veto_skip_winners)})")
