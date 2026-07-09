#!/usr/bin/env python3
"""L1_PRODUCTION_GATE_DRY_RUN — dry-run ÚNICO read-only da L1. HARD-LOCK Telegram: chama
runtime_xau.evaluate(snapshot) DIRETAMENTE — NUNCA main()/notify()/telegram_notify.py. Sem --send-telegram,
sem cycle, sem broker, sem produção. Lê snapshot live via tv_read_adapter (read-only MCP; sem draw/screenshot).
Reporta: bar fechado, NAS i-1 (ledger+live), fail-closed, estado final. Persist do eval_bar no ledger = capture
autorizado. Output: l1_production_gate_dry_run_result.json."""
import sys, json, inspect
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent
sys.path.insert(0,str(L1)); sys.path.insert(0,str(L1.parents[4]/"my-strategy/core"))
import runtime_xau as R

res={"phase":"production_gate_dry_run","telegram":"HARD_LOCKED (evaluate() direto; notify/main NÃO chamados)"}

# ---- HARD-LOCK em RUNTIME (tripwire — impossível de fingir): se notify/subprocess forem chamados,
# regista. Como só chamamos R.evaluate() (nunca R.notify/R.main), o tripwire NUNCA dispara. ----
src_main=inspect.getsource(R.main) if hasattr(R,"main") else ""
_tripwire={"notify_called":False,"subprocess_called":False}
def _trip_notify(*a,**k):
    _tripwire["notify_called"]=True
    raise AssertionError("HARD-LOCK VIOLADO: notify() foi chamado no dry-run")
R.notify=_trip_notify
import subprocess as _sp
_orig_run=_sp.run
def _trip_run(*a,**k):
    _tripwire["subprocess_called"]=True
    raise AssertionError(f"HARD-LOCK VIOLADO: subprocess chamado no dry-run: {a}")
_sp.run=_trip_run
if hasattr(R,"subprocess"): R.subprocess.run=_trip_run

# ---- snapshot live (read-only) ----
try:
    from tv_read_adapter import read_xau_snapshot
    snap=read_xau_snapshot("240")
    res["snapshot_meta"]={"symbol":snap.get("symbol"),"timeframe":snap.get("timeframe"),
        "bar_time":snap.get("bar_time"),"n_ohlcv":len(snap.get("ohlcv_recent") or []),
        "n_nas_series":len(snap.get("nas_series") or []),"n_rsi_series":len(snap.get("rsi_series") or []),
        "n_ob_zones":len(snap.get("ob_zones") or [])}
except Exception as e:
    res["snapshot_error"]=str(e)[:300]; snap=None

# ---- evaluate() DIRETO (sem notify/telegram) ----
if snap is not None:
    cand=R.evaluate(snap)
    diag=cand.get("bar_diagnostics") or {}
    now=int(datetime.now(timezone.utc).timestamp())
    res["dry_run"]={
        "state": cand.get("state"),
        "operational": cand.get("operational"),
        "candidate_timestamp": cand.get("candidate_timestamp"),
        "bar_diagnostics": diag,
        "bar_closed_confirmed": (diag.get("eval_bar_time") is not None and now >= (diag.get("eval_bar_time") or 0)+14400),
        "forming_bar_excluded": diag.get("forming_bar_excluded"),
        "nas_shift1_ledger_status": cand.get("nas_shift1_ledger_status"),
        "nas_shift1_value_used": cand.get("nas_shift1_value"),
        "nas_shift1_source": cand.get("nas_shift1_source"),
        "nas_shift1_live_value": cand.get("nas_shift1_live_value"),
        "ledger_persist_status": cand.get("ledger_persist_status"),
        "rsi_vs_ma": cand.get("rsi_vs_ma"),
        "entry_price": cand.get("entry_price"),"stop_price": cand.get("stop_price"),"target_price": cand.get("target_price"),
        "reason": cand.get("reason"),
    }
    # classificação do estado p/ os buckets do bloco
    st=cand.get("state")
    if st=="operational_candidate": bucket="operational_candidate"
    elif st=="blocked_exhaustion": bucket="blocked_exhaustion"
    elif st in ("blocked_missing_nas_shift1_ledger","blocked_nas_shift1_ledger_mismatch",
                "blocked_missing_closed_bar_study_values","blocked_bar_not_closed",
                "blocked_missing_base_rule_live_fields"): bucket="insufficient_source (fail-closed)"
    elif st=="blocked_l1_refined_filter": bucket="blocked_l1_refined_filter"
    else: bucket="no_candidate"
    res["state_bucket"]=bucket
    res["fail_closed_ok"]= (cand.get("operational") is True) or st.startswith("blocked") or st=="no_candidate"

    # ---- WARM DEMO (ledger TEMP; NÃO toca o real): seed do i-1 com o valor LIVE congelado da barra
    # fechada anterior (= o que um ciclo anterior teria persistido) -> demonstra o happy-path do SHIFT1.
    import tempfile
    prev_t=diag.get("previous_closed_bar_time")
    nas_by_t={r.get("time"): r.get("nas_dist") for r in (snap.get("nas_series") or []) if r.get("time") is not None}
    prev_live=nas_by_t.get(prev_t)
    real_fh=R.FEATURE_HISTORY
    try:
        tmp=Path(tempfile.mkdtemp())/"warm.jsonl"; R.FEATURE_HISTORY=tmp; R.STATE_DIR=tmp.parent
        if prev_t is not None and prev_live is not None:
            tmp.write_text(json.dumps({"bar_time":prev_t,"nas_dist":prev_live,
                "symbol":snap.get("symbol"),"timeframe":snap.get("timeframe")})+"\n")
        warm=R.evaluate(snap)
        res["warm_demo"]={"seeded_i_minus_1":{"bar_time":prev_t,"nas_dist":prev_live},
            "state":warm.get("state"),"nas_shift1_ledger_status":warm.get("nas_shift1_ledger_status"),
            "nas_shift1_value_used":warm.get("nas_shift1_value"),"nas_shift1_source":warm.get("nas_shift1_source"),
            "operational":warm.get("operational"),"reason":warm.get("reason"),
            "happy_path_ok": (warm.get("nas_shift1_ledger_status")=="ok"
                              and warm.get("state")!="blocked_missing_nas_shift1_ledger"
                              and warm.get("state")!="blocked_nas_shift1_ledger_mismatch")}
    finally:
        R.FEATURE_HISTORY=real_fh; R.STATE_DIR=real_fh.parent   # restaura ledger real

    # hardlock provado em runtime: o tripwire nunca disparou em NENHUMA das 2 chamadas evaluate()
    res["hardlock"]={
        "method":"runtime tripwire em R.notify + subprocess.run (rebentam se chamados)",
        "notify_called": _tripwire["notify_called"],
        "subprocess_called": _tripwire["subprocess_called"],
        "telegram_surface_zero": (not _tripwire["notify_called"] and not _tripwire["subprocess_called"]),
        "runtime_main_has_notify": ("notify(" in src_main)}
    res["dry_run_pass"]= bool(res["hardlock"]["telegram_surface_zero"] and res["fail_closed_ok"]
                              and res["dry_run"]["state"] is not None
                              and res["warm_demo"]["happy_path_ok"])
res["verdict"]="PASS" if res.get("dry_run_pass") else "REVIEW"
(HERE/"l1_production_gate_dry_run_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False,default=str))
print(json.dumps(res,indent=2,ensure_ascii=False,default=str))
