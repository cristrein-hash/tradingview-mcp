#!/usr/bin/env python3
"""ROTAÇÃO de logs de HEARTBEAT (C da auditoria 2026-07-18) — mantém as últimas N linhas de cada log
puramente OPERACIONAL (lido só por tail/última-linha). Reescrita atómica. py3.9 stdlib, diário.

⚠️ NUNCA toca:
  - e1_candidates.jsonl (lido por BYTE-OFFSET pelo E2 — truncar corromperia o offset)
  - ledgers analíticos/forward (e2_shadow/verdicts/outcomes/forward_notes, tradingview_alerts,
    indicator_signals) = DADOS, preservados integralmente.
Só a whitelist abaixo (heartbeat = ruído operacional reproduzível)."""
import os, json, datetime as dt
from pathlib import Path
REPO = Path("/Users/cristrein/tradingview-mcp")
KEEP = 5000
WHITELIST = [
    REPO / "my-strategy/core/bar_store/store/store_cycle.log",
    REPO / "my-strategy/strategies/xau_15m_long/reversal/CP_CAPITULATION/.cp_state/cp_cycle.log",
    REPO / "my-strategy/core/regime_engine/.regime_state/regime_cycle.log",
    REPO / "my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION/.runtime_state/l1_cycle.log",
    REPO / "my-strategy/strategies/xau_4h_long/reversal/L2_BPT_ZONE_TREND_EXIT/.runtime_state/l2_cycle.log",
    REPO / "my-strategy/core/stack_watchdog/.watchdog_state/watchdog.log",
    REPO / "alert-bridge/logs/e2_outcome_backfill.log",
    REPO / "external_factors_v2/snapshots/news_daemon.log",
    REPO / "external_factors_v2/snapshots/daemon.log",
]


def rotate(f, keep=KEEP):
    try:
        lines = f.read_text(errors="replace").splitlines()
    except Exception:
        return None
    if len(lines) <= keep:
        return 0
    cut = len(lines) - keep
    tmp = f.with_suffix(f.suffix + ".rot")
    tmp.write_text("\n".join(lines[-keep:]) + "\n")
    os.replace(tmp, f)
    return cut


def main():
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    out = {"ts": ts, "rotated": {}}
    for f in WHITELIST:
        if f.exists():
            n = rotate(f)
            if n:
                out["rotated"][f.name] = n
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
