#!/usr/bin/env python3
"""PASSO 2 — discriminacao faca-vs-dip pela LIQUIDEZ (recomputada do RAW 15M por evento).
CONSUMIR context_liquidity (stateless, ja existe) — NAO reconstruir. Para cada evento choch_dn 15M da
semana, recomputa liquidez dos bars ate ao evento e regista direction + sequence.high/low.state + trapped.
move_class COMPLETO precisa de magnets/OB (snapshot-live) -> aqui fica parcial (sem opposing). confluence e
OB-tie = MCP/forward-only (nao ha historico RAW). py3."""
import sys
from pathlib import Path
ROOT = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(ROOT / "alert-bridge"))
sys.path.insert(0, str(ROOT / "research/xau_15m_short"))
import context_liquidity as CL
import week_factor_discovery_20260814 as W
from collections import Counter

bars = W.load(W.FILES["15M"])
ev = W.choch_events(bars)

rows = []
for i, s in ev:
    oc = W.outcome(bars, i, s, "15M")
    if not oc:
        continue
    win = bars[max(0, i - CL.LOOKBACK):i + 1]     # bars ate ao evento (causal)
    try:
        liq = CL.compute(win)
    except Exception as e:
        liq = {"err": str(e)}
    seq = liq.get("sequence", {})
    hi = seq.get("high", {}); lo = seq.get("low", {})
    rows.append({
        "label": oc["label"], "down": oc["down_atr"], "up": oc["up_atr"],
        "dir": liq.get("direction"), "move_class": liq.get("move_class"),
        "hi_state": hi.get("state"), "hi_trap": hi.get("trapped"),
        "lo_state": lo.get("state"), "lo_trap": lo.get("trapped"),
    })

print("=" * 84)
print("PASSO 2 — LIQUIDEZ por evento choch_dn 15M (semana) | rotulo objetivo faca/dip")
print("=" * 84)
for r in rows:
    print("  %-5s d%4.1f u%4.1f | dir=%-4s move=%-20s | HIGH %-12s trap=%-6s | LOW %-12s trap=%-6s"
          % (r["label"], r["down"], r["up"], r["dir"], str(r["move_class"]),
             str(r["hi_state"]), str(r["hi_trap"]), str(r["lo_state"]), str(r["lo_trap"])))

print("\n" + "=" * 84)
print("DISCRIMINACAO por rotulo")
print("=" * 84)
for lab in ("FACA", "DIP"):
    g = [r for r in rows if r["label"] == lab]
    if not g:
        continue
    print("\n%s (n=%d):" % (lab, len(g)))
    print("  direction:", dict(Counter(r["dir"] for r in g)))
    print("  move_class:", dict(Counter(r["move_class"] for r in g)))
    print("  HIGH.state:", dict(Counter(r["hi_state"] for r in g)))
    print("  LOW.state :", dict(Counter(r["lo_state"] for r in g)))
    print("  LOW.trap  :", dict(Counter(r["lo_trap"] for r in g)))
print("\n(move_class PARCIAL: sem magnets/OB historicos, perde INICIATIVA/MISTO. "
      "confluence + OB-tie = so forward/MCP. Amostra pequena — hipotese, nao prova.)")
