#!/usr/bin/env python3
"""RESUMO P&L REAL POR MOTOR (pergunta Cris 28/08: o que deu lucro real e sinais operáveis sem drawdown
violento). Resolve cada ledger live contra bars_15m (SL-first, R do próprio sinal) + streak de perdas.
Materializado (regra output-órfão). py3 stdlib."""
import json
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
LX = dt.timezone(dt.timedelta(hours=1))
bars = [json.loads(l) for l in open(REPO / "my-strategy/core/bar_store/store/bars_15m.jsonl") if l.strip()]
T = [b["t"] for b in bars]; H = [b["h"] for b in bars]; L = [b["l"] for b in bars]


def res(t0, e, sl, tgt, lng=True):
    if not (t0 and e and sl and tgt):
        return "?", None
    i0 = next((i for i, t in enumerate(T) if t > t0), None)
    if i0 is None:
        return "FUT", None
    for i in range(i0, len(T)):
        if lng:
            if L[i] <= sl: return "LOSS", -1.0
            if H[i] >= tgt: return "WIN", round((tgt - e) / (e - sl), 1)
        else:
            if H[i] >= sl: return "LOSS", -1.0
            if L[i] <= tgt: return "WIN", round((e - tgt) / (sl - e), 1)
    return "OPEN", 0.0


def eng(name, path, lng=True):
    try:
        rows = [json.loads(l) for l in open(path) if l.strip()]
    except Exception:
        print(f"{name:<16} sem ledger"); return
    tot = 0.0; w = l = op = 0; streak = mx = 0
    for r in rows:
        o, R = res(r.get("entry_t") or r.get("t"), r.get("ent"), r.get("sl"), r.get("tgt"), lng)
        if R is None:
            continue
        tot += R; w += o == "WIN"; l += o == "LOSS"; op += o == "OPEN"
        streak = streak + 1 if o == "LOSS" else 0; mx = max(mx, streak)
    print(f"{name:<16} {len(rows):>3} sinais · {w}W-{l}L-{op}op · sumR {tot:+.0f} · pior sequência perdas {mx}")


print("=== P&L REAL POR MOTOR (ledger live, SL-first, R do sinal) ===")
eng("A1/A2 (todos)", REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2/.a1a2_state/alerted.jsonl")
eng("CP capitulação", REPO / "my-strategy/strategies/xau_15m_long/reversal/CP_CAPITULATION/.cp_state/alerted.jsonl")
print("\n(E2 reader, L1, L2, AMD: ver scoreboard forward canónico — reports/scoreboard_*.txt)")
