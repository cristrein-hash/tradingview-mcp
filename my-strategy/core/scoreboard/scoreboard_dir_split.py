#!/usr/bin/env python3
"""Split do scoreboard por DIREÇÃO (LONG/SHORT) por linha — pedido Cris 2026-08-19
(relatório de decisão separado por estratégia + reader + long/short). Reusa scoreboard.load_signals/resolve
(consumir, não reconstruir). Read-only; stdout apenas."""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scoreboard as sb


def main():
    T, H, L, C = sb.load_bars() if hasattr(sb, "load_bars") else (None, None, None, None)
    if T is None:
        bars = sb._jl(sb.STORE15)
        T = [b["t"] for b in bars]; H = [b["h"] for b in bars]; L = [b["l"] for b in bars]; C = [b["c"] for b in bars]
    agg = {}
    for s in sb.load_signals():
        r = sb.resolve(s, T, H, L, C)
        if not r:
            continue
        key = (s["src"], s.get("dir") or "LONG")
        a = agg.setdefault(key, {"n": 0, "w": 0, "l": 0, "o": 0, "sumR": 0.0})
        a["n"] += 1
        out = r.get("outcome") or r.get("res") or ""
        rr = r.get("R") if r.get("R") is not None else r.get("r3", 0)
        # fallback: infere do R
        if rr is None:
            rr = 0
        a["sumR"] += rr
        if rr > 0: a["w"] += 1
        elif rr < 0: a["l"] += 1
        else: a["o"] += 1
    print(f"{'linha':<12}{'dir':<7}{'N':>3}{'W-L-O':>9}{'sumR':>8}")
    for (src, d), a in sorted(agg.items()):
        print(f"{src:<12}{d:<7}{a['n']:>3}{a['w']:>4}-{a['l']}-{a['o']}{a['sumR']:>8.1f}")


if __name__ == "__main__":
    main()
