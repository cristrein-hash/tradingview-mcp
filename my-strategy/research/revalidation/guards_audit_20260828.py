#!/usr/bin/env python3
"""AUDITORIA GUARDS ANTI-FACA vs sinais da semana (Cris 28/08 'aposto que tem erros graves').
Ground truth: entry_t REAIS do ledger a1a2 × forward-logs dos guards (choch_guard.jsonl tick 300s +
sweep_reject_guard state/log). Pergunta por sinal: o guard X, no momento do envio, teria bloqueado?
Read-only. py3 stdlib."""
import json
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
LX = dt.timezone(dt.timedelta(hours=1))
WEEK0 = dt.datetime(2026, 8, 24, tzinfo=dt.timezone.utc).timestamp()


def jl(p):
    try:
        return [json.loads(l) for l in open(p).read().splitlines() if l.strip()]
    except Exception:
        return []


def hm(t):
    return dt.datetime.fromtimestamp(int(t), LX).strftime("%a %d/%m %H:%M")


sigs = [(r["entry_t"], r.get("ent")) for r in
        jl(REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2/.a1a2_state/alerted.jsonl")
        if (r.get("entry_t") or 0) >= WEEK0]

choch = jl(REPO / "alert-bridge/logs/choch_guard.jsonl")
sweep_log = []
# sweep guard: reconstruir timeline do estado (block desde/até) a partir do jsonl de estado se existir
for cand in ("alert-bridge/logs/sweep_reject_guard.jsonl", "alert-bridge/logs/sweep_reject.jsonl"):
    sweep_log = jl(REPO / cand)
    if sweep_log:
        break

print(f"sinais a1a2 na semana: {len(sigs)} · ticks choch: {len(choch)} · ticks sweep: {len(sweep_log)}")
print(f"{'sinal':<17}{'choch dn1h/dn4h/block':<26}{'Δlog':>7}  sweep@t")
for t, e in sigs:
    near = min(choch, key=lambda r: abs((r.get("logged_at") or 0) - t)) if choch else {}
    d = abs(near.get("logged_at", 0) - t)
    sw = "?"
    if sweep_log:
        ns = min(sweep_log, key=lambda r: abs((r.get("ts") or r.get("logged_at") or 0) - t))
        sw = f"block={ns.get('block')} (Δ{abs((ns.get('ts') or ns.get('logged_at') or 0)-t)}s)"
    print(f"{hm(t):<17}{str(near.get('dn_1h'))+'/'+str(near.get('dn_4h'))+'/'+str(near.get('block')):<26}{d:>6}s  {sw}")

# cobertura do log choch na semana (buracos)
ts = sorted(r.get("logged_at") or 0 for r in choch if (r.get("logged_at") or 0) >= WEEK0)
gaps = [(a, b) for a, b in zip(ts, ts[1:]) if b - a > 1800]
print(f"\nticks choch na semana: {len(ts)} · buracos >30min: {len(gaps)}")
for a, b in gaps[:8]:
    print(f"  {hm(a)} → {hm(b)} ({round((b-a)/3600,1)}h)")
