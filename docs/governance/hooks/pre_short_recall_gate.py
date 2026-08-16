#!/usr/bin/env python3
"""GS3 — RECALL-GATE para labs XAU SHORT (Cris 2026-08-16, playbook Núcleo 6/Passo 2).
BLOQUEIA (exit 2) correr um BACKTEST/census/painel de expectância do SHORT SEM um `recall_report.json` fresco
que prove que o detetor RECAPTURA o Ground-Truth de shorts conhecidos (GT#1 13/08 4406,5→quebra→4356 + os casos
do critério de aceitação) com recall >= limiar pré-registado. Detetor que descarta os próprios winners → backtest
NULO (lição do censo L2/BPT −9,7R com recall 2/17). Força o Passo 2 do playbook ANTES da expectância.
Formato do report (o lab produz; a hook só verifica): {ts, threshold, recall, gt_total, gt_caught, detector}.
Escape auditável RECALL_WAIVED. Núcleo decide() puro = testável. py3 stdlib."""
import sys, json, re, time
from pathlib import Path

SHORT = re.compile(r"xau_short|xau_15m_short|short_lab|xau15m_short", re.I)
# a etapa que PRODUZ outcome/expectância (não o detetor/scan em si)
BACKTEST = re.compile(r"backtest|census|expectanc|panel|outcome|metrics|forward.?score", re.I)
REPORT_GLOBS = ("recall_report.json", "*recall*report*.json")
FRESH_S = 14 * 24 * 3600     # report válido <=14 dias


def _find_report(script):
    p = Path(script)
    for d in [p.parent] + list(p.parents)[:4]:
        for g in REPORT_GLOBS:
            try:
                for f in d.glob(g):
                    return f
            except Exception:
                pass
    return None


def decide(cmd, now=None):
    """(ok, msg) puro. now injetável p/ teste."""
    now = now if now is not None else time.time()
    low = (cmd or "").lower()
    if "recall_waived" in low:
        return True, ""
    m = re.search(r"python3?\s+(\S+\.py)", cmd or "")
    if not m:
        return True, ""
    script = m.group(1)
    if not (SHORT.search(script) or SHORT.search(low)):
        return True, ""
    if any(x in low for x in ("--selftest", "--show", "raw_reader", "plot_", "read_", "/hooks/")):
        return True, ""
    if not BACKTEST.search(script) and not BACKTEST.search(low):
        return True, ""
    f = _find_report(script)
    why = None
    if f is None:
        why = "sem recall_report.json no dir do lab"
    else:
        try:
            r = json.loads(f.read_text())
            thr = float(r.get("threshold", 0.0)); rec = float(r.get("recall", -1))
            age = now - float(r.get("ts", 0))
            if age > FRESH_S:
                why = f"recall_report velho ({int(age/86400)}d > 14d)"
            elif rec < thr:
                why = f"recall {rec:.2f} < limiar prereg {thr:.2f} (detetor descarta GT)"
            elif r.get("gt_total") and r.get("gt_caught", 0) < r.get("gt_total"):
                why = f"GT recapturado {r.get('gt_caught')}/{r.get('gt_total')} (< total)"
        except Exception as e:
            why = f"recall_report ilegível ({type(e).__name__})"
    if why is None:
        return True, ""
    return False, (
        "🛑 GS3 — BACKTEST SHORT SEM RECALL PROVADO (Cris 2026-08-16, playbook Passo 2)\n"
        f"  {why}.\n"
        "  Um detetor que não recaptura o GT (GT#1 13/08 4406,5→4356 + casos do critério de aceitação) torna o\n"
        "  backtest NULO (lição censo L2/BPT −9,7R, recall 2/17). Prova o RECALL antes da expectância.\n"
        "  → gera recall_report.json {ts, threshold, recall, gt_total, gt_caught, detector} no dir do lab, recall>=limiar.\n"
        "  → exceção deliberada: declara 'RECALL_WAIVED: <razão>'.\n")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") not in (None, "Bash"):
        return 0
    cmd = ((data.get("tool_input") or {}).get("command")) or ""
    ok, msg = decide(cmd)
    if ok:
        return 0
    try:
        import _guard_log; _guard_log.fire("gs3_short_recall", "block", "backtest SHORT sem recall provado")
    except Exception:
        pass
    sys.stderr.write(msg)
    return 2


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        import tempfile, os as _os, json as _j
        now = 1000000000
        t = []
        # 1) backtest SHORT sem recall_report → BLOQUEIA
        ok, _ = decide("python3 research/xau_15m_short/short_backtest.py", now=now)
        t.append(("backtest sem recall_report bloqueia", ok is False))
        # 2) RECALL_WAIVED → passa
        ok, _ = decide("python3 research/xau_15m_short/short_backtest.py  # RECALL_WAIVED: 1a corrida", now=now)
        t.append(("RECALL_WAIVED passa", ok is True))
        # 3) recall_report FRESCO e recall>=limiar → passa
        d = tempfile.mkdtemp(prefix="xau_short_lab_")
        open(_os.path.join(d, "recall_report.json"), "w").write(_j.dumps(
            {"ts": now - 100, "threshold": 0.8, "recall": 0.9, "gt_total": 3, "gt_caught": 3, "detector": "reclaim"}))
        ok, _ = decide(f"python3 {d}/short_backtest.py", now=now)
        t.append(("recall_report fresco+pass passa", ok is True))
        # 4) recall < limiar → BLOQUEIA
        open(_os.path.join(d, "recall_report.json"), "w").write(_j.dumps(
            {"ts": now - 100, "threshold": 0.8, "recall": 0.4, "gt_total": 3, "gt_caught": 1}))
        ok, _ = decide(f"python3 {d}/short_backtest.py", now=now)
        t.append(("recall<limiar bloqueia", ok is False))
        # 5) report velho (>14d) → BLOQUEIA
        open(_os.path.join(d, "recall_report.json"), "w").write(_j.dumps(
            {"ts": now - 20 * 86400, "threshold": 0.8, "recall": 0.9, "gt_total": 3, "gt_caught": 3}))
        ok, _ = decide(f"python3 {d}/short_backtest.py", now=now)
        t.append(("report velho bloqueia", ok is False))
        # 6) detetor/scan (não backtest) → passa (GS3 só na expectância)
        ok, _ = decide("python3 research/xau_15m_short/short_detector.py", now=now)
        t.append(("detector (nao-backtest) passa", ok is True))
        # 7) nao-short → passa
        ok, _ = decide("python3 research/xau_4h/backtest.py", now=now)
        t.append(("nao-short passa", ok is True))
        for lab, r in t:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        allok = all(r for _, r in t)
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    sys.exit(main())
