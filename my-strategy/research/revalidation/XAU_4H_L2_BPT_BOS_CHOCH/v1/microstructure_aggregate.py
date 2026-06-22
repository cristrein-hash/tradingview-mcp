#!/usr/bin/env python3
"""MICRO-STRUCTURE LIQUIDITY ENGINE — agregação das 3 leituras de agentes (cegos, IDs opacos).
Decodifica opaque->plot_id (mapa oculto dos agentes), agrega consenso, checa alvos/contraste, cruza
camadas anteriores. DIAGNÓSTICO nos 62 ensino. Sem outcome como predicado (set/cris só p/ comparar leitura)."""
import csv, json
from collections import Counter

D = "results"
omap = json.load(open(f"{D}/_microstructure_opaque_map.json"))  # X## -> plot_id
v3 = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_bear_leg_block_gate_v3_62.csv"))}
feat = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_microstructure_feature_values_62.csv"))}

# leituras dos 3 agentes (state, confidence) por opaque id — transcritas dos retornos
A = {"X01":("MICRO_TOP_TRAP",.62),"X02":("MICRO_BOTTOM_RECLAIM",.55),"X03":("BREAKOUT_ACCEPTANCE",.66),
 "X04":("FAILED_BREAKOUT",.60),"X05":("BREAKOUT_ACCEPTANCE",.74),"X06":("BREAKOUT_ACCEPTANCE",.58),
 "X07":("BREAKOUT_ACCEPTANCE",.60),"X08":("BREAKOUT_ACCEPTANCE",.62),"X09":("MICRO_TOP_TRAP",.70),
 "X10":("MICRO_TOP_TRAP",.78),"X11":("MICRO_BOTTOM_RECLAIM",.50),"X12":("MICRO_TOP_TRAP",.64),
 "X13":("FAILED_BREAKOUT",.72),"X14":("LIQUIDITY_SWEEP_REVERSAL",.55),"X15":("BREAKOUT_ACCEPTANCE",.60),
 "X16":("BREAKOUT_ACCEPTANCE",.55),"X17":("MICRO_BOTTOM_RECLAIM",.58),"X18":("RANGE_CHOP",.50)}
B = {"X01":("MICRO_TOP_TRAP",.72),"X02":("BREAKOUT_ACCEPTANCE",.60),"X03":("BREAKOUT_ACCEPTANCE",.82),
 "X04":("FAILED_BREAKOUT",.60),"X05":("BREAKOUT_ACCEPTANCE",.85),"X06":("BREAKOUT_ACCEPTANCE",.62),
 "X07":("BREAKOUT_ACCEPTANCE",.66),"X08":("BREAKOUT_ACCEPTANCE",.68),"X09":("MICRO_TOP_TRAP",.80),
 "X10":("FAILED_BREAKOUT",.78),"X11":("BREAKOUT_ACCEPTANCE",.70),"X12":("MICRO_TOP_TRAP",.62),
 "X13":("FAILED_BREAKOUT",.74),"X14":("MICRO_BOTTOM_RECLAIM",.50),"X15":("BREAKOUT_ACCEPTANCE",.70),
 "X16":("BREAKOUT_ACCEPTANCE",.66),"X17":("BREAKOUT_ACCEPTANCE",.58),"X18":("RANGE_CHOP",.60)}
C = {"X01":("MICRO_TOP_TRAP",.72),"X02":("BREAKOUT_ACCEPTANCE",.60),"X03":("BREAKOUT_ACCEPTANCE",.78),
 "X04":("FAILED_BREAKOUT",.62),"X05":("BREAKOUT_ACCEPTANCE",.83),"X06":("BREAKOUT_ACCEPTANCE",.58),
 "X07":("BREAKOUT_ACCEPTANCE",.70),"X08":("BREAKOUT_ACCEPTANCE",.74),"X09":("MICRO_TOP_TRAP",.80),
 "X10":("MICRO_TOP_TRAP",.82),"X11":("BREAKOUT_ACCEPTANCE",.60),"X12":("MICRO_TOP_TRAP",.66),
 "X13":("FAILED_BREAKOUT",.78),"X14":("FAILED_BREAKOUT",.70),"X15":("BREAKOUT_ACCEPTANCE",.55),
 "X16":("BREAKOUT_ACCEPTANCE",.57),"X17":("FAILED_BREAKOUT",.50),"X18":("FAILED_BREAKOUT",.60)}

GOOD_STATES = {"BREAKOUT_ACCEPTANCE","MICRO_BOTTOM_RECLAIM","LIQUIDITY_SWEEP_REVERSAL"}
BAD_STATES = {"MICRO_TOP_TRAP","FAILED_BREAKOUT"}
# papel verdadeiro (do Cris) p/ COMPARAR a leitura (não é predicado dos agentes)
ROLE = {'T17':'BAD_micro_top','T20':'BAD_micro_top','T24':'BAD_micro_top','T40':'BAD_micro_top',
        'T23':'BAD_macrobear_accum','T32':'late_top_residual','T12':'corrective_blocked','T25':'corrective_blocked',
        'S12':'GOOD_contrast','S15':'GOOD_carveout_winner','S3':'GOOD_winner','S27':'GOOD_winner',
        'S20':'anchor_preserve','S24':'anchor_preserve','S25':'anchor_preserve','S29':'anchor_preserve',
        'S31':'anchor_preserve','S35':'anchor_preserve'}

rows = []
for x, pid in sorted(omap.items()):
    states = [A[x][0], B[x][0], C[x][0]]
    cons = Counter(states).most_common(1)[0]
    consensus = cons[0]; agree = cons[1]
    bad_votes = sum(1 for s in states if s in BAD_STATES)
    rows.append(dict(opaque=x, plot_id=pid, role=ROLE.get(pid, '?'), set=v3[pid]['set'],
        agentA=A[x][0], confA=A[x][1], agentB=B[x][0], confB=B[x][1], agentC=C[x][0], confC=C[x][1],
        consensus=consensus, agreement=f"{agree}/3", bad_votes=bad_votes,
        reads_as=('BAD' if bad_votes >= 2 else ('GOOD' if bad_votes == 0 else 'SPLIT')),
        d1_leg=feat[pid]['d1_leg'], sup_cat=feat[pid]['sup_cat'], pol_cat=feat[pid]['pol_cat'],
        dist_supply_atr=feat[pid]['dist_4h_supply_atr'], reclaim_body=feat[pid]['reclaim_body_atr']))
rows.sort(key=lambda r: (r['plot_id'][0], int(r['plot_id'][1:])))
with open(f"{D}/l2_bpt_microstructure_agent_readings_62.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(rows)
by = {r['plot_id']: r for r in rows}

print("=== LEITURA por trade (consenso 3 agentes) vs papel verdadeiro do Cris ===")
print(f"{'pid':5}{'role':22}{'reads_as':7}{'consensus':22}{'agree':6}")
for r in sorted(rows, key=lambda r: r['role']):
    print(f"  {r['plot_id']:5}{r['role']:22}{r['reads_as']:7}{r['consensus']:22}{r['agreement']:6}")

# ---- TARGET CHECK ----
CONTRAST_OUT = ['T21', 'T22', 'S11', 'S40']
tc = []
for p in ['T17', 'T20', 'T24', 'T40', 'T23', 'T32', 'S12', 'T21', 'T22']:
    if p in CONTRAST_OUT:
        tc.append(dict(plot_id=p, status='CONTRAST_OUT_OF_WORKING_SET', reads_as='-', consensus='-', note='citado pelo Cris, fora dos 62')); continue
    r = by[p]
    want_bad = ROLE.get(p, '').startswith('BAD')
    sep = 'SEPARATED' if (want_bad and r['reads_as'] == 'BAD') or (not want_bad and r['reads_as'] == 'GOOD') else 'NOT_SEPARATED'
    tc.append(dict(plot_id=p, status=ROLE.get(p), reads_as=r['reads_as'], consensus=r['consensus'],
                   note=f"separability={sep} agree={r['agreement']}"))
with open(f"{D}/l2_bpt_microstructure_target_check.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(tc[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(tc)
print("\n=== TARGET CHECK ===")
for r in tc: print(f"  {r['plot_id']:5} {r['status']:28} reads_as={r['reads_as']:6} consensus={r['consensus']:22} {r['note']}")

# ---- FALSE-FLAG diagnostic: a leitura 'BAD' atinge winners/anchors? ----
false_bad = [r['plot_id'] for r in rows if r['reads_as'] == 'BAD' and (r['role'].startswith('GOOD') or r['role'].startswith('anchor'))]
true_bad_flagged = [r['plot_id'] for r in rows if r['reads_as'] == 'BAD' and r['role'].startswith('BAD')]
bad_read_as_good = [r['plot_id'] for r in rows if r['role'].startswith('BAD') and r['reads_as'] == 'GOOD']
print("\n=== DECISÃO (a leitura microestrutural serve como filtro?) ===")
print(f"  BAD micro-tops que a leitura PEGOU (BAD): {true_bad_flagged}")
print(f"  BAD micro-tops que a leitura LEU COMO GOOD (não pegou): {bad_read_as_good}")
print(f"  FALSOS-BAD em winners/anchors (a leitura mataria winners): {false_bad}")

# ---- PRIOR LAYERS CROSSCHECK ----
pl = [
 ("sup_cat/pol_cat (supply structure)", "DECISIVO p/ trap óbvio (near+rejecting), MAS marca GOOD breakouts-through-supply como trap", "util_mas_perigoso"),
 ("dist_4h_supply_atr proximity", "único eixo que separa trap; porém dispara em winners que romperam supply (S15/S24)", "util_mas_perigoso"),
 ("reclaim_body sign + va_state (SVP)", "ABOVE_VAH+reclaim>0 compartilhado por acceptance E trap-near-supply = NÃO separa", "nao_separa"),
 ("legpos30/90 (leg position)", "alto em ambos good breakout e late-top; confound de escala persiste", "nao_separa"),
 ("drop20/rise20 (flush vs chase)", "FAILED_BREAKOUT (T20, below-VAL+neg reclaim) é o único padrão bad separável", "parcial"),
 ("bubbles order-flow", "forte buy-flow presente em acceptance E em blowoff-top (X15/X16) = não distingue", "nao_separa"),
 ("D1 leg-state backbone", "contexto macro correto (Bear-Leg Block v3 já usa); não resolve micro-top intra-bull", "contexto_only"),
 ("Bear-Leg Block v3 (corrective drop20)", "ortogonal: pega corrective raso, NÃO micro-top; T12/T25 leem como acceptance", "ortogonal_complementar"),
 ("entry-quality (refutado antes)", "confirmado de novo: entradas good/bad estruturalmente idênticas no ponto de entrada", "refutado_confirmado"),
]
with open(f"{D}/l2_bpt_microstructure_prior_layers_crosscheck.csv", "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n"); w.writerow(["layer", "finding_under_microstructure", "status"]); [w.writerow(r) for r in pl]
print("\n=== PRIOR LAYERS CROSSCHECK escrito (", len(pl), "camadas) ===")

# veredicto
print("\n=== VEREDICTO ===")
print(f"  T17 (BAD micro-top central): consenso 3/3 = {by['T17']['consensus']} -> lido como {by['T17']['reads_as']}")
print(f"  T20 (BAD micro-top): consenso 3/3 = {by['T20']['consensus']} -> {by['T20']['reads_as']} (separável)")
print(f"  S12 (GOOD contrast): consenso = {by['S12']['consensus']} -> {by['S12']['reads_as']}")
print(f"  Falsos-BAD em winners/anchors: {len(false_bad)} ({false_bad}) = filtro destruiria winners")
