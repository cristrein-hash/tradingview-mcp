#!/usr/bin/env python3
"""FASE 3 — auditoria do escape manual telegram_notify.py --send. Prova que SEM env
L1_PRODUCTION_AUTHORIZED=1 o envio é BLOQUEADO (hard-lock no próprio sender). NUNCA testa o caminho
autorizado (env=1) — isso enviaria de verdade. Output: l1_telegram_escape_audit_result.json."""
import sys, json, subprocess, os
from pathlib import Path
HERE=Path(__file__).resolve().parent; L1=HERE.parent
TN=L1/"telegram_notify.py"
res={"phase":"telegram_escape_audit"}

# (1) estático: gate presente ANTES de send_telegram
src=TN.read_text()
res["has_production_gate"]=("_production_authorized" in src and "L1_PRODUCTION_AUTHORIZED" in src)
res["gate_before_send"]=(src.index("if args.send and not _production_authorized()") < src.index("ok = send_telegram(text)")) if ("if args.send and not _production_authorized()" in src and "ok = send_telegram(text)" in src) else False

# (2) runtime: --test --send SEM env -> deve bloquear (não envia). env limpo.
env=dict(os.environ); env.pop("L1_PRODUCTION_AUTHORIZED",None)
r=subprocess.run([sys.executable,str(TN),"--test","--send"],capture_output=True,text=True,env=env,timeout=30)
out=(r.stdout or "")+(r.stderr or "")
res["run_test_send_no_env"]={
    "returncode":r.returncode,
    "blocked_msg_present":("PRODUCTION_NOT_AUTHORIZED" in out),
    "dryrun_forced":("DRY-RUN FORÇADO" in out or "DRY-RUN FORCADO" in out),
    "no_real_send":("SENT=" not in out),   # send_telegram imprime SENT=... ; ausência = não enviou
}
res["run_test_send_no_env"]["pass"]=(res["run_test_send_no_env"]["blocked_msg_present"]
    and res["run_test_send_no_env"]["no_real_send"])

# (3) confirmação: env está unset agora
res["env_L1_PRODUCTION_AUTHORIZED_unset"]=(os.environ.get("L1_PRODUCTION_AUTHORIZED") is None)

res["verdict"]="PASS" if (res["has_production_gate"] and res["gate_before_send"]
    and res["run_test_send_no_env"]["pass"] and res["env_L1_PRODUCTION_AUTHORIZED_unset"]) else "REVIEW"
(HERE/"l1_telegram_escape_audit_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(json.dumps(res,indent=2,ensure_ascii=False))
