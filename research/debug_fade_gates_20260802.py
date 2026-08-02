#!/usr/bin/env python3
"""Sonda dos gates do R10 top_fade na janela do topo de 2ª-feira 27/07 (por que 0 candidatos?).
Reusa o modo --week do e1_replay (dados+synth); imprime, para cada barra da janela com CRUZ de rejeição
(pclose>=z.low -> close<z.low), o valor de cada gate: wick, sweep(ph60/swept), episódios, rsi<rsi_ma."""
import sys, bisect, json, datetime as dt
from pathlib import Path
BASE = Path("/Users/cristrein/tradingview-mcp/alert-bridge")
sys.path.insert(0, str(BASE))
import e1_replay as ER
import e1_detector as e1

rows = ER._load_store_15m()
mcp = ER.capture()
data = {"15": {"H": [b["h"] for b in rows], "L": [b["l"] for b in rows],
               "C": [b["c"] for b in rows], "T": [b["t"] for b in rows]}}
for tf in ("60", "240", "1D"):
    if tf in mcp: data[tf] = mcp[tf]
T15 = [b["t"] for b in rows]
Z = ER.WEEK_ZONES_240["above"]
print(f"zona supply: {Z['low']}-{Z['high']} | janela B: 26/07 22:00 -> 27/07 08:00 UTC (alargada a 27/07 16:00 p/ diagnóstico)")
W0, W1 = ER.WIN_B[0], ER.WIN_B[1] + 8 * 3600
prev = None
for i in range(45, len(rows)):
    t = T15[i]
    if not (W0 <= t <= W1):
        prev = rows[i]; continue
    b = rows[i]; pb = rows[i - 1]
    cross = pb["c"] >= Z["low"] and b["c"] < Z["low"]
    if cross:
        d = ER.synth(data, i)
        micro = d["axes"]["micro_15m"]
        atr15 = e1.atr_of((d["axes"]["mtf"].get("15", {}) or {}).get("leg") or {})
        tail = rows[max(0, i + 1 - e1.FADE_LOOKBACK_BARS):i + 1]
        swept = max(x["h"] for x in tail)
        ph60 = ((d["axes"]["mtf"].get("60", {}).get("swings") or {}).get("prev_high") or {}).get("price")
        wick = (b["h"] - max(b["o"], b["c"]))
        rsi = micro.get("rsi"); rsi_ma = micro.get("rsi_ma")
        # episódios
        eps = 0; in_ep = False; ep_rej = False
        for x in tail:
            if x["t"] >= t: break
            touch = x["h"] >= Z["low"]
            if touch and not in_ep: in_ep = True; ep_rej = x["c"] < Z["low"]
            elif touch and in_ep: ep_rej = x["c"] < Z["low"]
            elif not touch and in_ep:
                in_ep = False
                if ep_rej: eps += 1
        if in_ep and ep_rej: eps += 1
        hh = dt.datetime.utcfromtimestamp(t).strftime("%d %H:%M")
        print(f"CRUZ @{hh}UTC c={b['c']:.1f} | atr15={atr15 and round(atr15,1)} wick={wick:.1f} (min {atr15 and round(0.25*atr15,1)}) "
              f"| swept={swept:.1f} ph60={ph60} sweep_ok={ph60 and swept>ph60 and b['c']<ph60} "
              f"| eps={eps} (min 2) | rsi={rsi} rsi_ma={rsi_ma} rsi_ok={rsi is not None and rsi_ma is not None and rsi<rsi_ma}")
