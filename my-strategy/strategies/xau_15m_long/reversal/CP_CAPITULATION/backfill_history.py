#!/usr/bin/env python3
"""Cp — BACKFILL one-off do passado recente via MCP (gap pós-RAW: 2026-07-04 -> hoje). Pagina o buffer
em memória do chart 15M com data_get_ohlcv from_time/to_time (requer histórico carregado — scroll do
Cris se não alcançar) + pine_shapes 'Market Order' com max_bars grande. Merge nos MESMOS buffers do
runtime via update_buffers (mesma validação: grelha 15M, OHLC sanidade, dedup, retenção 10d, fechadas).
Read-only na tab; não troca chart. Uso: python3 backfill_history.py"""
import sys, os, json, time, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_cp_cycle as RC

iso = RC.iso
BAR_S = RC.BAR_S


def main():
    tid = RC.find_tab_15m()
    if not tid:
        print("SEM tab 15M"); return 1
    os.environ["TVMCP_TARGET_CHART_ID"] = tid
    now = int(time.time())
    t_from = now - RC.RETAIN_S                       # horizonte útil = retenção (10 dias)
    all_bars = {}
    from draw_xau_4h_trades import MCPClient
    c = MCPClient(); c.start()
    try:
        # janelas de 36h a paginar o buffer do chart
        w = 36 * 3600; t0 = t_from
        while t0 < now:
            t1 = min(now, t0 + w)
            oh = c.call_tool("data_get_ohlcv", {"from_time": t0, "to_time": t1, "count": 500}) or {}
            bars = oh.get("bars") or oh.get("ohlcv") or []
            for b in bars:
                if b.get("time") is not None:
                    all_bars[b["time"]] = b
            print(f"  janela {iso(t0)} -> {iso(t1)}: {len(bars)} barras (acum {len(all_bars)})")
            t0 = t1
        pb = c.call_tool("data_get_pine_shapes", {"study_filter": "Market Order", "max_bars": 2000}) or {}
    finally:
        c.stop()
    pairs = []
    for s in (pb or {}).get("studies", []):
        for a in s.get("activations", []):
            t = a.get("time")
            for plot in (a.get("shapes") or {}):
                pairs.append((t, plot))
    print(f"total: {len(all_bars)} barras únicas · {len(pairs)} activations bubbles")
    res, counts, err = RC.update_buffers(list(all_bars.values()), pairs)
    if err:
        print(f"HARD_STOP buffer: {err}"); return 1
    rows, bub = res
    print(f"buffer pós-merge: {len(rows)} barras ({iso(rows[0]['t'])} -> {iso(rows[-1]['t'])}) · "
          f"{len(bub)} bubbles · novos: {counts[0]} barras, {counts[1]} bubbles")
    # relatório de gaps de barras no buffer
    gaps = []
    for i in range(1, len(rows)):
        d = rows[i]["t"] - rows[i - 1]["t"]
        if d > BAR_S * 8 and not _weekend(rows[i - 1]["t"], rows[i]["t"]):
            gaps.append((rows[i - 1]["t"], rows[i]["t"]))
    if gaps:
        print("GAPS (não-fim-de-semana):")
        for a, b in gaps:
            print(f"  {iso(a)} -> {iso(b)}")
    else:
        print("sem gaps não-fim-de-semana")
    return 0


def _weekend(a, b):
    da = dt.datetime.utcfromtimestamp(a); db = dt.datetime.utcfromtimestamp(b)
    return da.weekday() == 4 and db.weekday() in (6, 0)   # sexta -> dom/seg


if __name__ == "__main__":
    sys.exit(main())
