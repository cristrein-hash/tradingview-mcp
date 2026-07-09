#!/usr/bin/env python3
"""FASE 4 — audita a camada capacity_journal (pura, fail-closed, NÃO wired). Prova as regras:
max 2 posições, max 2 mesmo-símbolo, €200 agregado, €100/posição, duplicate-bar BLOCK, LONG-only,
sem hedge; + journal record com todos os campos mínimos. Output: l1_risk_capacity_journal_audit_result.json."""
import sys, json
from pathlib import Path
HERE=Path(__file__).resolve().parent; L1=HERE.parent
sys.path.insert(0,str(L1))
import capacity_journal as CJ
res={"phase":"risk_capacity_journal","rules":CJ.RULES}
XAU="PEPPERSTONE:XAUUSD"
def cand(bt=1000,risk=100,direction="LONG",sym=XAU): return {"symbol":sym,"bar_time":bt,"direction":direction,"risk_eur":risk}
def pos(bt,risk=100,direction="LONG",sym=XAU): return {"symbol":sym,"bar_time":bt,"direction":direction,"risk_eur":risk}
T={}

# 1) 0 abertas -> allow slot 0
r=CJ.evaluate_capacity([],cand(1000)); T["empty_allows_slot0"]={"r":r,"pass":(r["allow"] and r["slot_index"]==0 and r["risk_after"]==100)}
# 2) 1 aberta -> allow slot 1
r=CJ.evaluate_capacity([pos(900)],cand(1000)); T["one_open_allows_slot1"]={"r":r,"pass":(r["allow"] and r["slot_index"]==1 and r["risk_after"]==200)}
# 3) 2 abertas -> BLOCK (max posições)
r=CJ.evaluate_capacity([pos(900),pos(950)],cand(1000)); T["two_open_blocks"]={"r":r,"pass":(not r["allow"] and "max_open_l1_positions_reached" in r["reasons"])}
# 4) duplicado mesmo bar_time -> BLOCK
r=CJ.evaluate_capacity([pos(1000)],cand(1000)); T["duplicate_bar_blocks"]={"r":r,"pass":(not r["allow"] and "duplicate_same_bar_signal" in r["reasons"])}
# 5) SHORT -> BLOCK (LONG-only)
r=CJ.evaluate_capacity([],cand(1000,direction="SHORT")); T["short_blocks"]={"r":r,"pass":(not r["allow"] and any("LONG" in x for x in r["reasons"]))}
# 6) hedge presente (posição SHORT aberta) -> BLOCK
r=CJ.evaluate_capacity([pos(900,direction="SHORT")],cand(1000)); T["hedge_present_blocks"]={"r":r,"pass":(not r["allow"] and any("hedge" in x for x in r["reasons"]))}
# 7) risco por posição > €100 -> BLOCK
r=CJ.evaluate_capacity([],cand(1000,risk=150)); T["per_position_risk_blocks"]={"r":r,"pass":(not r["allow"] and "per_position_risk_exceeds_limit" in r["reasons"])}
# 8) risco agregado > €200 (2×100 + novo 100 = 300) via 2 abertas já barra por max, mas testar risco: 1 aberta €150 não permitido... usar risco agregado limite: 1 aberta €100 + nova €100 = €200 OK; forçar exceed com risco custom
r=CJ.evaluate_capacity([pos(900,risk=100)],cand(1000,risk=100)); agg_ok=r["allow"] and r["risk_after"]==200
# exceder: aberta €100, nova €100.01 -> per-position já barra; usar aberta €150 (inválida mas simula estado) + nova €100 -> agg 250
r2=CJ.evaluate_capacity([pos(900,risk=150)],cand(1000,risk=100)); T["aggregate_risk_blocks"]={"r":r2,"pass":(not r2["allow"] and "aggregate_open_risk_exceeds_limit" in r2["reasons"])}
T["aggregate_exact_200_ok"]={"risk_after":r["risk_after"],"pass":agg_ok}
# 9) missing symbol/bar_time -> BLOCK
r=CJ.evaluate_capacity([],{"direction":"LONG","risk_eur":100}); T["missing_fields_blocks"]={"r":r,"pass":(not r["allow"] and "missing_symbol_or_bar_time" in r["reasons"])}

# journal record: todos os campos
capr=CJ.evaluate_capacity([],cand(1000))
rec=CJ.build_journal_record({**cand(1000),"entry":2000,"sl":1980,"target":2060,"timeframe":"240"},
    capr,trade_id="L1-XAU-0001",signal_time="2026-07-09T02:00:00Z",source_snapshot="dryrun",created_at="2026-07-09T05:00:00Z")
missing=[f for f in CJ.JOURNAL_FIELDS if f not in rec]
T["journal_all_fields"]={"missing":missing,"human_status":rec["human_status"],"broker_status":rec["broker_status"],
    "telegram_status":rec["telegram_status"],"pass":(missing==[] and rec["telegram_status"]=="NOT_SENT"
    and rec["broker_status"].startswith("NOT_EXECUTED") and rec["decision_state"]=="ALLOW_MANUAL_APPROVAL")}

res["tests"]=T
res["all_pass"]=all(v["pass"] for v in T.values())
res["verdict"]="PASS" if res["all_pass"] else "REVIEW"
(HERE/"l1_risk_capacity_journal_audit_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print("verdict:",res["verdict"])
for k,v in T.items(): print(f"  {'PASS' if v['pass'] else 'FAIL'}  {k}")
