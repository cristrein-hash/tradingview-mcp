#!/usr/bin/env python3
"""BEAR-LEG + RANGE-CHOP BLOCK GATE com carve-out bottom/turn — DIAGNÓSTICO nos 62 (ensino).
Bloquear macro-bear-MARKDOWN-leg + range-chop losers, PRESERVANDO ao máximo: bull-run, bull-pullback E
bottom-reversal/pre-bull-turn (carve-out). Determinístico, causal (D1 shift D-1), sem outcome como predicado,
sem ID-fit. Engine/decisions/produção intocados. NÃO plotar (Cris avalia por plotagem depois)."""
import json,csv
from collections import Counter
D="results"
packs={json.loads(l)['plot_id']:json.loads(l) for l in open(f"{D}/l2_bpt_leg_state_d1_evidence_packs.jsonl")}
mat={r['plot_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0.csv"))}
cris={r['plot_id']:r['cris_verdict'] for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0_cris_verdicts.csv"))}
v1={r['plot_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_macro_specialist_confluence_62.csv"))}
def fn(v):
    try:return float(v)
    except:return None
def tb(v): return v in(True,'true','True','1',1)
def final(pid):
    c=cris.get(pid)
    if c:return 'PROTECT' if c.startswith('PROTECT') else('BLOCK' if c.startswith('BLOCK') else('REVIEW' if c.startswith('REVIEW') else('TRANSFORM' if c.startswith('TRANSFORM') else mat[pid]['visual_verdict'])))
    return mat[pid]['visual_verdict']
C_NAMED={'T34','T36','S39','S19','T27','S14'}
def setof(p):
    f=final(p)
    if p.startswith('S') and f=='PROTECT' and p not in C_NAMED: return 'A'
    if p.startswith('T') and f=='BLOCK' and p not in C_NAMED: return 'B'
    return 'C'

# THRESHOLDS DECLARADOS (não ID-fit)
DROP_CAP=2.5; RSI_OS=35
def gate(p):
    pk_=packs[p];leg=pk_['d1_macro_leg'];d1=pk_['d1_evidence'];R=v1[p]
    mb=tb(d1.get('macro_broken'));cs=fn(d1.get('regimeB_combined'));wsl=fn(d1.get('weekly_slope'))
    cap=pk_.get('capit',{});drop=fn(cap.get('drop20_atr'));rmin=fn(cap.get('rsi_min8'))
    recl=fn(pk_.get('entry_quality',{}).get('reclaim_body'));dem=R.get('demand');capstate=R.get('capit')
    # ---- CARVE-OUT bottom/turn (preserva mesmo com regime bear/atrasado) — exige sinal FORTE ----
    capit_reclaim = (drop is not None and drop>=DROP_CAP and rmin is not None and rmin<=RSI_OS and recl is not None and recl>0)
    climax = capstate=='CLIMAX_RECLAIM'
    bottom_turn = capit_reclaim or climax
    if bottom_turn:
        return 'PRESERVE_BOTTOM_TURN','carve-out: capitulation/climax reclaim (fundo a virar)'
    # ---- BLOQUEIO bear-markdown ----
    if leg=='MACRO_BEAR_LEG' or (mb and (cs is not None and cs<0)):
        return 'BLOCK_BEAR_MARKDOWN',f'leg={leg} macro_broken={mb} combined={cs}'
    # ---- BLOQUEIO range-chop (só em range NÃO macro-bull) ----
    if leg in('MACRO_RANGE','MACRO_TRANSITION') and not (cs is not None and cs>0) and not (wsl is not None and wsl>0):
        return 'BLOCK_RANGE_CHOP',f'leg={leg} combined={cs} weekly_slope={wsl} (range/transição sem macro-bull)'
    # ---- restante = contexto bull/accumulation -> permitir ----
    return 'ALLOW',f'leg={leg} (contexto bull/accumulation)'

rows=[]
for p in sorted(packs,key=lambda x:(setof(x),x[0],int(x[1:]))):
    dec,reason=gate(p);s=setof(p)
    blocked = dec.startswith('BLOCK')
    rows.append(dict(plot_id=p,set=s,datetime=packs[p]['datetime'],d1_macro_leg=packs[p]['d1_macro_leg'],
        gate_decision=dec,blocked=('YES' if blocked else 'NO'),reason=reason,
        cris_verdict=cris.get(p,final(p)),macro_v1_capit=v1[p].get('capit')))
with open(f"{D}/l2_bpt_bear_leg_block_gate_62.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
bym={r['plot_id']:r for r in rows}
print("=== gate decisions ===",dict(Counter(r['gate_decision'] for r in rows)))
print("\n=== blocked por SET (A=preservar 0 block ideal; B=bloquear losers; C=misto) ===")
for s in('A','B','C'):
    sub=[r for r in rows if r['set']==s]
    blk=sum(1 for r in sub if r['blocked']=='YES')
    print(f"  {s}: {blk}/{len(sub)} blocked")
# PRESERVAÇÃO: A-winners bloqueados (falhas) + must-preserve anchors
A=[p for p in bym if bym[p]['set']=='A']
A_blocked=[p for p in A if bym[p]['blocked']=='YES']
print(f"\n=== PRESERVAÇÃO ===")
print(f"  A-winners bloqueados (PERDAS a evitar): {len(A_blocked)}/{len(A)} -> {sorted(A_blocked,key=lambda x:int(x[1:]))}")
PRESERVE=['T34','T35','T37','S20','S24','S25','S26','S27','S29','S30','S31','S32','T39','T41','S35','S36','S37','S38']
pres_blocked=[p for p in PRESERVE if p in bym and bym[p]['blocked']=='YES']
print(f"  must-preserve anchors bloqueados: {len(pres_blocked)}/{len([p for p in PRESERVE if p in bym])} -> {pres_blocked}")
# bottom-turn carve-out aplicado a quem?
ct=[r['plot_id'] for r in rows if r['gate_decision']=='PRESERVE_BOTTOM_TURN']
print(f"  carve-out bottom/turn aplicado a {len(ct)}: {ct}")
# B bear/range losers bloqueados
B=[p for p in bym if bym[p]['set']=='B']
B_blocked=[p for p in B if bym[p]['blocked']=='YES']
print(f"\n=== BLOQUEIO (alvo) ===")
print(f"  B-set bloqueados: {len(B_blocked)}/{len(B)} -> {sorted(B_blocked,key=lambda x:int(x[1:]))}")
print(f"  B-set NÃO bloqueados (late-top-em-bull irredutível + bons): {sorted([p for p in B if bym[p]['blocked']=='NO'],key=lambda x:int(x[1:]))}")
