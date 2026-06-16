#!/usr/bin/env python3
"""Re-derivação MÍNIMA da L1 sob regime_l1_v4 (research/in-sample — NOT_VALIDATION).

Reusa o MESMO gate da scanner.py (sem duplicar lógica): varre todos os bars do RAW canônico
sob regime_l1_v4 (= regime que roda ao vivo) e compara com o set antigo (gerado sob regime_B_v3).
Diagnóstico apenas. NÃO é OOS, NÃO é prova de edge. Read-only; escreve só neste diretório.
"""
import json, sys
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).resolve().parent
L1 = HERE.parents[3] / "strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION"
sys.path.insert(0, str(L1))
import scanner  # MESMO gate (regime_l1_v4 já unificado)

OLD_TRADES = HERE.parents[0].parent / "XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5/rebuild_v3/trades.jsonl"
LABELED = {"preserved_winners": [1, 11, 36, 38], "rsi_blocked_losers": [3, 15, 18, 32]}

def norm(ts):  # "2020-06-18T02:00[:00]" -> "YYYY-MM-DDTHH:MM"
    return ts.replace("Z", "")[:16]

def run():
    S = scanner.build_series()
    # 1) novo set de candidatos sob regime_l1_v4 (loop todos os bars)
    new_cands = {}
    for i in range(60, S.N):
        passed, _r = scanner.gate_trace(S, i)
        if not passed:
            continue
        out = scanner.evaluate(S, i)
        new_cands[norm(out["timestamp"])] = {
            "ts": out["timestamp"], "state": out["state"],
            "operational": out["operational"], "exhaustion_gate": out["exhaustion_gate"],
            "rsi_vs_ma": out["rsi_vs_ma"],
        }
    # 2) set antigo (regime_B_v3) = rebuild_v3 trades (#1..#38)
    raw = open(OLD_TRADES).read()
    old = json.loads(raw)
    old_by_n = {t["n"]: t for t in old}
    old_ts = {norm(t["ts"]) for t in old}
    new_ts = set(new_cands.keys())

    preserved = sorted(old_ts & new_ts)
    removed = sorted(old_ts - new_ts)
    appeared = sorted(new_ts - old_ts)

    def status_of(n):
        t = old_by_n.get(n)
        if not t: return {"n": n, "error": "no_old_trade"}
        k = norm(t["ts"])
        nc = new_cands.get(k)
        return {"n": n, "ts": t["ts"], "old_cls": t.get("cls"), "old_R": t.get("R"),
                "still_candidate": nc is not None,
                "new_state": (nc["state"] if nc else "no_candidate(regime_l1_v4 dropped)"),
                "rsi_vs_ma": (nc["rsi_vs_ma"] if nc else None)}

    labeled = {grp: [status_of(n) for n in ns] for grp, ns in LABELED.items()}

    new_ops = sum(1 for c in new_cands.values() if c["operational"])
    new_blocked = sum(1 for c in new_cands.values() if c["state"] == "blocked_exhaustion")

    res = {
        "NOT_VALIDATION": True,
        "note": "Re-derivação in-sample sob regime_l1_v4 (regime LIVE). Diagnóstico, NÃO prova de edge. RAW canônico read-only.",
        "regime_source": "regime_l1_v4 (unificado com runtime_xau.py)",
        "old_set": {"source": "rebuild_v3/trades.jsonl (regime_B_v3)", "n": len(old)},
        "new_set_regime_l1v4": {"n_candidates": len(new_cands),
                                 "operational": new_ops, "blocked_exhaustion": new_blocked},
        "comparison": {"preserved": len(preserved), "removed_vs_old": len(removed),
                        "appeared_new": len(appeared)},
        "removed_timestamps": removed,
        "appeared_timestamps": appeared,
        "labeled_trades": labeled,
    }
    (HERE / "rederive_regime_l1v4.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return res

if __name__ == "__main__":
    run()
