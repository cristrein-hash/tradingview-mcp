#!/usr/bin/env python3
"""FINAL LIVE-XAU/240 DRY-RUN — repete o dry-run que falhou por hiccup MCP. evaluate() direto (nunca
main/notify), tripwire Telegram+subprocess. Garante chart em PEPPERSTONE:XAUUSD/240 + NAS visível
(gestão mínima de chart, como o cycle --manage-chart; sem draw/screenshot/trade). Aplica capacity_journal
report-only. NÃO envia, NÃO liga cycle, NÃO toca broker. Output: l1_final_live_xau_dryrun_result.json."""
import sys, json, time
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent
sys.path.insert(0,str(L1)); sys.path.insert(0,str(L1.parents[4]/"my-strategy/core"))
import runtime_xau as R
import capacity_journal as CJ
BAR=14400; NAS="pkqE7L"
res={"phase":"final_live_xau_dryrun"}

# tripwire hard-lock
trip={"notify":False,"run":False}
R.notify=lambda *a,**k:(trip.__setitem__("notify",True) or (_ for _ in ()).throw(AssertionError("notify")))
def _r(*a,**k): trip["run"]=True; raise AssertionError("subprocess.run")
R.subprocess.run=_r

from tv_read_adapter import _MCP, read_xau_snapshot

# (1) PREP mínima do chart: garantir XAU/240 + NAS visível/computado
c=_MCP(); c.start(); prep={}
try:
    st=c.call("chart_get_state")
    prep["symbol_before"]=(st or {}).get("symbol"); prep["tf_before"]=(st or {}).get("resolution") or (st or {}).get("timeframe")
    if prep["symbol_before"]!="PEPPERSTONE:XAUUSD":
        c.call("chart_set_symbol",{"symbol":"PEPPERSTONE:XAUUSD"}); prep["set_symbol"]=True
    if str(prep["tf_before"])!="240":
        c.call("chart_set_timeframe",{"timeframe":"240"}); prep["set_tf"]=True
    time.sleep(1.5)
    di=c.call("data_get_indicator",{"entity_id":NAS})
    if (di or {}).get("visible") is False:
        c.call("indicator_toggle_visibility",{"entity_id":NAS,"visible":True}); prep["toggled_nas_visible"]=True
        time.sleep(1.5)
    st2=c.call("chart_get_state")
    prep["symbol_after"]=(st2 or {}).get("symbol"); prep["tf_after"]=(st2 or {}).get("resolution") or (st2 or {}).get("timeframe")
finally:
    try: c.stop()
    except Exception: pass
res["chart_prep"]=prep

# (2) snapshot live com retries (contra hiccup)
snap=None; errs=[]
for attempt in range(5):
    try:
        s=read_xau_snapshot("240")
        if isinstance(s,dict) and s.get("symbol")=="PEPPERSTONE:XAUUSD" and s.get("ohlcv_recent") and s.get("nas_series") is not None:
            snap=s; break
        errs.append(f"attempt{attempt}: symbol={s.get('symbol') if isinstance(s,dict) else type(s)} n_ohlcv={len(s.get('ohlcv_recent') or []) if isinstance(s,dict) else 0}")
    except Exception as e:
        errs.append(f"attempt{attempt}: {str(e)[:100]}")
    time.sleep(1.0)
res["snapshot_attempts"]=errs

if snap is None:
    res["dry_run"]={"state":"BLOCKED_MCP","reason":"snapshot XAU/240 indisponível após 5 tentativas"}
    res["verdict"]="BLOCKED_MCP"
else:
    res["snapshot_meta"]={"symbol":snap.get("symbol"),"timeframe":snap.get("timeframe"),
        "n_ohlcv":len(snap.get("ohlcv_recent") or []),"n_nas_series":len(snap.get("nas_series") or []),
        "n_rsi_series":len(snap.get("rsi_series") or []),"n_ob_zones":len(snap.get("ob_zones") or [])}
    cand=R.evaluate(snap); diag=cand.get("bar_diagnostics") or {}
    now=int(datetime.now(timezone.utc).timestamp()); st=cand.get("state")
    res["dry_run"]={
        "eval_bar_time":diag.get("eval_bar_time"),"previous_closed_bar_time":diag.get("previous_closed_bar_time"),
        "forming_bar_excluded":diag.get("forming_bar_excluded"),
        "bar_closed_confirmed":(diag.get("eval_bar_time") is not None and now>=(diag.get("eval_bar_time") or 0)+BAR),
        "nas_live_n_bars":res["snapshot_meta"]["n_nas_series"],
        "nas_shift1_source":cand.get("nas_shift1_source"),"nas_shift1_value":cand.get("nas_shift1_value"),
        "nas_shift1_ledger_status":cand.get("nas_shift1_ledger_status"),
        "state":st,"operational":cand.get("operational"),"reason":cand.get("reason")}
    # bucket
    res["state_bucket"]=("operational_candidate" if st=="operational_candidate"
        else "blocked_exhaustion" if st=="blocked_exhaustion"
        else st if st.startswith("blocked") else "no_candidate")
    # risk/capacity (report-only; assume 0 posições abertas no dry-run)
    cap=CJ.evaluate_capacity([], {"symbol":"PEPPERSTONE:XAUUSD","bar_time":diag.get("eval_bar_time"),
        "direction":"LONG","risk_eur":CJ.RULES["each_position_risk_eur"]})
    res["risk_slot_state"]={"open_l1_positions":cap["open_before"],"max_open_l1_positions":CJ.RULES["max_open_l1_positions"],
        "aggregate_open_risk_eur":cap["risk_before"],"next_position_risk_eur":CJ.RULES["each_position_risk_eur"],
        "max_total_l1_open_risk_eur":CJ.RULES["max_total_l1_open_risk_eur"],
        "duplicate_same_bar_status":("dup" if "duplicate_same_bar_signal" in cap["reasons"] else "clear"),
        "capacity_decision":cap["decision_state"]}
    # would_send só se operacional (NUNCA enviado)
    if cand.get("operational"):
        res["would_send_payload"]={"strategy":"L1 · EMA21 CONTINUATION","symbol":cand.get("symbol"),
            "timeframe":cand.get("timeframe"),"bar_time":cand.get("candidate_timestamp"),
            "entry":cand.get("entry_price"),"sl":cand.get("stop_price"),"target":cand.get("target_price"),
            "nas_shift1_source":cand.get("nas_shift1_source"),"slot_usage":f"{cap['open_after']}/{CJ.RULES['max_open_l1_positions']}",
            "aggregate_risk_eur":cap["risk_after"],"manual_approval_required":True,"telegram_status":"NOT_SENT_DRYRUN"}
        res["would_send"]=True
    else:
        res["would_send_payload"]=None; res["would_send"]=False
    res["verdict"]=("PASS_READY_FOR_GO_LIVE_DECISION"
        if (res["dry_run"]["bar_closed_confirmed"] and st is not None) else "PARTIAL_MORE_DRYRUN_REQUIRED")

res["telegram_tripwire"]={"notify_called":trip["notify"],"subprocess_run_called":trip["run"],
    "telegram_zero":(not trip["notify"] and not trip["run"])}
res["production_authorized"]=R._production_authorized()
(HERE/"l1_final_live_xau_dryrun_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False,default=str))
print(json.dumps(res,indent=2,ensure_ascii=False,default=str))
