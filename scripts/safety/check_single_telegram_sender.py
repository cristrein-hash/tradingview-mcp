#!/usr/bin/env python3
"""GUARD: sender Telegram único (DEEP_AUDIT_20260819 RC1 / invariante 19/08).
Falha (exit 1) se aparecer um POST a api.telegram.org fora da ALLOWLIST — deteta regressões da
centralização no notify.py. Allowlist = exceções documentadas com formato/destino próprios."""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ALLOW = {
    "alert-bridge/notify.py",                    # sender canónico (4 canais)
    "alert-bridge/tv_webhook_receiver.py",       # ingress TradingView (HTML próprio, documentado)
    "alert-bridge/telegram_assistant_bridge.py", # ponte bidirecional (chunks/long-poll)
    "alert-bridge/auto_d2r_daily.py",            # relatório D2R (HTML; consumido por tg_trade_signal)
    "alert-bridge/monitor_xau_4h_strategies.py", # LEGACY_DISABLED (trava dura no send)
    "my-strategy/core/stack_watchdog/stack_watchdog.py",  # só chk_network (não envia)
}
SCOPES = ["alert-bridge", "my-strategy/core", "my-strategy/strategies", "external_factors_v2/runtime",
          "external_factors_v2/collectors", "copilot"]


def main():
    bad = []
    for scope in SCOPES:
        p = REPO / scope
        if not p.exists():
            continue
        out = subprocess.run(["grep", "-rln", "api.telegram.org", "--include=*.py", str(p)],
                             capture_output=True, text=True).stdout
        for f in out.splitlines():
            rel = str(Path(f).relative_to(REPO))
            if "/archive/" in rel:
                continue                             # arquivado = fora do runtime, não conta
            if rel not in ALLOW:
                bad.append(rel)
    if bad:
        print("FAIL — senders Telegram fora da allowlist (migrar para alert-bridge/notify.py):")
        for b in sorted(set(bad)):
            print("  ", b)
        return 1
    print("PASS — nenhum sender Telegram fora da allowlist")
    return 0


if __name__ == "__main__":
    sys.exit(main())
