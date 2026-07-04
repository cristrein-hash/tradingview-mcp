#!/usr/bin/env python3
"""
LAB B r2 — ROUND 3: quantificação das classes de contexto sobreviventes.
Estado: hipótese-teto REFUTADA na base (flagged CONV2/CONV3 payer-enriched).
Assinatura real da dor = ANTI-estrutura ("DEAD_MIDDLE"): conv==0 (sem teto, sem extensão,
meio de range) com WR 37.6 / avg +0.288 / 43% dos membros em loss-run.

Predicados (congelados; ledger continua):
  CLASS_NOSTRUCT = conv==0 (das 6 lentes do round 1; quantis da base).
  CLASS_DEADMID  = conv==0 AND g_ema50_dist<=q50(base) AND h1_pos<=q50(base)
                   *** DERIVADA DO SCREENING L#15 — declarada como hipótese fitted,
                   exige convergência por-ano + null + jackknife DENTRO desta rodada
                   e rodada própria de confirmação antes de qualquer promoção. ***
Looks:
  L#16 painéis SKIP/SIZE50 conv==0 · L#17 null SKIP conv==0 (200x, mesma cobertura)
  L#18 CLASS_DEADMID cohort+painéis+por-ano · L#19 jackknife por bloco (política melhor)
  L#20 anatomia de streak: runs encurtados/quebrados sob SKIP das classes.
  L#21 E_HTFCEIL como classe POSITIVA (contexto p/ F4; leitura, sem size-up aqui).
"""
import json, random, statistics, datetime
from collections import Counter, defaultdict

SB = 0.80
D = '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo'
rows = [json.loads(l) for l in open(f'{D}/results/lab_g_candidates.jsonl')]
base = sorted([r for r in rows if r.get('g_in_base435') == 1 and r.get('g_v5h') != 'BEAR'],
              key=lambda r: r['t'])
for r in base: r['net'] = r['g_R'] - SB / r['g_risk']

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
         e50_q75=q([r['g_ema50_dist'] for r in base], .75),
         e50_q50=q([r['g_ema50_dist'] for r in base], .50),
         h1pos_q50=q([r['h1_pos'] for r in base], .50))
for r in base:
    L = dict(A=r['n_supply_overhead'] >= Q['supply_q75'],
             B=r['clean_sky_atr'] <= Q['sky_q25'],
             C=r['legpos60'] >= Q['leg60_q75'] and r['legpos90'] >= Q['leg90_q75'],
             D=r['g_box96'] >= Q['box96_q80'] and r['g_box480'] >= Q['box480_q80'],
             E=(r['h1n_clean_sky_atr'] is not None and r['h1n_clean_sky_atr'] <= Q['h1sky_q25']
                and r['h4n_clean_sky_atr'] is not None and r['h4n_clean_sky_atr'] <= Q['h4sky_q25']),
             F=r['g_ema21_dist'] >= Q['e21_q75'] and r['g_ema50_dist'] >= Q['e50_q75'])
    r['L'] = L; r['conv'] = sum(L.values())
    r['nostruct'] = r['conv'] == 0
    r['deadmid'] = (r['conv'] == 0 and r['g_ema50_dist'] <= Q['e50_q50']
                    and r['h1_pos'] is not None and r['h1_pos'] <= Q['h1pos_q50'])

runs, cur = [], []
for i, r in enumerate(base):
    if r['net'] < 0: cur.append(i)
    else:
        if len(cur) >= 3: runs.append(cur)
        cur = []
if len(cur) >= 3: runs.append(cur)
in_run = {i for run in runs for i in run}

def seqstats(net):
    eq = pk = dd = 0.0; stk = wst = 0
    for x in net:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x < 0: stk += 1; wst = max(wst, stk)
        else: stk = 0
    return sum(net), dd, wst

def panel(weights, label):
    xs = [(r, w) for r, w in zip(base, weights) if w > 0]
    net = [r['net'] * w for r, w in xs]
    s, dd, wst = seqstats(net)
    N = len(xs); wr = 100 * sum(1 for r, w in xs if r['net'] > 0) / N
    yr = defaultdict(float); mo = defaultdict(float)
    for r, w in xs:
        yr[r['yr']] += r['net'] * w
        mo[datetime.datetime.utcfromtimestamp(r['t']).strftime('%Y-%m')] += r['net'] * w
    wm = min(mo.items(), key=lambda kv: kv[1])
    rk = sum(w for r, w in xs if r['g_R'] >= 3)
    print(f'{label:32s} N={N:3d} WR={wr:4.1f} sumNET={s:+7.1f} avg={s/N:+.3f} DD={dd:6.1f} '
          f'r/DD={s/abs(dd):5.1f} stk={wst} runW={rk:.1f}/53 piorMes={wm[0]}:{wm[1]:+.1f} '
          f'ano={{{", ".join(f"{k}:{v:+.0f}" for k,v in sorted(yr.items()))}}}')
    return dict(s=s, dd=dd, stk=wst)

print('== L#16 CLASSE NOSTRUCT (conv==0) ==')
p0 = panel([1.0] * 435, 'P0 baseline')
pS = panel([0.0 if r['nostruct'] else 1.0 for r in base], 'SKIP conv==0')
pH = panel([0.5 if r['nostruct'] else 1.0 for r in base], 'SIZE50 conv==0')

print('\n== L#17 NULL p/ SKIP conv==0 (200 flags aleatórias, cobertura=157) ==')
k = sum(1 for r in base if r['nostruct'])
random.seed(7)
dds, stks, sums, wrs = [], [], [], []
for _ in range(200):
    idx = set(random.sample(range(435), k))
    keep = [base[i]['net'] for i in range(435) if i not in idx]
    s, dd, wst = seqstats(keep)
    dds.append(dd); stks.append(wst); sums.append(s)
    wrs.append(100 * sum(1 for i in range(435) if i not in idx and base[i]['net'] > 0) / (435 - k))
print(f'  null: sum med={statistics.median(sums):+.1f} | DD med={statistics.median(dds):.1f} '
      f'p10={q(dds,.10):.1f} p90={q(dds,.90):.1f} | stk med={statistics.median(stks)} min={min(stks)} '
      f'| WR med={statistics.median(wrs):.1f}')
print(f'  SKIP conv==0: sum {pS["s"]:+.1f} (> {100*sum(1 for s in sums if pS["s"]>s)/200:.0f}% null) · '
      f'DD {pS["dd"]:.1f} (melhor que {100*sum(1 for d in dds if pS["dd"]>d)/200:.0f}% null) · '
      f'stk {pS["stk"]} (<= {100*sum(1 for x in stks if pS["stk"]<=x)/200:.0f}% null)')

print('\n== L#18 CLASS_DEADMID (DERIVADA DO SCREENING — hipótese fitted, tratar como tal) ==')
dm = [r for r in base if r['deadmid']]
s = sum(r['net'] for r in dm)
print(f'  cohort: N={len(dm)} WR={100*sum(1 for r in dm if r["net"]>0)/len(dm):.1f} '
      f'sumNET={s:+.1f} avg={s/len(dm):+.3f} runners={sum(1 for r in dm if r["g_R"]>=3)} '
      f'%in-loss-run={100*sum(1 for r in dm if base.index(r) in in_run)/len(dm):.0f}')
yr = defaultdict(lambda: [0, 0.0])
for r in dm:
    yr[r['yr']][0] += 1; yr[r['yr']][1] += r['net']
print('  por-ano cohort:', {k: (v[0], round(v[1], 1)) for k, v in sorted(yr.items())})
pDS = panel([0.0 if r['deadmid'] else 1.0 for r in base], 'SKIP DEADMID')
pDH = panel([0.5 if r['deadmid'] else 1.0 for r in base], 'SIZE50 DEADMID')
kd = len(dm)
random.seed(11)
dds2, sums2, stks2 = [], [], []
for _ in range(200):
    idx = set(random.sample(range(435), kd))
    s2, dd2, w2 = seqstats([base[i]['net'] for i in range(435) if i not in idx])
    dds2.append(dd2); sums2.append(s2); stks2.append(w2)
print(f'  null(k={kd}): sum med={statistics.median(sums2):+.1f} DD med={statistics.median(dds2):.1f} stk med={statistics.median(stks2)}')
print(f'  SKIP DEADMID vs null: sum > {100*sum(1 for x in sums2 if pDS["s"]>x)/200:.0f}% · '
      f'DD melhor que {100*sum(1 for x in dds2 if pDS["dd"]>x)/200:.0f}% · '
      f'stk <= {100*sum(1 for x in stks2 if pDS["stk"]<=x)/200:.0f}%')

print('\n== L#19 JACKKNIFE por bloco — SKIP conv==0 vs P0 ==')
for b in sorted({r['block'] for r in base}):
    sub = [r for r in base if r['block'] != b]
    s0, d0, w0 = seqstats([r['net'] for r in sub])
    s1, d1, w1 = seqstats([r['net'] for r in sub if not r['nostruct']])
    print(f'  -{b}: P0 {s0:+7.1f}/DD{d0:6.1f}/stk{w0} -> SKIP {s1:+7.1f}/DD{d1:6.1f}/stk{w1}')

print('\n== L#20 ANATOMIA: das 36 loss-runs, quantas encurtam sob SKIP conv==0 / DEADMID ==')
def run_after_skip(flag):
    short = broken = 0
    for run in runs:
        mem = [base[i] for i in run]
        rem = [r for r in mem if not r[flag]]
        if len(rem) < len(mem):
            short += 1
            if len(rem) < 3: broken += 1
    return short, broken
for flag in ['nostruct', 'deadmid']:
    sh, br = run_after_skip(flag)
    print(f'  {flag}: {sh}/36 runs tocados, {br}/36 quebrados (<3 após skip)')
runlens = Counter(len(r) for r in runs)
print('  dist tamanhos runs:', dict(sorted(runlens.items())))

print('\n== L#21 E_HTFCEIL classe POSITIVA (leitura p/ rota F4/contexto) ==')
eh = [r for r in base if r['L']['E']]
yr = defaultdict(lambda: [0, 0.0])
for r in eh: yr[r['yr']][0] += 1; yr[r['yr']][1] += r['net']
print(f'  N={len(eh)} WR={100*sum(1 for r in eh if r["net"]>0)/len(eh):.1f} '
      f'sumNET={sum(r["net"] for r in eh):+.1f} runners={sum(1 for r in eh if r["g_R"]>=3)} '
      f'por-ano={ {k:(v[0],round(v[1],1)) for k,v in sorted(yr.items())} }')

print('\nLOOKS LEDGER round3: L#16..L#21 (6 looks). Total acumulado: 21.')
