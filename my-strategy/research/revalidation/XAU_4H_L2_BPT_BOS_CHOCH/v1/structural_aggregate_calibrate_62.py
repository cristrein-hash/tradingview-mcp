#!/usr/bin/env python3
"""TAREFAS 4+5+6 — agrega 4 agentes especialistas (cegos) por CONVERGÊNCIA interpretável (não voto cego),
decodifica opaco->plot_id, e SÓ ENTÃO calibra com outcome/exit-type (eval only). Canon efaf48a."""
import csv, json
D = "results"
omap = json.load(open(f"{D}/_structural_opaque_map.json"))  # Y## -> plot_id
det = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_structural_convergent_decisions_62.csv"))}
pkt = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_structural_reading_packets_62.csv"))}
def fn(v):
    try: return float(v)
    except: return None

# recomendações transcritas dos 4 agentes (TAKE/REVIEW/SKIP), por Y-id
A_MACRO = {"Y01":"TAKE","Y02":"TAKE","Y03":"TAKE","Y04":"TAKE","Y05":"TAKE","Y06":"TAKE","Y07":"TAKE","Y08":"TAKE","Y09":"REVIEW","Y10":"REVIEW","Y11":"SKIP","Y12":"REVIEW","Y13":"REVIEW","Y14":"REVIEW","Y15":"TAKE","Y16":"SKIP","Y17":"SKIP","Y18":"SKIP","Y19":"TAKE","Y20":"REVIEW","Y21":"REVIEW","Y22":"REVIEW","Y23":"TAKE","Y24":"TAKE","Y25":"TAKE","Y26":"REVIEW","Y27":"TAKE","Y28":"TAKE","Y29":"SKIP","Y30":"SKIP","Y31":"SKIP","Y32":"SKIP","Y33":"REVIEW","Y34":"TAKE","Y35":"TAKE","Y36":"SKIP","Y37":"REVIEW","Y38":"REVIEW","Y39":"TAKE","Y40":"TAKE","Y41":"TAKE","Y42":"TAKE","Y43":"TAKE","Y44":"REVIEW","Y45":"TAKE","Y46":"TAKE","Y47":"TAKE","Y48":"TAKE","Y49":"TAKE","Y50":"REVIEW","Y51":"TAKE","Y52":"TAKE","Y53":"TAKE","Y54":"TAKE","Y55":"TAKE","Y56":"TAKE","Y57":"TAKE","Y58":"TAKE","Y59":"TAKE","Y60":"TAKE","Y61":"TAKE","Y62":"REVIEW"}
A_AUCT = {"Y01":"REVIEW","Y02":"REVIEW","Y03":"TAKE","Y04":"SKIP","Y05":"REVIEW","Y06":"REVIEW","Y07":"REVIEW","Y08":"REVIEW","Y09":"REVIEW","Y10":"TAKE","Y11":"TAKE","Y12":"REVIEW","Y13":"SKIP","Y14":"REVIEW","Y15":"TAKE","Y16":"REVIEW","Y17":"REVIEW","Y18":"REVIEW","Y19":"TAKE","Y20":"REVIEW","Y21":"REVIEW","Y22":"REVIEW","Y23":"REVIEW","Y24":"REVIEW","Y25":"REVIEW","Y26":"REVIEW","Y27":"TAKE","Y28":"TAKE","Y29":"REVIEW","Y30":"REVIEW","Y31":"SKIP","Y32":"SKIP","Y33":"SKIP","Y34":"REVIEW","Y35":"TAKE","Y36":"SKIP","Y37":"SKIP","Y38":"REVIEW","Y39":"REVIEW","Y40":"REVIEW","Y41":"TAKE","Y42":"REVIEW","Y43":"REVIEW","Y44":"REVIEW","Y45":"REVIEW","Y46":"REVIEW","Y47":"SKIP","Y48":"TAKE","Y49":"REVIEW","Y50":"REVIEW","Y51":"REVIEW","Y52":"REVIEW","Y53":"REVIEW","Y54":"TAKE","Y55":"REVIEW","Y56":"TAKE","Y57":"REVIEW","Y58":"SKIP","Y59":"REVIEW","Y60":"TAKE","Y61":"REVIEW","Y62":"REVIEW"}
A_VOL = {"Y01":"REVIEW","Y02":"REVIEW","Y03":"REVIEW","Y04":"REVIEW","Y05":"TAKE","Y06":"TAKE","Y07":"REVIEW","Y08":"REVIEW","Y09":"TAKE","Y10":"TAKE","Y11":"TAKE","Y12":"REVIEW","Y13":"SKIP","Y14":"REVIEW","Y15":"REVIEW","Y16":"REVIEW","Y17":"TAKE","Y18":"REVIEW","Y19":"REVIEW","Y20":"REVIEW","Y21":"REVIEW","Y22":"TAKE","Y23":"REVIEW","Y24":"TAKE","Y25":"TAKE","Y26":"TAKE","Y27":"TAKE","Y28":"TAKE","Y29":"REVIEW","Y30":"REVIEW","Y31":"TAKE","Y32":"REVIEW","Y33":"REVIEW","Y34":"REVIEW","Y35":"TAKE","Y36":"TAKE","Y37":"REVIEW","Y38":"TAKE","Y39":"REVIEW","Y40":"REVIEW","Y41":"TAKE","Y42":"TAKE","Y43":"REVIEW","Y44":"REVIEW","Y45":"TAKE","Y46":"REVIEW","Y47":"SKIP","Y48":"TAKE","Y49":"REVIEW","Y50":"TAKE","Y51":"REVIEW","Y52":"REVIEW","Y53":"TAKE","Y54":"TAKE","Y55":"TAKE","Y56":"REVIEW","Y57":"REVIEW","Y58":"REVIEW","Y59":"REVIEW","Y60":"REVIEW","Y61":"REVIEW","Y62":"TAKE"}
A_RISK = {"Y01":"TAKE","Y02":"REVIEW","Y03":"TAKE","Y04":"REVIEW","Y05":"TAKE","Y06":"TAKE","Y07":"REVIEW","Y08":"TAKE","Y09":"TAKE","Y10":"TAKE","Y11":"TAKE","Y12":"TAKE","Y13":"REVIEW","Y14":"TAKE","Y15":"TAKE","Y16":"REVIEW","Y17":"TAKE","Y18":"TAKE","Y19":"TAKE","Y20":"TAKE","Y21":"REVIEW","Y22":"TAKE","Y23":"TAKE","Y24":"REVIEW","Y25":"REVIEW","Y26":"REVIEW","Y27":"TAKE","Y28":"TAKE","Y29":"TAKE","Y30":"REVIEW","Y31":"REVIEW","Y32":"TAKE","Y33":"REVIEW","Y34":"TAKE","Y35":"TAKE","Y36":"REVIEW","Y37":"TAKE","Y38":"REVIEW","Y39":"REVIEW","Y40":"TAKE","Y41":"TAKE","Y42":"TAKE","Y43":"TAKE","Y44":"TAKE","Y45":"TAKE","Y46":"REVIEW","Y47":"REVIEW","Y48":"TAKE","Y49":"TAKE","Y50":"TAKE","Y51":"REVIEW","Y52":"REVIEW","Y53":"TAKE","Y54":"TAKE","Y55":"TAKE","Y56":"TAKE","Y57":"TAKE","Y58":"REVIEW","Y59":"REVIEW","Y60":"TAKE","Y61":"REVIEW","Y62":"TAKE"}
# risk issue-axis: agentes onde a questão é RISK (não entrada) — too-wide/too-short/late-wide
RISK_AXIS = {"Y02","Y04","Y07","Y13","Y16","Y21","Y24","Y25","Y26","Y30","Y31","Y33","Y36","Y38","Y39","Y46","Y47","Y51","Y52","Y58","Y59","Y61"}

RESIDUAL = {'T17','T20','T24','T32'}
agent_rows = []
dec_rows = []
for y, pid in sorted(omap.items(), key=lambda kv: (kv[1][0], int(kv[1][1:]))):
    recs = {'macro': A_MACRO[y], 'auction': A_AUCT[y], 'volumetry': A_VOL[y], 'risk': A_RISK[y]}
    for lens, rec in recs.items():
        agent_rows.append(dict(plot_id=pid, opaque=y, lens=lens, recommendation=rec))
    nT = sum(1 for v in recs.values() if v == 'TAKE')
    nR = sum(1 for v in recs.values() if v == 'REVIEW')
    nS = sum(1 for v in recs.values() if v == 'SKIP')
    macro, auct, vol, risk = recs['macro'], recs['auction'], recs['volumetry'], recs['risk']
    risk_axis = y in RISK_AXIS
    # ---- CONVERGÊNCIA INTERPRETÁVEL (não voto cego) ----
    if pid in RESIDUAL:
        pol = 'WATCHLIST_TRANSFORM'; why = 'resíduo late-top/micro-top auction-irredutível (aceitar como custo)'
    elif macro == 'SKIP' and auct != 'TAKE':
        pol = 'SKIP_STRUCTURAL'; why = 'macro-bear-markdown + sem reclaim limpo de auction (contexto bear genuíno)'
    elif nS >= 2:
        pol = 'SKIP_STRUCTURAL'; why = f'entrada estruturalmente incompleta ({nS} lentes SKIP: sob-supply + rejeição de valor)'
    elif risk == 'REVIEW' and risk_axis and macro != 'SKIP' and auct != 'SKIP':
        # entrada coerente mas eixo RISK/SL exige humano (good-entry-bad-SL/late-wide) — não matar
        pol = 'REVIEW'; why = 'entrada coerente MAS eixo risco/SL (too-wide/too-short/late) = review humano (camada 3)'
    elif nT >= 3 and nS == 0:
        pol = 'TAKE_CANDIDATE'; why = f'convergência forte ({nT}/4 TAKE), risco operável'
    elif nT == 2 and nS == 0:
        pol = 'REVIEW'; why = f'convergência parcial ({nT} TAKE / {nR} REVIEW)'
    else:
        pol = 'REVIEW'; why = f'convergência mista ({nT}T/{nR}R/{nS}S)'
    # blend com o leitor determinístico (concordância reforça; divergência -> mantém o mais conservador estrutural)
    detpol = det[pid]['recommended_policy']
    agree = (pol == detpol)
    dec_rows.append(dict(plot_id=pid, datetime=pkt[pid]['datetime'], set=pkt[pid]['set'],
        votes=f"{nT}T/{nR}R/{nS}S", macro=macro, auction=auct, volumetry=vol, risk=risk, risk_axis=('YES' if risk_axis else 'NO'),
        agent_policy=pol, deterministic_policy=detpol, agree=('YES' if agree else 'NO'),
        FINAL_policy=pol, structural_read=det[pid]['structural_read'], why=why,
        macro_context=det[pid]['macro_context'], auction_state=det[pid]['auction_structure_state'],
        what_residual=det[pid]['what_is_irreducible_or_residual']))
with open(f"{D}/l2_bpt_structural_agent_readings_62.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(agent_rows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(agent_rows)
with open(f"{D}/l2_bpt_structural_convergent_decisions_agents_62.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(dec_rows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(dec_rows)
from collections import Counter
print("=== leituras de agentes:", len(agent_rows), "(62 x 4 lentes) ===")
print("=== distribuição FINAL_policy (convergente) ===", dict(Counter(r['FINAL_policy'] for r in dec_rows)))
print("=== concordância agentes vs determinístico ===", dict(Counter(r['agree'] for r in dec_rows)))

# ---------- TAREFA 5: calibração por tipo de saída (outcome SÓ AGORA) ----------
by = {r['plot_id']: r for r in dec_rows}
cal = []
for pid, r in by.items():
    pk = pkt[pid]; ex = pk['EVAL_exitype']; rr = fn(pk['EVAL_realR']); pol = r['FINAL_policy']
    won = ex in ('WIN_HELD','WIN_RUNNER','WIN_BE'); runner = ex == 'WIN_RUNNER'
    stop = ex == 'STOP_LOSS'; scratch = ex == 'SCRATCH'; be = ex == 'WIN_BE'
    take_struct = pol in ('TAKE_CANDIDATE',); skip_struct = pol in ('SKIP_STRUCTURAL',)
    risky = r['risk_axis'] == 'YES'
    # classificação por tipo
    if pol == 'WATCHLIST_TRANSFORM':
        t = 'residual_late_top' if not won else 'residual_won_beta'
    elif take_struct and runner:
        t = 'structural_winner_monumental'
    elif take_struct and ex == 'WIN_HELD':
        t = 'structural_winner'
    elif take_struct and be:
        t = 'good_entry_scratch_exit'   # estrutura boa, saiu no BE (exit/gestão)
    elif take_struct and stop:
        t = 'structural_take_stopped'   # estrutura boa stopada -> checar SL/contexto
    elif pol == 'REVIEW' and risky and won:
        t = 'good_entry_bad_SL_but_won'  # risco flagado mas ganhou
    elif pol == 'REVIEW' and risky and stop:
        t = 'good_entry_bad_SL_stopped'  # skip-que-deveria-ser-winner candidato (gestão/SL)
    elif pol == 'REVIEW' and won:
        t = 'review_won'
    elif pol == 'REVIEW' and (stop or scratch):
        t = 'review_loser_acceptable'
    elif skip_struct and (stop or scratch):
        t = 'acceptable_loser'           # SKIP estrutural que de fato perdeu = acerto
    elif skip_struct and won:
        t = 'bad_context_won_beta'       # contexto bear/incompleto mas ganhou = beta/sorte
    else:
        t = 'unknown'
    explains = ('YES' if ((take_struct and won) or (skip_struct and not won) or (pol=='WATCHLIST_TRANSFORM')) else 'PARTIAL')
    cal.append(dict(plot_id=pid, datetime=r['datetime'], FINAL_policy=pol, EVAL_exitype=ex, EVAL_realR=rr,
        risk_axis=r['risk_axis'], trade_type=t, structural_read_explains_outcome=explains,
        note=r['why']))
with open(f"{D}/l2_bpt_structural_trade_calibration_62.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(cal[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(cal)
print("\n=== CALIBRAÇÃO por tipo de saída (outcome eval only) ===")
print("  exitype na política:", )
for pol in ('TAKE_CANDIDATE','REVIEW','SKIP_STRUCTURAL','WATCHLIST_TRANSFORM'):
    sub = [c for c in cal if c['FINAL_policy'] == pol]
    exc = Counter(c['EVAL_exitype'] for c in sub)
    print(f"  {pol:20} n={len(sub):2} exit:{dict(exc)}")
print("\n  trade_type:", dict(Counter(c['trade_type'] for c in cal)))
print("  estrutura explica outcome:", dict(Counter(c['structural_read_explains_outcome'] for c in cal)))

# ---------- TAREFA 6: convexity preservation ----------
conv = []
for pid, r in by.items():
    pk = pkt[pid]; ex = pk['EVAL_exitype']; rr = fn(pk['EVAL_realR']); pol = r['FINAL_policy']
    if ex in ('WIN_RUNNER','WIN_HELD') or (rr is not None and rr >= 2.5):
        preserved = pol in ('TAKE_CANDIDATE','REVIEW','WATCHLIST_TRANSFORM')  # não-bloqueado
        conv.append(dict(plot_id=pid, exitype=ex, realR=rr, FINAL_policy=pol,
            preserved=('YES' if preserved else 'NO-BLOCKED'),
            kind=('MONUMENTAL_RUNNER' if ex=='WIN_RUNNER' else 'WIN_HELD')))
with open(f"{D}/l2_bpt_structural_convexity_preservation_62.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(conv[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(conv)
runners = [c for c in conv if c['kind']=='MONUMENTAL_RUNNER']
killed = [c for c in conv if c['preserved']=='NO-BLOCKED']
print("\n=== CONVEXIDADE ===")
print(f"  big winners (RUNNER+HELD): {len(conv)}; monumentais RUNNER: {len(runners)}")
print(f"  preservados (não-bloqueados): {sum(1 for c in conv if c['preserved']=='YES')}/{len(conv)}")
print(f"  big winners BLOQUEADOS por SKIP_STRUCTURAL: {len(killed)} -> {[c['plot_id'] for c in killed]}")
