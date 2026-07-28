#!/usr/bin/env python3
"""VIGIA DE ALERTA (pedido Cris 2026-07-28 00:5x): demanda A=4044-4056 (OB 15M+1H+4H) e B=4022-4043
mais abaixo. Monitorar REJEIÇÃO + RECLAIM ALTISTA quando o preço lá chegar — se segurar = long
interessante. Poll 45s do bar-store (5M p/ toque intrabar rápido; 15M p/ fechos/reclaim + EMA21 do
dossiê E0). Eventos discretos, cada um 1× (re-arma se o preço sair da zona e voltar). Read-only."""
import json, time, os, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
R = "/Users/cristrein/tradingview-mcp/"
ZA = (4044.0, 4056.0)      # demanda A (OB 15M+1H+4H) — níveis do Cris
ZB = (4022.0, 4043.0)      # demanda B (mais abaixo)
hm = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%H:%M")

def bars(name, n=8):
    p = R + f"my-strategy/core/bar_store/store/bars_{name}.jsonl"
    with open(p, "rb") as f:
        f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 6000))
        rows = [json.loads(l) for l in f.read().decode(errors="ignore").splitlines()[1:] if l.strip()]
    return rows[-n:]

def ema21_15m():
    try:
        d = json.load(open(R + "external_factors_v2/snapshots/market_context.json"))
        return (d["axes"]["micro_15m"].get("ema") or {}).get("ema21")
    except Exception:
        return None

state = {"touchA": False, "rejA": False, "reclA": False, "touchB": False, "rejB": False, "lostA": False, "lostB": False}
print(f"vigia armado: zona A {ZA[0]}-{ZA[1]} · zona B {ZB[0]}-{ZB[1]} (toque->rejeição->reclaim)")
while True:
    try:
        b5 = bars("5m", 4); b15 = bars("15m", 6)
        if not b5 or not b15:
            time.sleep(45); continue
        last5 = b5[-1]; c15 = b15[-1]; p15 = b15[-2] if len(b15) >= 2 else None
        px = last5["c"]
        # --- ZONA A 4044-4056 ---
        in_a = last5["l"] <= ZA[1]
        if in_a and not state["touchA"]:
            state["touchA"] = True
            print(f"TOQUE ZONA A: preço tocou a demanda 4044-4056 (low {last5['l']} @ {hm(last5['t'])}, close {px}) — a monitorar rejeição")
        if state["touchA"] and not state["rejA"] and c15["l"] <= ZA[1] and c15["c"] > ZA[1]:
            state["rejA"] = True
            print(f"REJEIÇÃO 15M NA ZONA A: wick {c15['l']} dentro da demanda e FECHO {c15['c']} de volta acima de {ZA[1]} @ {hm(c15['t'])} — falta o reclaim")
        if state["rejA"] and not state["reclA"] and p15 is not None:
            e21 = ema21_15m()
            if c15["c"] > p15["h"] and c15["c"] > c15["o"] and (e21 is None or c15["c"] > e21):
                state["reclA"] = True
                print(f"RECLAIM ALTISTA CONFIRMADO (zona A): fecho 15M {c15['c']} > high anterior {p15['h']}" + (f" e > EMA21 {round(e21,2)}" if e21 else "") + f" @ {hm(c15['t'])} — setup LONG do Cris ativo; conferir chart")
        if state["touchA"] and not state["lostA"] and c15["c"] < ZA[0]:
            state["lostA"] = True; state["rejA"] = False; state["reclA"] = False
            print(f"ZONA A PERDIDA: fecho 15M {c15['c']} abaixo de {ZA[0]} @ {hm(c15['t'])} — atenção à zona B 4022-4043")
        # --- ZONA B 4022-4043 ---
        in_b = last5["l"] <= ZB[1]
        if in_b and not state["touchB"]:
            state["touchB"] = True
            print(f"TOQUE ZONA B: preço tocou 4022-4043 (low {last5['l']} @ {hm(last5['t'])}) — última demanda antes do vazio")
        if state["touchB"] and not state["rejB"] and c15["l"] <= ZB[1] and c15["c"] > ZB[1]:
            state["rejB"] = True
            print(f"REJEIÇÃO 15M NA ZONA B: wick {c15['l']} e fecho {c15['c']} acima de {ZB[1]} @ {hm(c15['t'])}")
        if state["touchB"] and not state["lostB"] and c15["c"] < ZB[0]:
            state["lostB"] = True
            print(f"ZONA B PERDIDA: fecho 15M {c15['c']} abaixo de {ZB[0]} @ {hm(c15['t'])} — zonas do Cris quebradas; cenário long invalidado")
        # re-arme: preço bem acima da zona A outra vez
        if state["touchA"] and px > ZA[1] + 6 and not state["reclA"]:
            state["touchA"] = False; state["rejA"] = False
    except Exception as e:
        print(f"vigia erro transitório: {type(e).__name__}")
    time.sleep(45)
