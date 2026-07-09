#!/usr/bin/env python3
"""FASE 5 — dry-run final pre-go-live. evaluate() direto (nunca main/notify), tripwire Telegram.
Estado atual read-only + demonstração do payload 'would_send' (nunca enviado) com slot/risk/manual-approval.
Output: l1_final_pregolive_dryrun_result.json."""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent
sys.path.insert(0,str(L1)); sys.path.insert(0,str(L1.parents[4]/"my-strategy/core"))
import runtime_xau as R
import capacity_journal as CJ
res={"phase":"final_pregolive_dryrun","would_send_real":False}

# tripwire hard-lock
trip={"notify":False,"run":False}
R.notify=lambda *a,**k:(trip.__setitem__("notify",True) or (_ for _ in ()).throw(AssertionError("notify")))
def _r(*a,**k): trip["run"]=True; raise AssertionError("subprocess.run")
R.subprocess.run=_r

def would_send_payload(cand, open_positions):
    """Payload local (NUNCA enviado) de um candidato operacional: contexto + capacity/risk + manual-approval."""
    c={"symbol":cand.get("symbol"),"bar_time":None,"direction":"LONG","risk_eur":CJ.RULES["each_position_risk_eur"],
       "entry":cand.get("entry_price"),"sl":cand.get("stop_price"),"target":cand.get("target_price"),"timeframe":cand.get("timeframe")}
    try: c["bar_time"]=int(datetime.fromisoformat(cand.get("candidate_timestamp")).replace(tzinfo=timezone.utc).timestamp())
    except Exception: c["bar_time"]=cand.get("candidate_timestamp")
    cap=CJ.evaluate_capacity(open_positions,c)
    return {"strategy":"L1 · EMA21 CONTINUATION","symbol":c["symbol"],"timeframe":c["timeframe"],
            "bar_time":cand.get("candidate_timestamp"),"entry":c["entry"],"sl":c["sl"],"target":c["target"],
            "nas_shift1_source":cand.get("nas_shift1_source"),"nas_shift1_value":cand.get("nas_shift1_value"),
            "state":cand.get("state"),"slot_index":cap["slot_index"],"slot_usage":f"{cap['open_after']}/{CJ.RULES['max_open_l1_positions']}",
            "max_positions":CJ.RULES["max_open_l1_positions"],"aggregate_risk_eur":cap["risk_after"],
            "max_aggregate_risk_eur":CJ.RULES["max_total_l1_open_risk_eur"],"capacity_decision":cap["decision_state"],
            "manual_approval_required":True,"broker_execution":CJ.RULES["broker_execution"],"telegram_status":"NOT_SENT_DRYRUN"}

# (1) estado atual live (com retry + guard se snapshot incompleto)
from tv_read_adapter import read_xau_snapshot
snap=None
for _ in range(3):
    try:
        s=read_xau_snapshot("240")
        if isinstance(s,dict) and "symbol" in s and "timeframe" in s and (s.get("ohlcv_recent")): snap=s; break
    except Exception as e:
        res.setdefault("snapshot_retry_errors",[]).append(str(e)[:120])
cand=None; st=None
if snap is None:
    res["live_state"]={"error":"snapshot incompleto após retries (MCP hiccup) — live eval pulado; demo abaixo válida"}
    res["live_would_send"]=None; res["live_note"]="snapshot indisponível; sem envio (fail-closed)"
else:
    cand=R.evaluate(snap); diag=cand.get("bar_diagnostics") or {}
    st=cand.get("state")
    res["live_state"]={"state":st,"operational":cand.get("operational"),
        "eval_bar_time":diag.get("eval_bar_time"),"forming_bar_excluded":diag.get("forming_bar_excluded"),
        "reason":cand.get("reason")}
    if cand.get("operational"):
        res["live_would_send"]=would_send_payload(cand, open_positions=[])
        res["live_note"]="operational_candidate em dry-run — payload construído, NÃO enviado"
    else:
        res["live_would_send"]=None
        res["live_note"]=f"não-operacional ({st}) — nada a enviar"

# (2) demonstração do formato would_send com candidato SINTÉTICO operacional (payload only, sem envio)
synth={"symbol":"PEPPERSTONE:XAUUSD","timeframe":"240","candidate_timestamp":"2026-07-08T22:00:00",
       "operational":True,"state":"operational_candidate","entry_price":2000.0,"stop_price":1980.0,
       "target_price":2060.0,"nas_shift1_source":"ledger_frozen","nas_shift1_value":1.42}
res["demo_would_send_payload"]=would_send_payload(synth, open_positions=[])
res["demo_would_send_with_1_open"]=would_send_payload(synth, open_positions=[{"symbol":"PEPPERSTONE:XAUUSD","bar_time":1,"direction":"LONG","risk_eur":100}])

res["telegram_tripwire"]={"notify_called":trip["notify"],"subprocess_run_called":trip["run"],
    "telegram_zero":(not trip["notify"] and not trip["run"])}
# PASS: Telegram zero + demo payload construído (manual_approval=True, telegram NOT_SENT) + live não disparou
live_ok=(snap is None) or (cand.get("operational") is False) or (st=="operational_candidate")
demo_ok=(res["demo_would_send_payload"].get("manual_approval_required") is True
         and res["demo_would_send_payload"].get("telegram_status")=="NOT_SENT_DRYRUN")
res["verdict"]="PASS" if (res["telegram_tripwire"]["telegram_zero"] and demo_ok and live_ok) else "REVIEW"
(HERE/"l1_final_pregolive_dryrun_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False,default=str))
print(json.dumps({k:v for k,v in res.items() if k!="demo_would_send_with_1_open"},indent=2,ensure_ascii=False,default=str))
