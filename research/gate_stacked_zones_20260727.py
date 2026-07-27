#!/usr/bin/env python3
"""GATE de deploy do E1_STACKED_ZONES (gap #1). 3 verificações, tudo read-only:
G1 PARIDADE flag-OFF: _zones_from_payload novo sobre o payload REAL do store == lógica antiga verbatim.
G2 RECALL topo 27/07: cenário da barra real 02:15 (pclose/close reais, zonas reais do store) —
   flag ON gera o SHORT zone_reject que faltou; flag OFF gera 0 (reproduz o miss real de hoje).
G3 CONTENÇÃO: no mesmo bar, os candidatos do stack partilham entry=close -> anti-spam por zona
   admite 1 (prova da contenção de flood).
Nota honesta: zonas = snapshot atual do store (não há histórico de zonas); a barra 02:15 usa preços
reais do bar-store. Corre o mesmo processo 2x (env difere) via subprocess p/ flag limpa por módulo."""
import json, subprocess, sys, os
R = "/Users/cristrein/tradingview-mcp/"

INNER = r'''
import os, sys, json
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import context_mtf as cm
import e1_detector as e1

# payload real 15M do store
pb = json.load(open("/Users/cristrein/tradingview-mcp/my-strategy/core/bar_store/store/pine_boxes_15.json"))["data"]

# --- G1: paridade above/below vs lógica antiga verbatim (só relevante flag OFF) ---
if os.environ.get("E1_STACKED_ZONES", "0") != "1":
    last = 4101.2
    new = cm._zones_from_payload(pb, last)
    zs = cm._zs_of(pb)
    above = min((z for z in zs if z["low"] > last), key=lambda z: z["low"], default=None)
    below = max((z for z in zs if z["high"] < last), key=lambda z: z["high"], default=None)
    old = {"n": len(zs), "above": above, "below": below}
    print("G1 paridade above/below:", "PASS" if new == old else f"FALHA new={new} old={old}")
    print("G1 sem chave stack (flag OFF):", "PASS" if "stack" not in new else "FALHA")

# --- G2: recall do topo 27/07 (barra 02:15 real: pclose=4101.21@02:00, close=4100.08@02:15) ---
bars = [json.loads(l) for l in open("/Users/cristrein/tradingview-mcp/my-strategy/core/bar_store/store/bars_15m.jsonl") if l.strip()]
import datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
bmap = {dt.datetime.fromtimestamp(b["t"], LX).strftime("%d/%m %H:%M"): b for b in bars}
b_prev, b_cur = bmap["27/07 02:00"], bmap["27/07 02:15"]
zview = cm._zones_from_payload(pb, b_prev["c"])       # zonas vistas ao preço de entrada da barra

def mk(close, bar_t):
    return {"_meta": {"cycle_ts": 1, "price_ref": close},
            "source_health": {"mtf": {"status": "fresh"}, "micro_15m": {"status": "fresh"}},
            "axes": {"mtf": {
                "240": {"trend": "UP", "svp": {}}, "1D": {"trend": "RANGE"}, "60": {"trend": "RANGE", "svp": {}},
                "15": {"trend": "UP",
                       "leg": {"low": 4065.0, "high": 4116.0, "mag_atr": 3.0, "pos_in_leg": 0.7},
                       "swings": {"last_high": {"price": 4116.0, "bar": 9}, "last_low": {"price": 4088.0, "bar": 5},
                                  "prev_high": {"price": 4110.0, "bar": 3}, "prev_low": {"price": 4080.0, "bar": 1}},
                       "zones": zview, "svp": {}}},
                "micro_15m": {"close": close, "bar_time": bar_t,
                              "ema": {"ema21": 4095.0}, "rsi": "55", "rsi_ma": "50", "dmi": {}},
                "macro": {"risk_level": "normal", "news_gate": {"session": "asia", "high_impact_now": False}},
                "confluence": {"15": {"act_dens": 1.0, "buy_dens": 0.3, "sell": {"dens": 0.5}, "leg_sell": 50}}}}

p = mk(b_prev["c"], b_prev["t"]); d = mk(b_cur["c"], b_cur["t"])
cands = e1.detect(d, p)
zr_short = [c for c in cands if c["rule"] == "zone_reject" and c["direction"] == "SHORT" and c["tf"] == "15"]
flag = os.environ.get("E1_STACKED_ZONES", "0")
tag = "ON " if flag == "1" else "OFF"
if zr_short:
    c = zr_short[0]
    print(f"G2 [{tag}] barra 02:15 (pclose {b_prev['c']} -> close {b_cur['c']}): SHORT zone_reject GERADO "
          f"entry={c['entry']} sl={c['sl']} tgt={c['target']} rr={c['rr']}")
else:
    print(f"G2 [{tag}] barra 02:15: 0 SHORT zone_reject")

# --- G3: contenção anti-spam (só com flag ON e quando gerou) ---
if flag == "1" and zr_short:
    state = {"cooldown": {}, "dedup": {}, "zones": {}}
    admitted = 0
    for c in zr_short + zr_short:      # simula o mesmo candidato re-proposto no mesmo bar/zona
        c2 = dict(c)
        c2["materiality"] = e1.materiality(c2, d, 3.0)
        sup = e1.anti_spam(c2, state, b_cur["t"], conf=c2["materiality"].get("confluence"))
        if sup is None:
            admitted += 1
    print(f"G3 contenção: {admitted} admitido(s) de {2} re-propostas na mesma zona:",
          "PASS" if admitted == 1 else "FALHA")
'''

env_off = dict(os.environ); env_off.pop("E1_STACKED_ZONES", None)
env_on = dict(os.environ); env_on["E1_STACKED_ZONES"] = "1"
print("========== FLAG OFF ==========")
subprocess.run([sys.executable, "-c", INNER], env=env_off, check=True)
print("========== FLAG ON ==========")
subprocess.run([sys.executable, "-c", INNER], env=env_on, check=True)
