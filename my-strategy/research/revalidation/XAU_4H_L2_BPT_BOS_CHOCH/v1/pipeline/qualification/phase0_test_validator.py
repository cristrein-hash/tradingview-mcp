#!/usr/bin/env python3
"""FASE 0 — testa schema+validador em 5 fixtures (1 TAKE-win,1 TAKE-lose,1 SKIP-win,1 SKIP-lose,1 REVIEW).
NÃO gera decisão nova, NÃO altera outcome, NÃO roda agentes. Só valida o schema/validador com
evidências válidas E inválidas propositais. Relatório: results/l2_bpt_multi_agent_phase0_schema_validation.csv"""
import os,sys,csv,json,glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_agent_evidence import validate_evidence
from multi_agent_schema import FACTORS
D="results"; RR="repro_recovery"
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_decisions_merged.csv"))}
out={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
pk={json.loads(l)['bar_idx']:json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
def win(i): return out[i]['exitype'].startswith('WIN')
# selecionar 1 de cada
want={'TAKE_win':None,'TAKE_lose':None,'SKIP_win':None,'SKIP_lose':None,'REVIEW':None}
for i in sorted(dec):
    if i not in out or i not in pk: continue
    d=dec[i]['decision']
    if d=='TAKE': key='TAKE_win' if win(i) else 'TAKE_lose'
    elif d=='SKIP': key='SKIP_win' if win(i) else 'SKIP_lose'
    elif d=='REVIEW': key='REVIEW'
    else: continue
    if want.get(key) is None: want[key]=i
fixtures={k:v for k,v in want.items() if v is not None}
print("fixtures:",{k:f"bar{v}({dec[v]['decision']},R={out[v]['realR']})" for k,v in fixtures.items()})

def real_val(p,f):
    return p.get(f)
rows=[]
for fxid,bi in fixtures.items():
    p=pk[bi]
    # achar 1 fator não-null permitido p/ demand_supply e p/ rsi_momentum (p/ evidência válida)
    valid_factor=next((f for f in ['dist_4h_demand_low_atr','rsi_min8','legpos90','drop20_atr'] if p.get(f) is not None),'rsi')
    fam_valid='demand_supply' if 'demand' in valid_factor else ('rsi_momentum' if 'rsi' in valid_factor else 'capitulation' if valid_factor=='drop20_atr' else 'exhaustion_top')
    base=dict(specialist_id=fam_valid,episode_id=dec[bi].get('episode_id') or str(bi),
              factor_used=valid_factor,value=real_val(p,valid_factor),interpretation="valor consistente com a tese",
              impact="negative",strength="medium",decisive_or_supporting="supporting",causal=True)
    # bateria de testes: (descrição, evidência, esperado_valid)
    tests=[]
    tests.append(("VALID_real_factor_value", dict(base), True))
    tests.append(("INVALID_fake_factor", {**base,"factor_used":"supply_magic_xyz"}, False))
    tests.append(("INVALID_wrong_value_eco", {**base,"value":(real_val(p,valid_factor) or 0)+9.99}, False))
    tests.append(("INVALID_no_value", {k:v for k,v in base.items() if k!="value"}, False))
    tests.append(("INVALID_wrong_family", {**base,"specialist_id":"session_time","factor_used":"nas_long_new_8b","value":real_val(p,"nas_long_new_8b")}, False))
    tests.append(("INVALID_no_impact", {k:v for k,v in base.items() if k!="impact"}, False))
    tests.append(("INVALID_no_specialist", {k:v for k,v in base.items() if k!="specialist_id"}, False))
    tests.append(("INVALID_bad_impact", {**base,"impact":"muito_negativo"}, False))
    for desc,ev,exp in tests:
        res=validate_evidence(ev,p)
        ok=(res['valid']==exp)  # validador concorda com o esperado?
        rows.append(dict(fixture_id=f"{fxid}|bar{bi}|{desc}",evidence_valid=res['valid'],
                         invalid_reason=';'.join(res['reasons'])[:120],fields_checked=res['fields_checked'],
                         validator_pass_fail='PASS' if ok else 'FAIL'))
with open(f"{D}/l2_bpt_multi_agent_phase0_schema_validation.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['fixture_id','evidence_valid','invalid_reason','fields_checked','validator_pass_fail']);w.writeheader();w.writerows(rows)
npass=sum(1 for r in rows if r['validator_pass_fail']=='PASS')
print(f"\nTESTES: {npass}/{len(rows)} PASS (validador concorda com o esperado)")
for r in rows:
    if r['validator_pass_fail']=='FAIL': print("  FAIL:",r['fixture_id'],r['invalid_reason'])
print("\nVALIDADOR GLOBAL:", "PASS" if npass==len(rows) else "FAIL")
print("WROTE results/l2_bpt_multi_agent_phase0_schema_validation.csv")
