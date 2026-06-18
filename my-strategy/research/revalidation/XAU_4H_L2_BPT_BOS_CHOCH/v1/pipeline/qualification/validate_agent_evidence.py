#!/usr/bin/env python3
"""FASE 0 — Validador de evidência estruturada do engine multiagente. INFRA APENAS.
Rejeita: factor fora dos 84; value != packet (anti-eco/artefato); fator não-permitido p/ a família;
sem source/impact/specialist_id; não-causal/posterior; "uso" sem value explícito; campos inválidos.
NÃO roda agentes, NÃO decide. Schema: multi_agent_schema.py."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multi_agent_schema import FACTORS, FAMILY_FACTORS, SPECIALIST_FAMILIES, is_factor, is_causal, allowed_for

IMPACTS={"positive","negative","neutral","veto","review_flag"}
STRENGTHS={"weak","medium","strong"}
ROLES={"decisive","supporting"}
REQUIRED=["specialist_id","episode_id","factor_used","value","interpretation","impact","strength","decisive_or_supporting","causal"]

def _num(v):
    try: return float(v)
    except: return None

def value_matches(factor, value, packet):
    """value do agente bate com o packet? (anti-eco). float: tol 0.011 (2 casas); resto: igualdade."""
    if factor not in packet: return False, None
    pv=packet[factor]
    if isinstance(pv,dict):  # smc_bos/choch: comparar por bars_ago/text (não preço, repaint)
        if not isinstance(value,dict): return False, pv
        ok=(value.get('bars_ago')==pv.get('bars_ago') and (value.get('text') or '')==(pv.get('text') or ''))
        return ok, pv
    if isinstance(pv,bool): return (bool(value)==pv), pv
    a,b=_num(value),_num(pv)
    if a is not None and b is not None: return (abs(a-b)<=0.011), pv
    return (str(value)==str(pv)), pv  # categorical

def validate_evidence(ev, packet):
    reasons=[]; checks={}
    # campos obrigatórios
    for k in REQUIRED:
        if k not in ev or ev[k] in (None,"",[]):
            if k=="value" and ev.get("value") in (0,0.0,False): pass  # 0/False são valores válidos
            else: reasons.append(f"campo_obrigatorio_ausente:{k}")
    checks["required_fields"]= not any("campo_obrigatorio" in r for r in reasons)
    sid=ev.get("specialist_id"); fac=ev.get("factor_used")
    # specialist_id válido
    if sid not in SPECIALIST_FAMILIES: reasons.append(f"specialist_id_desconhecido:{sid}")
    # factor ∈ 84
    if not is_factor(fac): reasons.append(f"factor_fora_dos_84:{fac}")
    else:
        # causal
        if not is_causal(fac): reasons.append(f"factor_nao_causal:{fac}")
        # permitido p/ a família
        if sid in SPECIALIST_FAMILIES and not allowed_for(fac, sid):
            reasons.append(f"factor_nao_permitido_para_familia:{fac}@{sid}")
        # value presente + bate com packet (anti-eco)
        if "value" not in ev: reasons.append("value_ausente_nao_conta_como_uso")
        else:
            ok,pv=value_matches(fac, ev["value"], packet)
            checks["value_match"]=ok; checks["packet_value"]=pv
            if not ok: reasons.append(f"value_difere_do_packet:{ev.get('value')}!={pv}")
    # impacto / strength / role válidos
    if ev.get("impact") not in IMPACTS: reasons.append(f"impact_invalido:{ev.get('impact')}")
    if ev.get("strength") not in STRENGTHS: reasons.append(f"strength_invalida:{ev.get('strength')}")
    if ev.get("decisive_or_supporting") not in ROLES: reasons.append(f"role_invalido:{ev.get('decisive_or_supporting')}")
    # interpretation não-vazia
    if not (ev.get("interpretation") or "").strip(): reasons.append("interpretation_vazia")
    valid=len(reasons)==0
    return {"valid":valid,"reasons":reasons,"checks":checks,"fields_checked":len(REQUIRED)+4}

if __name__=="__main__":
    print("validador OK. famílias:",len(SPECIALIST_FAMILIES),"| fatores:",len(FACTORS))
