#!/usr/bin/env python3
"""
LAB B r2 — STREAK/DD via LEITURA ESTRUTURAL DE CONTEXTO (não sizing, não outcome-chaveado).
Missão Cris 2026-07-04.

DESENHO (congelado ANTES de olhar g_R dos flagged — ledger de looks no fim):
  Lentes estruturais ex-ante, thresholds por QUANTIL DA BASE (declarado: CALIBRAÇÃO, não validação):
    A_SUPPLY : n_supply_overhead >= q75(base)          (peso de supply acima)
    B_SKY    : clean_sky_atr     <= q25(base)          (céu curto — PROIBIDO isolado; só em convergência)
    C_LEGTOP : legpos60>=q75 AND legpos90>=q75         (topo de extensão da perna)
    D_BOXTOP : g_box96>=q80 AND g_box480>=q80          (teto da estrutura/regime anterior 96/480)
    E_HTFCEIL: h1n_clean_sky_atr<=q25 AND (h4n_clean_sky_atr<=q25 ou null->False)
    F_EXT    : g_ema21_dist>=q75 AND g_ema50_dist>=q75 (extensão vs média)
  Convergência = nº de lentes ativas. CONV2 = >=2 lentes (REVIEW/size), CONV3 = >=3 (SKIP-candidata).
  Regra assimétrica: antes de propor SKIP, medir runners entre flagged; se flagged carrega runners,
  demover para size-50/REVIEW (preservação de runners = 1ª classe).

  Clusters de dor (alvo, definidos por outcome — permitido, é o TARGET não o predicado):
    - loss-runs >=3 consecutivas na sequência NET-SB temporal;
    - semanas-dor: g_week com NET <= -3.
  Classificação: cluster ESTRUTURAL se >=2/3 dos membros têm CONV2; senão TEMPORAL.

  Impacto (políticas, painel completo N·WR·sumR·avgR·DD·r/DD·streak·por-ano·pior-mês·runners):
    P0 baseline · P1 SKIP CONV2 · P2 SIZE50 CONV2 · P3 SKIP CONV3 ·
    P4 tiered (CONV3 SKIP + CONV2 SIZE50) · P5 SKIP só membros ex-ante-flagged (CONV2) — igual P1
    (flag é ex-ante, sem conhecimento de cluster).
  Null: 200 flags aleatórias com mesma cobertura → dist. de ΔDD/Δstreak; jackknife por bloco.
"""
import json, random, statistics, datetime
from collections import Counter, defaultdict

SB = 0.80
D = '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo'
rows = [json.loads(l) for l in open(f'{D}/results/lab_g_candidates.jsonl')]
base = sorted([r for r in rows if r.get('g_in_base435') == 1 and r.get('g_v5h') != 'BEAR'],
              key=lambda r: r['t'])
assert len(base) == 435
mat = {m['t']: m for m in json.load(open(f'{D}/base4_maturation_features.json'))}

for r in base:
    r['net'] = r['g_R'] - SB / r['g_risk']
    r['m'] = mat.get(r['t']) or mat.get(r.get('cj_t'))

def q(vals, p):
    vs = sorted(v for v in vals if v is not None)
    return vs[min(len(vs) - 1, int(p * len(vs)))]

# ---- CALIBRAÇÃO NA BASE (declarada) ----
Q = {
    'supply_q75': q([r['n_supply_overhead'] for r in base], .75),
    'sky_q25':    q([r['clean_sky_atr'] for r in base], .25),
    'leg60_q75':  q([r['legpos60'] for r in base], .75),
    'leg90_q75':  q([r['legpos90'] for r in base], .75),
    'box96_q80':  q([r['g_box96'] for r in base], .80),
    'box480_q80': q([r['g_box480'] for r in base], .80),
    'h1sky_q25':  q([r['h1n_clean_sky_atr'] for r in base], .25),
    'h4sky_q25':  q([r['h4n_clean_sky_atr'] for r in base], .25),
    'e21_q75':    q([r['g_ema21_dist'] for r in base], .75),
    'e50_q75':    q([r['g_ema50_dist'] for r in base], .75),
}
print('== QUANTIS CALIBRADOS NA BASE (calibração, não validação) ==')
for k, v in Q.items(): print(f'  {k} = {v}')

def lenses(r):
    L = {}
    L['A_SUPPLY'] = r['n_supply_overhead'] >= Q['supply_q75']
    L['B_SKY'] = r['clean_sky_atr'] <= Q['sky_q25']
    L['C_LEGTOP'] = r['legpos60'] >= Q['leg60_q75'] and r['legpos90'] >= Q['leg90_q75']
    L['D_BOXTOP'] = r['g_box96'] >= Q['box96_q80'] and r['g_box480'] >= Q['box480_q80']
    h4 = r['h4n_clean_sky_atr']
    L['E_HTFCEIL'] = (r['h1n_clean_sky_atr'] is not None and r['h1n_clean_sky_atr'] <= Q['h1sky_q25']
                      and h4 is not None and h4 <= Q['h4sky_q25'])
    L['F_EXT'] = r['g_ema21_dist'] >= Q['e21_q75'] and r['g_ema50_dist'] >= Q['e50_q75']
    return L

for r in base:
    r['L'] = lenses(r)
    r['conv'] = sum(r['L'].values())

print('\n== COBERTURA NA BASE (antes de qualquer look em g_R condicionado) ==')
for name in ['A_SUPPLY', 'B_SKY', 'C_LEGTOP', 'D_BOXTOP', 'E_HTFCEIL', 'F_EXT']:
    n = sum(r['L'][name] for r in base)
    print(f'  {name:9s}: {n:3d} ({100*n/435:.1f}%)')
cv = Counter(r['conv'] for r in base)
print('  conv dist:', dict(sorted(cv.items())))
print('  CONV2 (>=2):', sum(1 for r in base if r['conv'] >= 2),
      ' CONV3 (>=3):', sum(1 for r in base if r['conv'] >= 3))

# ---- CLUSTERS DE DOR ----
runs, cur = [], []
for i, r in enumerate(base):
    if r['net'] < 0:
        cur.append(i)
    else:
        if len(cur) >= 3: runs.append(cur)
        cur = []
if len(cur) >= 3: runs.append(cur)
print(f'\n== LOSS-RUNS >=3 (target): {len(runs)} runs, {sum(len(x) for x in runs)} trades ==')

wknet = defaultdict(float)
for r in base: wknet[r['g_week']] += r['net']
painweeks = {w for w, v in wknet.items() if v <= -3}
print(f'   semanas-dor (NET<=-3): {len(painweeks)}')

# assinatura estrutural dos clusters
struct_runs = temporal_runs = 0
run_detail = []
for run in runs:
    mem = [base[i] for i in run]
    frac2 = sum(1 for r in mem if r['conv'] >= 2) / len(mem)
    frac1 = sum(1 for r in mem if r['conv'] >= 1) / len(mem)
    kind = 'STRUCTURAL' if frac2 >= 2/3 else 'TEMPORAL'
    if kind == 'STRUCTURAL': struct_runs += 1
    else: temporal_runs += 1
    d0 = datetime.datetime.utcfromtimestamp(mem[0]['t']).date()
    ln = Counter()
    for r in mem:
        for k, v in r['L'].items():
            if v: ln[k] += 1
    run_detail.append((str(d0), len(mem), round(frac1, 2), round(frac2, 2), kind,
                       dict(ln.most_common(3))))
print(f'   STRUCTURAL (>=2/3 membros CONV2): {struct_runs} · TEMPORAL: {temporal_runs}')
print(f'   base-rate CONV2 = {sum(1 for r in base if r["conv"]>=2)/435:.2f} · '
      f'CONV1 = {sum(1 for r in base if r["conv"]>=1)/435:.2f}')
for d in run_detail:
    print('   ', d)

# enriquecimento: taxa CONV2 dentro de loss-runs vs fora
in_run = {i for run in runs for i in run}
r_in = sum(1 for i in in_run if base[i]['conv'] >= 2) / len(in_run)
r_out = sum(1 for i in range(435) if i not in in_run and base[i]['conv'] >= 2) / (435 - len(in_run))
print(f'   CONV2 rate dentro loss-runs: {r_in:.3f} vs fora: {r_out:.3f}')
r1_in = sum(1 for i in in_run if base[i]['conv'] >= 1) / len(in_run)
r1_out = sum(1 for i in range(435) if i not in in_run and base[i]['conv'] >= 1) / (435 - len(in_run))
print(f'   CONV1 rate dentro loss-runs: {r1_in:.3f} vs fora: {r1_out:.3f}')

# ---- PAINEL / POLÍTICAS (LOOK #1..#5 declarados no ledger) ----
def panel(weights, label):
    xs = [(r, w) for r, w in zip(base, weights) if w > 0]
    net = [r['net'] * w for r, w in xs]
    N = len(xs)
    wr = 100 * sum(1 for r, w in xs if r['net'] > 0) / N
    eq = pk = dd = 0.0; stk = wst = 0
    for x in net:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x < 0: stk += 1; wst = max(wst, stk)
        else: stk = 0
    yr = defaultdict(float)
    mo = defaultdict(float)
    for r, w in xs:
        yr[r['yr']] += r['net'] * w
        mo[datetime.datetime.utcfromtimestamp(r['t']).strftime('%Y-%m')] += r['net'] * w
    wm = min(mo.items(), key=lambda kv: kv[1])
    run_kept = sum(w for r, w in xs if r['g_R'] >= 3)
    s = sum(net)
    print(f'{label:28s} N={N:3d} WR={wr:4.1f} sumNET={s:+7.1f} avg={s/N:+.3f} '
          f'DD={dd:6.1f} r/DD={s/abs(dd):5.1f} stk={wst} '
          f'runnersW={run_kept:.1f}/53 piorMes={wm[0]}:{wm[1]:+.1f} '
          f'porAno={{{", ".join(f"{k}:{v:+.0f}" for k,v in sorted(yr.items()))}}}')
    return dict(N=N, s=s, dd=dd, stk=wst, run=run_kept)

print('\n== POLÍTICAS (cada linha = 1 look em outcomes condicionados; ledger no fim) ==')
w0 = [1.0] * 435
p0 = panel(w0, 'P0 baseline')
p1 = panel([0.0 if r['conv'] >= 2 else 1.0 for r in base], 'P1 SKIP CONV2')
p2 = panel([0.5 if r['conv'] >= 2 else 1.0 for r in base], 'P2 SIZE50 CONV2')
p3 = panel([0.0 if r['conv'] >= 3 else 1.0 for r in base], 'P3 SKIP CONV3')
p4 = panel([0.0 if r['conv'] >= 3 else (0.5 if r['conv'] == 2 else 1.0) for r in base],
           'P4 tiered SKIP3+SIZE50@2')

# leitura fria dos flagged (LOOK #6-#7)
print('\n== LEITURA FRIA DOS FLAGGED (pós-congelamento) ==')
for tag, sel in [('CONV2', [r for r in base if r['conv'] >= 2]),
                 ('CONV3', [r for r in base if r['conv'] >= 3])]:
    if not sel: continue
    s = sum(r['net'] for r in sel)
    wr = 100 * sum(1 for r in sel if r['net'] > 0) / len(sel)
    rn = sum(1 for r in sel if r['g_R'] >= 3)
    print(f'  {tag}: N={len(sel)} WR={wr:.1f} sumNET={s:+.1f} avg={s/len(sel):+.3f} runners={rn}')

# lente individual (LOOK #8) — leitura, não filtro
print('\n== POR LENTE (leitura fria; nenhuma vira filtro isolado) ==')
for name in ['A_SUPPLY', 'B_SKY', 'C_LEGTOP', 'D_BOXTOP', 'E_HTFCEIL', 'F_EXT']:
    sel = [r for r in base if r['L'][name]]
    if not sel: print(f'  {name}: N=0'); continue
    s = sum(r['net'] for r in sel)
    rn = sum(1 for r in sel if r['g_R'] >= 3)
    print(f'  {name:9s}: N={len(sel):3d} WR={100*sum(1 for r in sel if r["net"]>0)/len(sel):4.1f} '
          f'sumNET={s:+7.1f} avg={s/len(sel):+.3f} runners={rn}')

# ---- NULL: flags aleatórias com mesma cobertura de CONV2 (SKIP) ----
k2 = sum(1 for r in base if r['conv'] >= 2)
random.seed(42)
dds, stks, sums = [], [], []
for _ in range(200):
    idx = set(random.sample(range(435), k2))
    net = [base[i]['net'] for i in range(435) if i not in idx]
    eq = pk = dd = 0.0; stk = wst = 0
    for x in net:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x < 0: stk += 1; wst = max(wst, stk)
        else: stk = 0
    dds.append(dd); stks.append(wst); sums.append(sum(net))
print(f'\n== NULL (200 SKIPs aleatórios, cobertura={k2}) ==')
print(f'  DD null: med={statistics.median(dds):.1f} p10={q(dds,.10):.1f} | P1 DD={p1["dd"]:.1f}')
print(f'  stk null: med={statistics.median(stks)} min={min(stks)} | P1 stk={p1["stk"]}')
print(f'  sumNET null: med={statistics.median(sums):+.1f} | P1 sum={p1["s"]:+.1f}')
print(f'  P1 DD melhor que {100*sum(1 for d in dds if p1["dd"]>d)/200:.0f}% dos nulls; '
      f'sum melhor que {100*sum(1 for s in sums if p1["s"]>s)/200:.0f}% dos nulls')

# ---- JACKKNIFE por bloco (P4 tiered, política mais provável) ----
print('\n== JACKKNIFE por bloco — P4 tiered vs P0 (Δsum, ΔDD) ==')
blocks = sorted({r['block'] for r in base})
for b in blocks:
    sub = [r for r in base if r['block'] != b]
    def mini(ws):
        net = [r['net'] * w for r, w in zip(sub, ws) if w > 0]
        eq = pk = dd = 0.0
        for x in net: eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        return sum(net), dd
    s0, d0_ = mini([1.0] * len(sub))
    s4, d4 = mini([0.0 if r['conv'] >= 3 else (0.5 if r['conv'] == 2 else 1.0) for r in sub])
    print(f'  -{b}: P0 {s0:+7.1f}/DD{d0_:6.1f} -> P4 {s4:+7.1f}/DD{d4:6.1f}')

print('\nLOOKS LEDGER: 8 looks em outcomes condicionados (P0-P4 painéis=5, flagged CONV2/CONV3=2, por-lente=1).')
print('Predicados congelados antes do primeiro look; quantis = calibração na base, declarado.')
