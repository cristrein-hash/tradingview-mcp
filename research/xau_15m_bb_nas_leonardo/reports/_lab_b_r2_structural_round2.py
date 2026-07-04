#!/usr/bin/env python3
"""
LAB B r2 — ROUND 2 (devil's advocate sobre round 1).
Round 1 achou: lentes de teto CONVERGENTES na base NÃO são loser-enriched — são payer-enriched
(CONV2 avg +0.629 > base +0.537; E_HTFCEIL avg +1.874; CONV2 rate DENTRO de loss-runs 0.294 < fora 0.344).
Só 6/36 loss-runs são estruturais. SKIP CONV2 piora tudo (DD -14.2→-19.7, pior que 93% dos nulls).

Round 2 (predicados congelados antes dos looks; ledger continua do #8):
  L#9  conv==0 (ANTI-estrutura, céu aberto/meio de range) — painel frio.
  L#10 A&B (n_supply>=q75 AND clean_sky<=q25) — combo clássico "sob supply pesada".
  L#11 A&B & h1n_clean_sky<=q25 — teto multi-TF estreito.
  L#12 correlação tamanho-do-run × frac_CONV2 (runs grandes são mais estruturais?).
  L#13 overlap semanas-dor × runs estruturais.
  L#14 painel SKIP/SIZE50 do combo A&B (se ele for loser-enriched; senão reportar e parar).
  L#15 EXPLORATÓRIO DECLARADO (geração de hipótese, não filtro): screening de campos ex-ante
       membros-de-loss-run vs resto (effect size), para achar a assinatura REAL dos clusters de dor.
"""
import json, statistics, datetime
from collections import Counter, defaultdict

SB = 0.80
D = '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo'
rows = [json.loads(l) for l in open(f'{D}/results/lab_g_candidates.jsonl')]
base = sorted([r for r in rows if r.get('g_in_base435') == 1 and r.get('g_v5h') != 'BEAR'],
              key=lambda r: r['t'])
mat = {m['t']: m for m in json.load(open(f'{D}/base4_maturation_features.json'))}
for r in base:
    r['net'] = r['g_R'] - SB / r['g_risk']
    r['m'] = mat.get(r['t'])

def q(vals, p):
    vs = sorted(v for v in vals if v is not None)
    return vs[min(len(vs) - 1, int(p * len(vs)))]

Q = dict(supply_q75=q([r['n_supply_overhead'] for r in base], .75),
         sky_q25=q([r['clean_sky_atr'] for r in base], .25),
         leg60_q75=q([r['legpos60'] for r in base], .75),
         leg90_q75=q([r['legpos90'] for r in base], .75),
         box96_q80=q([r['g_box96'] for r in base], .80),
         box480_q80=q([r['g_box480'] for r in base], .80),
         h1sky_q25=q([r['h1n_clean_sky_atr'] for r in base], .25),
         h4sky_q25=q([r['h4n_clean_sky_atr'] for r in base], .25),
         e21_q75=q([r['g_ema21_dist'] for r in base], .75),
         e50_q75=q([r['g_ema50_dist'] for r in base], .75))
for r in base:
    L = dict(A=r['n_supply_overhead'] >= Q['supply_q75'],
             B=r['clean_sky_atr'] <= Q['sky_q25'],
             C=r['legpos60'] >= Q['leg60_q75'] and r['legpos90'] >= Q['leg90_q75'],
             D=r['g_box96'] >= Q['box96_q80'] and r['g_box480'] >= Q['box480_q80'],
             E=(r['h1n_clean_sky_atr'] is not None and r['h1n_clean_sky_atr'] <= Q['h1sky_q25']
                and r['h4n_clean_sky_atr'] is not None and r['h4n_clean_sky_atr'] <= Q['h4sky_q25']),
             F=r['g_ema21_dist'] >= Q['e21_q75'] and r['g_ema50_dist'] >= Q['e50_q75'])
    r['L'] = L; r['conv'] = sum(L.values())

runs, cur = [], []
for i, r in enumerate(base):
    if r['net'] < 0: cur.append(i)
    else:
        if len(cur) >= 3: runs.append(cur)
        cur = []
if len(cur) >= 3: runs.append(cur)
in_run = {i for run in runs for i in run}

def panel(sel_w, label):
    xs = [(r, w) for r, w in sel_w if w > 0]
    if not xs: print(f'{label}: N=0'); return None
    net = [r['net'] * w for r, w in xs]
    N = len(xs); s = sum(net)
    wr = 100 * sum(1 for r, w in xs if r['net'] > 0) / N
    eq = pk = dd = 0.0; stk = wst = 0
    for x in net:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x < 0: stk += 1; wst = max(wst, stk)
        else: stk = 0
    yr = defaultdict(float); mo = defaultdict(float)
    for r, w in xs:
        yr[r['yr']] += r['net'] * w
        mo[datetime.datetime.utcfromtimestamp(r['t']).strftime('%Y-%m')] += r['net'] * w
    wm = min(mo.items(), key=lambda kv: kv[1])
    rk = sum(w for r, w in xs if r['g_R'] >= 3)
    print(f'{label:34s} N={N:3d} WR={wr:4.1f} sumNET={s:+7.1f} avg={s/N:+.3f} DD={dd:6.1f} '
          f'r/DD={(s/abs(dd)) if dd else float("inf"):5.1f} stk={wst} runW={rk:.1f}/53 '
          f'piorMes={wm[0]}:{wm[1]:+.1f} ano={{{", ".join(f"{k}:{v:+.0f}" for k,v in sorted(yr.items()))}}}')
    return dict(s=s, dd=dd, stk=wst)

def cohort(sel, label):
    if not sel: print(f'  {label}: N=0'); return
    s = sum(r['net'] for r in sel)
    wr = 100 * sum(1 for r in sel if r['net'] > 0) / len(sel)
    rn = sum(1 for r in sel if r['g_R'] >= 3)
    lr = sum(1 for r in sel if base.index(r) in in_run)
    print(f'  {label:34s} N={len(sel):3d} WR={wr:4.1f} sumNET={s:+7.1f} avg={s/len(sel):+.3f} '
          f'runners={rn} %in-loss-run={100*lr/len(sel):.0f}')

print('== L#9 ANTI-ESTRUTURA conv==0 ==')
cohort([r for r in base if r['conv'] == 0], 'conv==0 (céu aberto/meio range)')
cohort([r for r in base if r['conv'] == 1], 'conv==1')
cohort([r for r in base if r['conv'] >= 2], 'conv>=2')
print(f'  base %in-loss-run = {100*len(in_run)/435:.0f}')

print('\n== L#10/11 COMBOS ESTREITOS SOB SUPPLY ==')
AB = [r for r in base if r['L']['A'] and r['L']['B']]
cohort(AB, 'A&B supply_q75 & sky_q25')
ABh = [r for r in AB if r['h1n_clean_sky_atr'] is not None and r['h1n_clean_sky_atr'] <= Q['h1sky_q25']]
cohort(ABh, 'A&B & h1_sky_q25 (multi-TF)')

print('\n== L#12 tamanho-do-run x estruturalidade (frac CONV2 dos membros) ==')
pairs = []
for run in runs:
    mem = [base[i] for i in run]
    f2 = sum(1 for r in mem if r['conv'] >= 2) / len(mem)
    pairs.append((len(run), f2))
for ln in sorted({p[0] for p in pairs}):
    fs = [f for l, f in pairs if l == ln]
    print(f'  len={ln}: n_runs={len(fs)} frac2 med={statistics.median(fs):.2f} mean={statistics.mean(fs):.2f}')
big = [f for l, f in pairs if l >= 5]; small = [f for l, f in pairs if l < 5]
print(f'  runs>=5: mean frac2={statistics.mean(big):.2f} (n={len(big)}) | runs 3-4: {statistics.mean(small):.2f} (n={len(small)})')

print('\n== L#13 semanas-dor x runs estruturais ==')
wknet = defaultdict(float)
for r in base: wknet[r['g_week']] += r['net']
pw = sorted((w for w, v in wknet.items() if v <= -3), key=lambda w: w)
for w in pw:
    mem = [r for r in base if r['g_week'] == w]
    f2 = sum(1 for r in mem if r['conv'] >= 2) / len(mem)
    print(f'  {w}: NET={wknet[w]:+.1f} N={len(mem)} fracCONV2={f2:.2f}')

print('\n== L#14 painel A&B como SKIP/SIZE50 (só se loser-enriched; leitura acima decide) ==')
panel([(r, 1.0) for r in base], 'P0 baseline')
panel([(r, 0.0 if (r['L']['A'] and r['L']['B']) else 1.0) for r in base], 'SKIP A&B')
panel([(r, 0.5 if (r['L']['A'] and r['L']['B']) else 1.0) for r in base], 'SIZE50 A&B')

print('\n== L#15 EXPLORATÓRIO DECLARADO — screening membros-de-loss-run vs resto (hipótese, não filtro) ==')
num_fields = ['reclaim_atr','low_wick','confirm_body_atr','pullback_depth','dist_demand_atr',
              'clean_sky_atr','n_supply_overhead','legpos60','legpos90','rsi_low','rsi_min8',
              'atr_regime','atr_compression_pre','downleg_eff','n_demand_near','h1_pos','h1_rsi',
              'h1_dist','h4n_dist_demand_atr','h4n_rsi','h4n_clean_sky_atr','h1n_dist_demand_atr',
              'h1n_rsi','h1n_clean_sky_atr','g_atr_spike','g_sweep_depth','g_box96','g_box480',
              'g_rec_speed','g_ema21_dist','g_ema50_dist','g_flush_wick','g_cj_body','g_risk','g_atr']
res = []
A = [base[i] for i in in_run]; Bc = [base[i] for i in range(435) if i not in in_run]
for f in num_fields:
    va = [r[f] for r in A if r.get(f) is not None]
    vb = [r[f] for r in Bc if r.get(f) is not None]
    if len(va) < 20 or len(vb) < 20: continue
    ma, mb = statistics.mean(va), statistics.mean(vb)
    sd = statistics.pstdev(va + vb) or 1e-9
    res.append((abs(ma - mb) / sd, f, round(ma, 3), round(mb, 3)))
res.sort(reverse=True)
print('  campo (|d| efeito) — média_in_run vs média_fora:')
for d, f, ma, mb in res[:12]:
    print(f'   d={d:.2f} {f:24s} in={ma} out={mb}')
bin_fields = ['is_bottom','is_monforte','is_medfraco','above_ema21','micro_hl','downleg_decel',
              'demand_reclaim','in_demand','swept_prior_low','h1_trend','h4n_trend','h1n_trend',
              'macro_bull','buy_bub_w','nas_long_16','killzone','h4n_in_demand','h1n_in_demand',
              'htf_demand_confluence','htf_demand_any','falling_knife','g_rsi_div','g_downrun',
              'g_knife','g_regime_flip5d']
print('  binários (taxa in_run vs fora):')
rb = []
for f in bin_fields:
    va = [1 if r.get(f) in (1, True) else 0 for r in A]
    vb = [1 if r.get(f) in (1, True) else 0 for r in Bc]
    rb.append((abs(statistics.mean(va) - statistics.mean(vb)), f,
               round(statistics.mean(va), 2), round(statistics.mean(vb), 2)))
rb.sort(reverse=True)
for d, f, ma, mb in rb[:8]:
    print(f'   Δ={d:.2f} {f:24s} in={ma} out={mb}')
reg_in = Counter(r['g_v5h'] for r in A); reg_out = Counter(r['g_v5h'] for r in Bc)
print('  regime v5h in_run:', dict(reg_in), ' fora:', dict(reg_out))

print('\nLOOKS LEDGER round2: L#9..L#15 (7 looks; L#15 = exploratório declarado, gera hipótese p/ rodada própria).')
