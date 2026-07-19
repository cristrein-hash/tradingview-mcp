#!/usr/bin/env python3
"""COPILOT/JOURNAL — captura P0 (read-only, manual). Lê as trades do chart, deriva entry/SL/TP, e (com
--commit) congela o snapshot + regista no trades.jsonl. SEM daemon, SEM LLM, SEM resolve-loop (isso é P1).
Objetivo P0: PROVAR a correção da captura contra uma trade real do Cris (reproduz 4039/SL/TP).
Uso: python3 capture_trades.py          (só lê+imprime, não escreve)
     python3 capture_trades.py --commit (congela snapshot + regista no ledger)"""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))
import chart_read
import snapshot as snaplib
import ledger


def main():
    commit = "--commit" in sys.argv
    r = chart_read.read_trades()
    if not r.get("ok"):
        print(json.dumps(r, ensure_ascii=False)); return
    trades = r.get("trades", [])
    print(f"draw_list: {r.get('raw_n')} desenhos · {len(trades)} trade(s) detetada(s)"
          + (f" · {r.get('reason')}" if r.get("reason") else ""))
    existing = ledger.keys()
    for t in trades:
        if t.get("status") == "UNPAIRED":
            print(f"  {t['trade_id']} UNPAIRED (tag sem posição próxima) — não registo"); continue
        print(f"  {t['trade_id']} {t['direction'].upper()} entry {t['entry']} SL {t['sl']} TP {t['tp']} "
              f"RR {t['rr']} risk {t['risk']} · \"{t['reason']}\"")
        if commit:
            if ledger._key(t) in existing:
                print("    já no ledger (dedup) — skip"); continue
            snap = snaplib.build_snapshot()
            rec = ledger.append(t, snap)
            print(f"    -> registado ({rec['detected_ts']}) · snapshot {rec['snapshot_ref']} "
                  f"({len(json.dumps(snap))} bytes, price {snap.get('price_at_detection')})")
    if not commit and trades:
        print("(read-only — corre com --commit para congelar snapshot + registar)")


if __name__ == "__main__":
    main()
