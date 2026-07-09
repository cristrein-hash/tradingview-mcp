#!/usr/bin/env python3
"""FINAL LIVE-XAU/240 DRY-RUN v2 — corrige os 2 achados do DA:
 (1) snapshot exige ob_zones NÃO-vazio (guard simétrico; o 0 anterior era leitura transiente — 12 boxes reais);
 (2) exercita o GATE COMPLETO end-to-end: além do estado cold (ledger real), roda uma variante com LEDGER
     TEMP quente (seed do i-1 = valor live CONGELADO da barra fechada anterior = o que um ciclo anterior
     teria persistido) -> scanner.evaluate corre sobre OHLCV/OB/RSI/regime live -> estado real do gate.
evaluate() direto (nunca main/notify), tripwire. NÃO envia, NÃO liga cycle, NÃO toca broker. NÃO polui o
ledger real (warm usa TEMP, restaurado). Output: l1_final_live_xau_dryrun_v2_result.json."""
import sys, json, time, tempfile
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent
sys.path.insert(0,str(L1)); sys.path.insert(0,str(L1.parents[4]/"my-strategy/core"))
import runtime_xau as R
import capacity_journal as CJ
BAR=14400; NAS="pkqE7L"
res={"phase":"final_live_xau_dryrun_v2"}
trip={"notify":False,"run":False}
R.notify=lambda *a,**k:(trip.__setitem__("notify",True) or (_ for _ in ()).throw(AssertionError("notify")))
def _r(*a,**k): trip["run"]=True; raise AssertionError("subprocess.run")
R.subprocess.run=_r
from tv_read_adapter import _MCP, read_xau_snapshot

# prep chart XAU/240 + NAS visível
c=_MCP(); c.start(); prep={}
try:
    st=c.call("chart_get_state"); prep["symbol"]=(st or {}).get("symbol"); prep["tf"]=(st or {}).get("resolution") or (st or {}).get("timeframe")
    if prep["symbol"]!="PEPPERSTONE:XAUUSD": c.call("chart_set_symbol",{"symbol":"PEPPERSTONE:XAUUSD"}); prep["set_symbol"]=True
    if str(prep["tf"])!="240": c.call("chart_set_timeframe",{"timeframe":"240"}); prep["set_tf"]=True
    di=c.call("data_get_indicator",{"entity_id":NAS})
    if (di or {}).get("visible") is False: c.call("indicator_toggle_visibility",{"entity_id":NAS,"visible":True}); prep["toggled_nas"]=True
    time.sleep(1.0)
finally:
    try: c.stop()
    except Exception: pass
res["chart_prep"]=prep

# snapshot com retries — guard SIMÉTRICO: exige ohlcv + nas_series + ob_zones não-vazios
snap=None; errs=[]
for a in range(6):
    try:
        s=read_xau_snapshot("240")
        ok=(isinstance(s,dict) and s.get("symbol")=="PEPPERSTONE:XAUUSD" and str(s.get("timeframe"))=="240"
            and s.get("ohlcv_recent") and s.get("nas_series") and s.get("ob_zones"))
        if ok: snap=s; break
        errs.append(f"a{a}: nas={len(s.get('nas_series') or []) if isinstance(s,dict) else '?'} ob={len(s.get('ob_zones') or []) if isinstance(s,dict) else '?'}")
    except Exception as e: errs.append(f"a{a}: {str(e)[:80]}")
    time.sleep(1.2)
res["snapshot_attempts"]=errs

if snap is None:
    res["verdict"]="BLOCKED_MCP"; res["note"]="snapshot XAU/240 com ob_zones indisponível após retries"
else:
    res["snapshot_meta"]={"symbol":snap.get("symbol"),"timeframe":snap.get("timeframe"),
        "n_ohlcv":len(snap.get("ohlcv_recent") or []),"n_nas_series":len(snap.get("nas_series") or []),
        "n_ob_zones":len(snap.get("ob_zones") or [])}
    # (A) COLD (ledger real): estado honesto de warmup
    cold=R.evaluate(snap); dcold=cold.get("bar_diagnostics") or {}
    res["cold_real_ledger"]={"state":cold.get("state"),"operational":cold.get("operational"),
        "eval_bar_time":dcold.get("eval_bar_time"),"previous_closed_bar_time":dcold.get("previous_closed_bar_time"),
        "nas_shift1_ledger_status":cold.get("nas_shift1_ledger_status")}
    # (B) WARM (ledger TEMP, i-1 congelado) -> GATE COMPLETO end-to-end
    prev_t=dcold.get("previous_closed_bar_time")
    nas_by_t={x.get("time"):x.get("nas_dist") for x in (snap.get("nas_series") or []) if x.get("time") is not None}
    prev_live=nas_by_t.get(prev_t)
    real_fh=R.FEATURE_HISTORY
    try:
        tmp=Path(tempfile.mkdtemp())/"warm.jsonl"; R.FEATURE_HISTORY=tmp; R.STATE_DIR=tmp.parent
        if prev_t is not None and prev_live is not None:
            tmp.write_text(json.dumps({"bar_time":prev_t,"nas_dist":prev_live,"symbol":snap.get("symbol"),"timeframe":"240"})+"\n")
        warm=R.evaluate(snap); dwarm=warm.get("bar_diagnostics") or {}
        now=int(datetime.now(timezone.utc).timestamp()); st=warm.get("state")
        res["warm_full_gate"]={
            "seeded_i_minus_1":{"bar_time":prev_t,"nas_dist":prev_live},
            "eval_bar_time":dwarm.get("eval_bar_time"),"forming_bar_excluded":dwarm.get("forming_bar_excluded"),
            "bar_closed_confirmed":(dwarm.get("eval_bar_time") is not None and now>=(dwarm.get("eval_bar_time") or 0)+BAR),
            "nas_shift1_source":warm.get("nas_shift1_source"),"nas_shift1_value":warm.get("nas_shift1_value"),
            "nas_shift1_ledger_status":warm.get("nas_shift1_ledger_status"),
            "state":st,"operational":warm.get("operational"),"reason":warm.get("reason"),
            "rsi_vs_ma":warm.get("rsi_vs_ma"),"entry":warm.get("entry_price"),"sl":warm.get("stop_price"),"target":warm.get("target_price"),
            "gate_ran_end_to_end":(warm.get("nas_shift1_ledger_status")=="ok")}
        res["warm_state_bucket"]=("operational_candidate" if st=="operational_candidate"
            else "blocked_exhaustion" if st=="blocked_exhaustion"
            else "blocked_l1_refined_filter" if st=="blocked_l1_refined_filter"
            else st if st.startswith("blocked") else "no_candidate")
    finally:
        R.FEATURE_HISTORY=real_fh; R.STATE_DIR=real_fh.parent
    # risk/capacity (report-only, 0 abertas)
    cap=CJ.evaluate_capacity([], {"symbol":"PEPPERSTONE:XAUUSD","bar_time":dcold.get("eval_bar_time"),"direction":"LONG","risk_eur":100})
    res["risk_slot_state"]={"open_l1_positions":0,"max_open_l1_positions":CJ.RULES["max_open_l1_positions"],
        "aggregate_open_risk_eur":0,"next_position_risk_eur":100,"max_total_l1_open_risk_eur":CJ.RULES["max_total_l1_open_risk_eur"],
        "duplicate_same_bar_status":"clear","capacity_decision":cap["decision_state"]}
    # would_send só se o gate completo deu operacional (NUNCA enviado)
    wf=res["warm_full_gate"]
    if wf["operational"]:
        res["would_send_payload"]={"strategy":"L1 · EMA21 CONTINUATION","symbol":"PEPPERSTONE:XAUUSD","timeframe":"240",
            "bar_time":wf["eval_bar_time"],"entry":wf["entry"],"sl":wf["sl"],"target":wf["target"],
            "nas_shift1_source":wf["nas_shift1_source"],"slot_usage":f"1/{CJ.RULES['max_open_l1_positions']}",
            "aggregate_risk_eur":100,"manual_approval_required":True,"telegram_status":"NOT_SENT_DRYRUN"}
        res["would_send"]=True
    else:
        res["would_send_payload"]=None; res["would_send"]=False
    res["verdict"]=("PASS_READY_FOR_GO_LIVE_DECISION" if (wf["gate_ran_end_to_end"] and wf["bar_closed_confirmed"]
        and res["snapshot_meta"]["n_ob_zones"]>0) else "PARTIAL_MORE_DRYRUN_REQUIRED")

res["telegram_tripwire"]={"notify_called":trip["notify"],"subprocess_run_called":trip["run"],
    "telegram_zero":(not trip["notify"] and not trip["run"])}
res["production_authorized"]=R._production_authorized()
(HERE/"l1_final_live_xau_dryrun_v2_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False,default=str))
print(json.dumps(res,indent=2,ensure_ascii=False,default=str))
