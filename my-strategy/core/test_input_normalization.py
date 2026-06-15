#!/usr/bin/env python3
"""Teste simples (sem framework) do módulo puro input_normalization.

Roda: python3 test_input_normalization.py
Sem IO real, sem rede, sem produção. Apenas asserts em funções puras.
"""
import sys
from input_normalization import (
    normalize_symbol, is_authorized_symbol, classify_input_event, compute_signal_hash,
)

CASES_ACCEPT = ["XAUUSD", "PEPPERSTONE:XAUUSD", "XAGUSD", "ETHUSD", "US500", "EURUSD", "USOUSD"]
CASES_REJECT = ["BTCUSD", "XPTUSD", "USDJPY", "OANDA:BTCUSD", "VANTAGE:USDJPY", "", None, "  "]

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


# 1. accepted symbols -> PEPPERSTONE:<BASE>
for s in CASES_ACCEPT:
    r = normalize_symbol(s)
    base = s.split(":")[-1].upper()
    check(r["ok"], f"ACCEPT esperado ok=True para {s!r} -> {r}")
    check(r["normalized_symbol"] == f"PEPPERSTONE:{base}",
          f"normalized esperado PEPPERSTONE:{base} para {s!r} -> {r['normalized_symbol']}")
    check(r["provider"] == "PEPPERSTONE", f"provider esperado PEPPERSTONE para {s!r}")
    e = classify_input_event({"symbol": s, "timeframe": "240"})
    check(e["accepted"] is True, f"classify accepted=True esperado para {s!r} -> {e}")

# 2. rejected symbols -> accepted False, com quarantine_reason
for s in CASES_REJECT:
    r = normalize_symbol(s)
    check(r["ok"] is False, f"REJECT esperado ok=False para {s!r} -> {r}")
    check(r["normalized_symbol"] == "", f"normalized vazio esperado para {s!r}")
    e = classify_input_event({"symbol": s, "timeframe": "240"})
    check(e["accepted"] is False, f"classify accepted=False esperado para {s!r}")
    check("quarantine_reason" in e and e["quarantine_reason"],
          f"quarantine_reason esperado para {s!r} -> {e}")

# 3. is_authorized_symbol
check(is_authorized_symbol("XAUUSD") and is_authorized_symbol("usousd"), "is_authorized whitelisted")
check(not is_authorized_symbol("BTCUSD") and not is_authorized_symbol(""), "is_authorized rejeita não-whitelist")

# 4. foreign provider em base autorizada -> normaliza p/ PEPPERSTONE (legacy proven-safe)
r = normalize_symbol("OANDA:XAUUSD")
check(r["ok"] and r["normalized_symbol"] == "PEPPERSTONE:XAUUSD"
      and r["reason"] == "replaced_oanda_with_pepperstone",
      f"OANDA:XAUUSD deveria normalizar p/ PEPPERSTONE (replaced) -> {r}")

# 5. signal_hash determinístico
ev = {"symbol": "XAUUSD", "timeframe": "240", "ts_signal": "2025-08-27T18:00:00",
      "indicator_name": "Custom OB", "signal_type": "demand"}
h1 = compute_signal_hash(ev)
h2 = compute_signal_hash(dict(ev))
check(h1 == h2 and isinstance(h1, str) and len(h1) == 16, f"signal_hash determinístico 16-char -> {h1} {h2}")
# hash muda com campo distinto
h3 = compute_signal_hash({**ev, "timeframe": "60"})
check(h3 != h1, "signal_hash deve mudar com timeframe diferente")

if fails:
    print(f"FAIL ({len(fails)}):")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print(f"PASS — todos os asserts OK (accept={len(CASES_ACCEPT)}, reject={len(CASES_REJECT)}, + foreign/hash/auth)")
