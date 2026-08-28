#!/usr/bin/env python3
"""Refresh periódico do liquidity_map (Cris 28/08: R8 pool_touch do E1 exige mapa <=1h). py3."""
import sys
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import liquidity_map as LM
m = LM.write_snapshot()
print("liquidity_map refresh: pools", len(m.get("pools", [])), "blocks", len(m.get("blocks", [])))
