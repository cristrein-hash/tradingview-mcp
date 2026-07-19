#!/usr/bin/env python3
"""COPILOT/JOURNAL — resolução de outcome (P1). Fill quando o preço TOCA o entry (limit), depois SL-first
do RAW (barras 15M do store). Convenção conservadora idêntica ao b_forward/Cp: se SL e TP na MESMA barra
pós-fill -> LOSS. Zero-CDP (lê o store). Atualiza o rec in-place e devolve-o.
short: SL acima (sl>entry) = high>=sl · TP abaixo (tp<entry) = low<=tp.
long:  SL abaixo (sl<entry) = low<=sl  · TP acima  (tp>entry) = high>=tp."""
import datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
BAR_S = 900
_lx = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%Y-%m-%d %H:%M Lisboa")


def _finish(rec, outcome, bar):
    rec["status"] = outcome
    rec["resolved_ts"] = _lx(bar["t"])
    ft = rec.get("filled_bar_t") or bar["t"]
    rec["bars_to_resolve"] = int((bar["t"] - ft) / BAR_S)
    return rec


def resolve_trade(rec, bars15):
    if rec.get("status") not in ("PENDING", "FILLED"):
        return rec
    e, sl, tp, d = rec.get("entry"), rec.get("sl"), rec.get("tp"), rec.get("direction")
    if e is None or sl is None or tp is None or d not in ("short", "long"):
        return rec
    det = rec.get("detected_epoch") or 0
    fb = [b for b in bars15 if b.get("t", 0) >= det]
    filled = rec.get("status") == "FILLED"
    for b in fb:
        if not filled:
            if b["l"] <= e <= b["h"]:                    # limit encheu (preço tocou o entry)
                filled = True
                rec["status"] = "FILLED"; rec["filled_bar_t"] = b["t"]; rec["filled_ts"] = _lx(b["t"])
            continue                                     # não avalia SL/TP na própria barra do fill
        if b["t"] <= (rec.get("filled_bar_t") or 0):
            continue
        sl_touch = (b["h"] >= sl) if d == "short" else (b["l"] <= sl)
        tp_touch = (b["l"] <= tp) if d == "short" else (b["h"] >= tp)
        if sl_touch:                                     # SL-first conservador (mesmo se TP também na barra)
            return _finish(rec, "LOSS", b)
        if tp_touch:
            return _finish(rec, "WIN", b)
    return rec
