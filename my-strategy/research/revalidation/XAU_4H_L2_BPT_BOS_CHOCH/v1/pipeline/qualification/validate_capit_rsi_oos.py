#!/usr/bin/env python3
"""L2/BPT — VALIDAÇÃO da confluência capitulation+rsi_momentum (foco LUCRO). Escopo XAU_4H_L2_BPT_BOS_CHOCH.
Aplica EXATAMENTE a regra preregistrada (docs/XAU_4H_L2_BPT_CAPIT_RSI_OOS_PREREG.md). Outcome só pós-hoc.
NÃO cria aggregator/decisão, NÃO promove, NÃO retuna, NÃO testa outras células, NÃO toca engine/produção.
Reuso fiel do state()/fonte de dados da Fase 2B.5. De-cap = runner +6R (piso documentado; true>=).
Emite: validation_plan, oos_data_availability, validation_results, validation_controls,
validation_by_context_window, validation_da (CSV).
"""
import os, sys, csv, json, glob, math, random
random.seed(20260619)
QD = os.path.dirname(os.path.abspath(__file__))
D = os.path.normpath(os.path.join(QD, "..", "..", "results"))

# ---- carga (mesmos arquivos da Fase 2B.5) ----
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
EP = sorted(set(i for i, _ in mat if i in out))

def stance(i, s): return net.get((i, s), 'neutral')
def veto(i, s): return int(mat.get((i, s), {}).get('veto_count', '0') or 0) > 0
def review(i, s): return int(mat.get((i, s), {}).get('review_flag_count', '0') or 0) > 0
def state(i, s):
    if veto(i, s): return 'veto'
    st = stance(i, s)
    if review(i, s) and st == 'neutral': return 'review_flag'
    return st
def R(i): return float(out[i]['realR'])               # capado +3.9
def Rdecap(i): return 6.0 if out[i]['exitype'] == 'WIN_RUNNER' else R(i)  # piso de-cap (true>=)
def ex(i): return out[i]['exitype']
def hit2(i): return ex(i).startswith('WIN')
def runner(i): return ex(i) == 'WIN_RUNNER'
def stop(i): return ex(i) == 'STOP_LOSS'
def scratch(i): return ex(i) == 'SCRATCH'
def win(i): return hit2(i)
def dt(i): return out[i]['datetime']
take_lose = set(i for i in EP if dec[i]['decision'] == 'TAKE' and not win(i))
skip_win = set(i for i in EP if dec[i]['decision'] == 'SKIP' and win(i))

# ---- regra CONGELADA ----
def in_cell(i): return state(i, 'capitulation') == 'supportive' and state(i, 'rsi_momentum') == 'supportive'
CELL = [i for i in EP if in_cell(i)]
CTX_CELL = set(sa.get(i) for i in CELL)

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; den = 1 + z*z/n
    c = (p + z*z/(2*n)) / den; half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den
    return (max(0, c-half), min(1, c+half))

def profit_factor(ids, rf=R):
    pos = sum(rf(i) for i in ids if rf(i) > 0); neg = -sum(rf(i) for i in ids if rf(i) < 0)
    return round(pos/neg, 2) if neg > 0 else (float('inf') if pos > 0 else 0.0)

def maxdd(ids, rf=R):  # cum-R ordenado por datetime
    seq = [rf(i) for i in sorted(ids, key=dt)]
    peak = cum = 0.0; dd = 0.0
    for r in seq:
        cum += r; peak = max(peak, cum); dd = min(dd, cum-peak)
    return round(dd, 2)

def max_lose_streak(ids):
    cur = mx = 0
    for i in sorted(ids, key=dt):
        if not win(i): cur += 1; mx = max(mx, cur)
        else: cur = 0
    return mx

def block(ids, label):
    ids = list(ids); n = len(ids)
    if n == 0:
        return dict(label=label, n=0, exp_capped=0, exp_decap=0, sumR_capped=0, sumR_decap=0, pf_capped=0,
                    pf_decap=0, WR=0, hit2R=0, hit3R=0, stop=0, scratch=0, avgR_capped_ref=0, drop2_decap=0,
                    maxDD_decap=0, lose_streak=0, hit2_wilson='[]', cut_losers=0, kill_skipwin=0)
    Rc = [R(i) for i in ids]; Rd = [Rdecap(i) for i in ids]
    avgc = sum(Rc)/n; avgd = sum(Rd)/n
    Rds = sorted(Rd); drop2 = sum(Rds[:-2])/(n-2) if n > 2 else avgd
    k2 = sum(1 for i in ids if hit2(i)); lo, hi = wilson(k2, n)
    return dict(label=label, n=n, exp_capped=round(avgc, 3), exp_decap=round(avgd, 3),
                sumR_capped=round(sum(Rc), 1), sumR_decap=round(sum(Rd), 1),
                pf_capped=profit_factor(ids, R), pf_decap=profit_factor(ids, Rdecap),
                WR=round(100*sum(1 for i in ids if win(i))/n), hit2R=round(100*k2/n),
                hit3R=round(100*sum(1 for i in ids if runner(i))/n), stop=round(100*sum(1 for i in ids if stop(i))/n),
                scratch=round(100*sum(1 for i in ids if scratch(i))/n), avgR_capped_ref=round(avgc, 3),
                drop2_decap=round(drop2, 3), maxDD_decap=maxdd(ids, Rdecap), lose_streak=max_lose_streak(ids),
                hit2_wilson=f"[{lo:.2f},{hi:.2f}]", cut_losers=len(set(ids) & take_lose), kill_skipwin=len(set(ids) & skip_win))

def writecsv(path, rows, cols):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

COLS = ['label', 'n', 'exp_capped', 'exp_decap', 'sumR_capped', 'sumR_decap', 'pf_capped', 'pf_decap',
        'WR', 'hit2R', 'hit3R', 'stop', 'scratch', 'avgR_capped_ref', 'drop2_decap', 'maxDD_decap',
        'lose_streak', 'hit2_wilson', 'cut_losers', 'kill_skipwin']

# ---- TAREFA 2: plano ----
writecsv(f"{D}/l2_bpt_capit_rsi_validation_plan.csv", [dict(
    validation_method="sub-janelas / split temporal in-sample (XAU 2020-2026)",
    dataset="276 episódios L2/BPT XAU 4H (outcomes congelados, realR capado +3.9)",
    date_range="2020-01 .. 2026 (halves + thirds por datetime)",
    reason_selected="forma mais segura/honesta SEM dado novo; Opção B NÃO rodada; OOS externo exigiria recoletar inputs/evidence. NÃO é OOS verdadeiro (descoberta no conjunto completo).",
    required_inputs="ablation_matrix(states)+specialist_out(net_read)+outcomes(realR/exitype/datetime)+stage_a_labels",
    available="YES", blocked_reason="")],
    ['validation_method', 'dataset', 'date_range', 'reason_selected', 'required_inputs', 'available', 'blocked_reason'])

# ---- TAREFA 3: disponibilidade ----
def has(fam): return any(k[1] == fam for k in net)
avail = [
    dict(input="specialist_evidence:capitulation", available="YES" if has('capitulation') else "NO", n=sum(1 for k in net if k[1] == 'capitulation'), note="net_read stance"),
    dict(input="specialist_evidence:rsi_momentum", available="YES" if has('rsi_momentum') else "NO", n=sum(1 for k in net if k[1] == 'rsi_momentum'), note="net_read stance"),
    dict(input="stage_a_context_labels", available="YES" if sa else "NO", n=len(sa), note="para context-matching"),
    dict(input="outcomes(realR/exitype/datetime)", available="YES", n=len(out), note="realR CAPADO +3.9 (de-cap não recuperável; piso runner +6R)"),
    dict(input="decisions_merged(TAKE/SKIP)", available="YES", n=len(dec), note="só para cut_losers/kill_skipwin; NÃO alterado"),
    dict(input="base_universe", available="YES", n=len(EP), note="276 episódios"),
    dict(input="context_matched_controls", available="YES", n=len([i for i in EP if sa.get(i) in CTX_CELL]), note="mesmos Stage A da célula"),
    dict(input="OOS_externo/OpçãoB", available="NO", n=0, note="não coletado neste bloco"),
]
writecsv(f"{D}/l2_bpt_capit_rsi_oos_data_availability.csv", avail, ['input', 'available', 'n', 'note'])

# ---- TAREFA 4: resultados (célula total + por janela) ----
HALVES = [("H1_2020_2022", lambda i: dt(i) < "2023-01"), ("H2_2023_2026", lambda i: dt(i) >= "2023-01")]
THIRDS = [("T1_2020_2021", lambda i: dt(i) < "2022-01"), ("T2_2022_2023", lambda i: "2022-01" <= dt(i) < "2024-01"), ("T3_2024_2026", lambda i: dt(i) >= "2024-01")]
res = [block(CELL, "CELL_capit+rsi_ALL")]
for name, fn in HALVES + THIRDS:
    res.append(block([i for i in CELL if fn(i)], f"CELL_{name}"))
res.append(block(EP, "BASE_universe_276"))
writecsv(f"{D}/l2_bpt_capit_rsi_validation_results.csv", res, COLS)

# ---- TAREFA 5: controles + random-matched null ----
ctx_pool = [i for i in EP if sa.get(i) in CTX_CELL]
ctrls = [
    block(CELL, "CELL_capit+rsi"),
    block([i for i in EP if state(i, 'capitulation') == 'supportive'], "capitulation_alone"),
    block([i for i in EP if state(i, 'rsi_momentum') == 'supportive'], "rsi_momentum_alone"),
    block(EP, "base_universe_276"),
    block(ctx_pool, "base_context_matched"),
    block([i for i in EP if state(i, 'nas') == 'supportive'], "nas_alone_benchmark"),
]
# random-matched null: amostra n=|CELL| do pool de mesmo contexto, 10k, percentil do exp_decap e hit2R da célula
nrep = 10000; ncell = len(CELL)
cell_expd = block(CELL, "_")['exp_decap']; cell_hit2 = block(CELL, "_")['hit2R']
null_expd = []; null_hit2 = []
if len(ctx_pool) >= ncell and ncell > 0:
    for _ in range(nrep):
        samp = random.sample(ctx_pool, ncell)
        null_expd.append(sum(Rdecap(i) for i in samp)/ncell)
        null_hit2.append(100*sum(1 for i in samp if hit2(i))/ncell)
    pct_expd = round(100*sum(1 for x in null_expd if x >= cell_expd)/nrep, 2)
    pct_hit2 = round(100*sum(1 for x in null_hit2 if x >= cell_hit2)/nrep, 2)
    nullrow = dict(label="random_matched_null(pctile_cell>=)", n=ncell,
                   exp_decap=cell_expd, hit2R=cell_hit2,
                   note=f"P(null>=cell) exp_decap={pct_expd}% hit2R={pct_hit2}% (10k same-context)")
else:
    nullrow = dict(label="random_matched_null", n=ncell, exp_decap=cell_expd, hit2R=cell_hit2, note="pool insuficiente")
writecsv(f"{D}/l2_bpt_capit_rsi_validation_controls.csv", ctrls, COLS)
with open(f"{D}/l2_bpt_capit_rsi_validation_controls.csv", "a", newline="") as f:
    f.write("\n# random-matched null (same-context, 10k)\n")
    f.write(f"label,n,exp_decap_cell,hit2R_cell,null_result\n")
    f.write(f"{nullrow['label']},{nullrow['n']},{nullrow.get('exp_decap')},{nullrow.get('hit2R')},{nullrow['note']}\n")

# ---- TAREFA 6: estabilidade por contexto ----
CTXS = ['demand_reclaim', 'bottom_reversal_capitulation', 'bull_pullback_continuation', 'late_top_exhaustion', 'bear_bounce', 'liquidity_sweep_reversal', 'mid_range_noise']
byctx = []
for ctx in CTXS:
    ids = [i for i in CELL if sa.get(i) == ctx]
    b = block(ids, f"CELL@{ctx}")
    byctx.append(b)
writecsv(f"{D}/l2_bpt_capit_rsi_validation_by_context_window.csv", byctx + res, COLS)

# ---- TAREFA 7: DA ----
cell = block(CELL, "_")
da_checks = [
    ("preregistro_antes_do_teste", "YES", "docs/XAU_4H_L2_BPT_CAPIT_RSI_OOS_PREREG.md congelado antes"),
    ("nenhuma_variante_testada", "YES", "só a regra congelada capit&rsi supportive"),
    ("nenhum_threshold_ajustado", "YES", "state() reusado fiel; sem retune"),
    ("outcome_so_pos_hoc", "YES", "cruzado após definir subset"),
    ("sem_aggregator", "YES", "nenhum"),
    ("sem_decisao_TAKE_nova", "YES", "decisions_merged só lido"),
    ("sem_promocao", "YES", "status não vira PROMOTED/DECISIVE"),
    ("n_reportado", "YES", f"n_cell={cell['n']} runners_capados={sum(1 for i in CELL if runner(i))}"),
    ("CI_incerteza_reportada", "YES", f"hit2_wilson={cell['hit2_wilson']}"),
    ("drop_top2_feito", "YES", f"drop2_decap={cell['drop2_decap']} vs exp_decap={cell['exp_decap']}"),
    ("controles_feitos", "YES", "capit/rsi alone, base, context-matched, nas benchmark"),
    ("context_matched_feito", "YES", f"random-matched null 10k: {nullrow.get('note','')}"),
    ("ultra_filter_risk_avaliado", "YES" if cell['n'] >= 5 else "FLAG", f"n_cell={cell['n']}; frequência {'ok p/ ler' if cell['n']>=10 else 'baixa'}; risco = matar lucro/frequência se virar filtro"),
    ("objetivo_lucro_nao_winrate", "YES", f"exp_decap={cell['exp_decap']} sumR_decap={cell['sumR_decap']} pf_decap={cell['pf_decap']}"),
    ("dependencia_cap_+3.9_avaliada", "YES", f"exp_capped={cell['exp_capped']} vs exp_decap={cell['exp_decap']}; drop2 remove 2 melhores"),
    ("engine_intocado", "YES", "nenhum arquivo de engine/decisões alterado"),
    ("producao_intacta", "YES", "sem chart/MCP/plot/SLIM/receiver"),
]
writecsv(f"{D}/l2_bpt_capit_rsi_validation_da.csv",
         [dict(check=c, result=r, detail=d) for c, r, d in da_checks], ['check', 'result', 'detail'])

# ---- print resumo ----
print(f"CELL capit+rsi: n={cell['n']} (runners capados={sum(1 for i in CELL if runner(i))}) contexts={sorted(x for x in CTX_CELL if x)}")
print(f"  exp_capped={cell['exp_capped']} exp_decap={cell['exp_decap']} (drop2_decap={cell['drop2_decap']}) sumR_decap={cell['sumR_decap']} pf_decap={cell['pf_decap']}")
print(f"  hit2R={cell['hit2R']}% wilson={cell['hit2_wilson']} stop={cell['stop']}% maxDD_decap={cell['maxDD_decap']} lose_streak={cell['lose_streak']}")
print(f"  random-matched null: {nullrow.get('note','')}")
print("\nPOR JANELA:")
for r in res:
    if r['label'].startswith('CELL_') and r['label'] != 'CELL_capit+rsi_ALL':
        print(f"  {r['label']:<18} n={r['n']:<2} exp_decap={r['exp_decap']:>6} sumR_decap={r['sumR_decap']:>6} hit2R={r['hit2R']}% pf_decap={r['pf_decap']}")
print("\nCONTROLES (exp_decap | hit2R | n | pf_decap):")
for r in ctrls:
    print(f"  {r['label']:<24} exp_decap={r['exp_decap']:>6} hit2R={r['hit2R']:>3}% n={r['n']:<3} pf_decap={r['pf_decap']}")
print("\nPOR CONTEXTO (célula):")
for b in byctx:
    if b['n'] > 0: print(f"  {b['label']:<40} n={b['n']:<2} exp_decap={b['exp_decap']:>6} hit2R={b['hit2R']}%")
