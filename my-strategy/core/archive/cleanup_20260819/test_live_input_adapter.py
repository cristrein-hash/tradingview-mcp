#!/usr/bin/env python3
"""Teste simples (sem framework) do dry-run live input adapter.
Roda: python3 test_live_input_adapter.py — sem IO real, sem rede, sem produção.
"""
import sys
from live_input_adapter import adapt_live_event, L1_ROUTE

fails = []
def check(cond, msg):
    if not cond:
        fails.append(msg)

# 1. XAUUSD 4H -> accepted, PEPPERSTONE:XAUUSD, route L1, dry_run
r = adapt_live_event({"symbol": "XAUUSD", "timeframe": "4H", "time": "2025-08-27T18:00:00",
                      "indicator": "Custom OB", "signal_type": "demand"})
check(r["accepted"] is True, f"XAUUSD 4H accepted -> {r}")
check(r["normalized_symbol"] == "PEPPERSTONE:XAUUSD", "XAUUSD normalized")
check(r["strategy_route"] == L1_ROUTE, f"XAUUSD 4H route L1 -> {r['strategy_route']}")
check(r["dry_run"] is True and r["telegram_allowed"] is False and r["execution_mode"] == "NONE", "flags dry-run")

# 2. PEPPERSTONE:XAUUSD com timeframe '240' -> accepted, route L1
r2 = adapt_live_event({"symbol": "PEPPERSTONE:XAUUSD", "interval": "240"})
check(r2["accepted"] is True and r2["strategy_route"] == L1_ROUTE, f"PEPPERSTONE:XAUUSD 240 -> {r2}")

# 3. XAUUSD timeframe errado -> accepted true, route None (unsupported)
r3 = adapt_live_event({"symbol": "XAUUSD", "timeframe": "15"})
check(r3["accepted"] is True and r3["strategy_route"] is None and r3.get("route_note") == "unsupported_route",
      f"XAUUSD 15m -> accepted/unsupported -> {r3}")

# 4. BTCUSD 4H -> accepted false
r4 = adapt_live_event({"symbol": "BTCUSD", "timeframe": "4H"})
check(r4["accepted"] is False and r4.get("quarantine_reason"), f"BTCUSD rejeitado -> {r4}")

# 5. OANDA:BTCUSD -> accepted false
r5 = adapt_live_event({"symbol": "OANDA:BTCUSD", "timeframe": "4H"})
check(r5["accepted"] is False and r5.get("quarantine_reason"), f"OANDA:BTCUSD rejeitado -> {r5}")

# 6. sem símbolo -> accepted false
r6 = adapt_live_event({"timeframe": "4H"})
check(r6["accepted"] is False and r6.get("quarantine_reason"), f"sem símbolo rejeitado -> {r6}")

# 7. signal_hash determinístico
ev = {"symbol": "XAUUSD", "timeframe": "4H", "time": "2025-08-27T18:00:00",
      "indicator": "Custom OB", "signal_type": "demand"}
h1 = adapt_live_event(dict(ev))["signal_hash"]
h2 = adapt_live_event(dict(ev))["signal_hash"]
check(h1 == h2 and isinstance(h1, str) and len(h1) == 16, f"signal_hash determinístico -> {h1} {h2}")
check(adapt_live_event({**ev, "timeframe": "15"})["signal_hash"] != h1, "hash muda com timeframe diferente")

# 8/9. telegram_allowed false + execution_mode NONE em todos
for rr in (r, r2, r3, r4, r5, r6):
    check(rr["telegram_allowed"] is False, "telegram_allowed sempre false")
    check(rr["execution_mode"] == "NONE", "execution_mode sempre NONE")
    check(rr["dry_run"] is True, "dry_run sempre true")

if fails:
    print(f"FAIL ({len(fails)}):")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("PASS — adapter dry-run: 9 grupos de asserts OK (accept/reject/route/hash/flags)")
