#!/usr/bin/env python3
"""AVALIAÇÃO DA SEMANA 27-31/07 — PARTE 1: trades IDEAIS do Cris (plotados no chart, tab 15M).
Lidos via research/read_trade_drawings.py (MCP tab-pinned); os 2 mais à direita EXCLUÍDOS por ordem do
Cris (boxes vivas p/ entrada a mercado, não trades). Datação = janela ideal (a instância de toque no entry
que vai a TP sem tocar SL — trades ideais são escolhidos com hindsight como as melhores entradas).
Fonte de preço = bar-store 15M (o mesmo do trading). Reprodutível (guard output-órfão)."""
import json, datetime as dt
from zoneinfo import ZoneInfo

LX = ZoneInfo("Europe/Lisbon")
STORE = "/Users/cristrein/tradingview-mcp/my-strategy/core/bar_store/store/bars_15m.jsonl"
WEEK_START = dt.datetime(2026, 7, 27, tzinfo=LX).timestamp()

# posições lidas do chart (read_trade_drawings.py, tab 15M 8DD9A79D, 2026-08-02);
# EXCLUÍDOS por ordem do Cris: LONG 4037.95 e LONG 4040.18 (boxes vivas, mais à direita)
TRADES = [
    ("SHORT", 4068.68, 4078.69, 4043.75),
    ("LONG",  4067.76, 4057.74, 4107.88),
    ("SHORT", 4088.35, 4104.81, 4018.04),
    ("LONG",  4011.48, 3994.50, 4110.47),
    ("SHORT", 4106.06, 4118.36, 4028.47),
    ("SHORT", 4089.57, 4101.86, 4038.69),
]


def load_bars():
    with open(STORE, "rb") as f:
        f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 260000))
        bars = [json.loads(l) for l in f.read().decode(errors="ignore").splitlines()
                if l.strip() and l[0] == "{"]
    return [b for b in bars if b["t"] >= WEEK_START]


def hm(t):
    return dt.datetime.fromtimestamp(t, LX).strftime("%a %d %H:%M")


def ideal_window(bars, d, e, sl, tp):
    """1ª instância de toque no entry cuja trajetória vai a TP sem tocar SL (a janela ideal)."""
    for i, b in enumerate(bars):
        if not (b["l"] <= e <= b["h"]):
            continue
        for b2 in bars[i + 1:]:
            if d == "LONG":
                if b2["l"] <= sl: break
                if b2["h"] >= tp: return bars[i]["t"], b2["t"]
            else:
                if b2["h"] >= sl: break
                if b2["l"] <= tp: return bars[i]["t"], b2["t"]
    return None


def main():
    bars = load_bars()
    print("dir     entry      SL      TP     R   RR   janela ideal (entry->TP sem SL)")
    tot = 0.0
    rows = []
    for d, e, sl, tp in TRADES:
        r = abs(e - sl); rr = abs(tp - e) / r
        w = ideal_window(bars, d, e, sl, tp)
        if w:
            tot += rr
            rows.append((d, e, sl, tp, r, rr, w))
            print(f"{d:6s}{e:8.2f}{sl:8.2f}{tp:8.2f}{r:6.1f}{rr:5.1f}   {hm(w[0])} -> TP {hm(w[1])}  +{rr:.1f}R")
        else:
            print(f"{d:6s}{e:8.2f}{sl:8.2f}{tp:8.2f}{r:6.1f}{rr:5.1f}   (sem janela TP-sem-SL na semana)")
    print(f"\nTOTAL dos {len(TRADES)} ideais: +{tot:.1f}R  (WR 100% por construção = são os ideais)")
    return rows


if __name__ == "__main__":
    main()
