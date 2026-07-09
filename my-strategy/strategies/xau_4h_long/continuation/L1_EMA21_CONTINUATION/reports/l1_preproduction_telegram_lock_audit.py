#!/usr/bin/env python3
"""FASE 2 — auditoria do HARD-LOCK de Telegram (pre-production). NÃO envia nada.
Prova: (1) plist sem --send-telegram; (2) notify(send=True) sem env L1_PRODUCTION_AUTHORIZED -> NÃO
invoca telegram_notify (hard-lock retorna antes do subprocess); (3) dry-run (send=False) nunca passa
--send. Tripwire em subprocess.run intercepta/rebenta se chamado. Output: l1_preproduction_telegram_lock_result.json."""
import sys, json
from pathlib import Path
HERE=Path(__file__).resolve().parent; L1=HERE.parent
sys.path.insert(0,str(L1)); sys.path.insert(0,str(L1.parents[4]/"my-strategy/core"))
import runtime_xau as R
res={"phase":"preproduction_telegram_lock"}

# (1) plist sem --send-telegram — REPO E cópia DEPLOYADA (launchd lê a deployada)
import os as _os
plist=(L1/"com.cristrein.xau-l1-cycle.plist").read_text()
res["repo_plist_active_send_flag"]=("<string>--send-telegram</string>" in plist)
res["plist_note_present"]=("Telegram disabled until Cris explicitly authorizes production" in plist)
deployed=Path(_os.path.expanduser("~/Library/LaunchAgents/com.cristrein.xau-l1-cycle.plist"))
res["deployed_plist_exists"]=deployed.exists()
dep_txt=deployed.read_text() if deployed.exists() else ""
res["deployed_plist_active_send_flag"]=("<string>--send-telegram</string>" in dep_txt)
res["deployed_plist_note_present"]=("Telegram disabled until Cris explicitly authorizes production" in dep_txt)
res["plist_has_send_telegram_flag"]=(res["repo_plist_active_send_flag"] or res["deployed_plist_active_send_flag"])

# tripwire subprocess.run: intercepta args e rebenta (nada é realmente executado)
captured={"called":False,"args":None}
def _trip(*a,**k):
    captured["called"]=True; captured["args"]=a[0] if a else k.get("args")
    raise AssertionError("subprocess.run interceptado (nada enviado)")
R.subprocess.run=_trip

cand={"signal_hash":"probe","operational":True,"state":"operational_candidate"}

# (2) send=True SEM env -> hard-lock deve retornar ANTES do subprocess
import os
os.environ.pop("L1_PRODUCTION_AUTHORIZED",None)
captured["called"]=False
r_send_noenv=R.notify(cand, send=True, dedup_path=None)
res["send_true_no_env"]={"result":r_send_noenv,"subprocess_called":captured["called"],
    "pass":(r_send_noenv.get("sent") is False and "PRODUCTION_NOT_AUTHORIZED" in str(r_send_noenv.get("skip",""))
            and captured["called"] is False)}

# (3) send=False (dry-run default) -> pode chegar ao subprocess, mas SEM --send
captured["called"]=False; captured["args"]=None
try:
    R.notify(cand, send=False, dedup_path=None)
except AssertionError:
    pass
args=[str(x) for x in (captured["args"] or [])]
res["send_false_dryrun"]={"subprocess_called":captured["called"],"args":args,
    "no_send_flag_in_args":("--send" not in args),
    "pass":(captured["called"] is True and "--send" not in args)}

# (4) confirmação: _production_authorized default = False
res["production_authorized_default_false"]=(R._production_authorized() is False)

res["verdict"]="PASS" if (not res["plist_has_send_telegram_flag"] and res["plist_note_present"]
    and res["send_true_no_env"]["pass"] and res["send_false_dryrun"]["pass"]
    and res["production_authorized_default_false"]) else "REVIEW"
(HERE/"l1_preproduction_telegram_lock_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(json.dumps(res,indent=2,ensure_ascii=False))
