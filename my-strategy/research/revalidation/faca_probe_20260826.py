#!/usr/bin/env python3
"""Probe incidente 26/08 (Cris: '2 entradas sugeridas com faca caindo'): que sinais sairam nas ultimas
24h, contexto de preco na hora, e estado dos guards anti-faca (choch/sweep) no momento. Read-only."""
import json
import time
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
LX = dt.timezone(dt.timedelta(hours=1))
now = time.time()
cut = now - 36 * 3600


def jl(p):
    try:
        return [json.loads(l) for l in open(p).read().splitlines() if l.strip()]
    except Exception:
        return []


def hm(t):
    return dt.datetime.fromtimestamp(t, LX).strftime("%d/%m %H:%M")


print("=== SINAIS ENVIADOS últimas 36h ===")
for src, p, tk, ek, sk in [
    ("a1a2", "my-strategy/strategies/xau_15m_long/continuation_A1A2/.a1a2_state/alerted.jsonl", "entry_t", "ent", "sl"),
    ("cp", "my-strategy/strategies/xau_15m_long/reversal/CP_CAPITULATION/.cp_state/alerted.jsonl", "etime", "ent", "sl"),
]:
    for r in jl(REPO / p):
        t = r.get(tk) or 0
        if t >= cut:
            print(f"  {src} {hm(t)} entry {r.get(ek)} sl {r.get(sk)} tg_ok={r.get('tg_ok', r.get('telegram'))}")

print("\n=== E2 verdicts surfaced (enviados) últimas 36h ===")
for r in jl(REPO / "alert-bridge/logs/e2_verdicts.jsonl"):
    t = r.get("bar_time") or 0
    if t >= cut and r.get("surfaced"):
        lv = r.get("levels") or {}
        print(f"  e2 {hm(t)} {r.get('direction')} {r.get('rule')} entry {lv.get('entry')} conv {(r.get('thesis') or {}).get('conviction')}")

print("\n=== barras 15M em volta (contexto de preço) ===")
bars = jl(REPO / "my-strategy/core/bar_store/store/bars_15m.jsonl")
for b in bars[-120:]:
    if b["t"] >= cut:
        pass
last = bars[-40:]
print(f"  janela: {hm(last[0]['t'])} → {hm(last[-1]['t'])}")
hi = max(b["h"] for b in last); lo = min(b["l"] for b in last)
print(f"  high {hi:.1f} · low {lo:.1f} · último close {last[-1]['c']:.1f} · range {hi-lo:.0f}pts")

print("\n=== guards no estado atual ===")
import sys
sys.path.insert(0, str(REPO / "alert-bridge"))
try:
    import choch_guard as CHG
    v = CHG.verdict()
    print(f"  choch_guard: block={v.get('block')} dn1h={v.get('dn_1h')} dn4h={v.get('dn_4h')} age={v.get('dossier_age_s')}s")
    print(f"  blocks_long() = {CHG.blocks_long()}")
except Exception as e:
    print(f"  choch_guard ERR {e}")
try:
    import sweep_reject_guard as SRG
    print(f"  sweep_reject blocks_long = {SRG.blocks_long()}")
except Exception as e:
    print(f"  sweep_reject ERR {e}")
