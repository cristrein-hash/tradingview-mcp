#!/usr/bin/env python3
"""FASE 4 — check final SHIFT1/ledger causal + dry-run final. Sem Telegram (tripwire), sem cycle.
(A) re-assert dos guards (ledger TEMP): 2017 rejeitado (write+read), símbolo/tf errado bloqueia,
    mismatch detectável, NAS(i)!=i-1. (B) dry-run final live: evaluate() direto, barra fechada,
    estado + fonte do SHIFT1. Se operational_candidate: NÃO envia, só regista. Output json."""
import sys, json, tempfile
from pathlib import Path
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent; L1=HERE.parent
sys.path.insert(0,str(L1)); sys.path.insert(0,str(L1.parents[4]/"my-strategy/core"))
import runtime_xau as R
res={"phase":"preproduction_shift1_final_check"}

# tripwire hard-lock (Telegram impossível)
trip={"notify":False,"run":False}
R.notify=lambda *a,**k:(_ for _ in ()).throw(AssertionError("notify chamado"))
def _run_trip(*a,**k): trip["run"]=True; raise AssertionError("subprocess.run chamado")
R.subprocess.run=_run_trip

# (A) guards em ledger TEMP
real_fh=R.FEATURE_HISTORY
tmp=Path(tempfile.mkdtemp())/"g.jsonl"; R.FEATURE_HISTORY=tmp; R.STATE_DIR=tmp.parent
now=int(datetime.now(timezone.utc).timestamp()); recent=(now//14400)*14400-14400
guards={}
ok2017,st2017=R.persist_feature(1488207600,3.2); v2017,vs2017=R.nas_from_history(1488207600)
guards["corrupt_2017_rejected"]=(ok2017 is False and v2017 is None and "epoch_out_of_range" in vs2017)
R.persist_feature(recent,0.5)
_,stdup=R.persist_feature(recent,0.9)
guards["conflicting_dup_rejected"]=(stdup=="conflicting_duplicate")
vwrong,swrong=R.nas_from_history(recent,symbol="WRONG:SYM")
guards["wrong_symbol_rejected"]=(vwrong is None)
vok,sok=R.nas_from_history(recent)
guards["valid_read_ok"]=(vok==0.5 and sok=="ok")
vmiss,smiss=R.nas_from_history(recent-14400)
guards["missing_i_minus_1_none"]=(vmiss is None and smiss=="not_in_ledger")
R.FEATURE_HISTORY=real_fh; R.STATE_DIR=real_fh.parent   # restaura real
res["guards"]=guards; res["guards_all_pass"]=all(guards.values())

# (B) dry-run final live
from tv_read_adapter import read_xau_snapshot
snap=read_xau_snapshot("240")
cand=R.evaluate(snap)
diag=cand.get("bar_diagnostics") or {}
st=cand.get("state")
bucket=("operational_candidate" if st=="operational_candidate"
        else "blocked_exhaustion" if st=="blocked_exhaustion"
        else "insufficient_source (fail-closed)" if st.startswith("blocked")
        else "no_candidate")
res["dry_run_final"]={"state":st,"bucket":bucket,"operational":cand.get("operational"),
    "eval_bar_time":diag.get("eval_bar_time"),"previous_closed_bar_time":diag.get("previous_closed_bar_time"),
    "forming_bar_excluded":diag.get("forming_bar_excluded"),
    "bar_closed_confirmed":(diag.get("eval_bar_time") is not None and now>=(diag.get("eval_bar_time") or 0)+14400),
    "nas_shift1_ledger_status":cand.get("nas_shift1_ledger_status"),
    "nas_shift1_source":cand.get("nas_shift1_source"),"nas_shift1_value":cand.get("nas_shift1_value"),
    "reason":cand.get("reason")}
res["telegram_tripwire"]={"notify_called":trip["notify"],"subprocess_run_called":trip["run"],
    "telegram_zero":(not trip["notify"] and not trip["run"])}
# se por acaso operational -> registrar que NÃO se envia (dry-run)
res["would_send_telegram"]=False
res["operational_note"]=("ATENÇÃO: operational_candidate em dry-run — NÃO enviado (registro apenas)"
                         if st=="operational_candidate" else "não-operacional")
res["verdict"]="PASS" if (res["guards_all_pass"] and res["telegram_tripwire"]["telegram_zero"]
    and st is not None and (cand.get("operational") is False or st=="operational_candidate")) else "REVIEW"
(HERE/"l1_preproduction_shift1_final_check_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False,default=str))
print(json.dumps(res,indent=2,ensure_ascii=False,default=str))
