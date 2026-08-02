#!/usr/bin/env python3
"""PROVA DE DISCRIMINAÇÃO da afinação 'PERNA NOVA EM FORMAÇÃO' (Cris aprovou 2026-08-02).
Dois reads Opus REAIS sobre dossiês sintéticos controlados, iguais em tudo exceto a sequência:
  A) FACA: perna 1H bear fresca, verde isolado, sem hold, fundo FORA de zona HTF -> esperado: recusa.
  B) VIRAGEM CONFIRMADA: sweep+reclaim+higher-low 3 barras+CHoCH-up 15M+fundo NA demanda 4H+sell-absorvido
     -> esperado: leitura reconhece a perna nova (convicção materialmente maior / possivelmente converge).
Se A continuar recusado E B subir claramente, a nuance discrimina sem abrir a porta às facas.
(Regressão exata dos 23 'não' históricos é impossível: dossiês rotacionados; âncoras+forward completam.)"""
import sys, json
from pathlib import Path
BASE = Path("/Users/cristrein/tradingview-mcp/alert-bridge")
sys.path.insert(0, str(BASE))
import e2_quality as E2


def dossier(seq_confirmada):
    # B v2: entrada no RETEST do higher-low (pos 0.30 da perna nova), não no topo do bounce (o reader
    # recusou o v1 pos 0.85 com razão — "comprar o topo de uma micro-perna madura" era crítica ao fixture)
    leg15 = {"low": 4012.5, "high": 4046.0, "mag_atr": 5.5, "pos_in_leg": 0.30, "dir": "up"} if seq_confirmada \
        else {"low": 4010.0, "high": 4070.0, "mag_atr": 10.0, "pos_in_leg": 0.05, "dir": "down"}
    ch15 = {"up": True, "dn": False} if seq_confirmada else {"up": False, "dn": True}
    zones240 = {"below": {"high": 4010.0, "low": 3996.0, "src": "Custom OB Dete"},
                "above": {"low": 4101.0, "high": 4116.0, "src": "Custom OB Dete"}} if seq_confirmada \
        else {"below": None, "above": {"low": 4101.0, "high": 4116.0, "src": "Custom OB Dete"}}
    conf = ({"tf": "15", "leg_dur_bars": 8, "buy_dens": 0.5, "sell": {"dens": 0.4}, "act_dens": 0.9,
             "leg_sell": 60, "window": {"bars": 4, "buy": {"n": 3, "weight": 4},
                                        "sell": {"n": 1, "weight": 2}, "net_side": "buy"}}
            if seq_confirmada else
            {"tf": "15", "leg_dur_bars": 4, "buy_dens": 0.0, "sell": {"dens": 1.5}, "act_dens": 1.5,
             "leg_sell": 200, "window": {"bars": 4, "buy": {"n": 0, "weight": 0},
                                         "sell": {"n": 4, "weight": 8}, "net_side": "sell"}})
    micro = {"close": 4023.0 if seq_confirmada else 4014.0, "bar_time": 1785500000,
             "ema": {"ema9": 4021.0, "ema21": 4019.0, "ema50": 4030.0} if seq_confirmada
             else {"ema9": 4020.0, "ema21": 4026.0, "ema50": 4040.0},
             "rsi": "47" if seq_confirmada else "28", "rsi_ma": "40" if seq_confirmada else "40",
             "dmi": {"plus_di": "22", "minus_di": "14"} if seq_confirmada else {"plus_di": "8", "minus_di": "34"},
             "candles": {"dominant": "buy" if seq_confirmada else "sell",
                         "up_force_atr": 1.2 if seq_confirmada else 0.2,
                         "dn_force_atr": 0.3 if seq_confirmada else 1.6}}
    # estrutura: no caso B, sweep do low + higher-low confirmado; 1H ainda rotulada DOWN (o LAG em teste)
    sw15 = ({"last_low": {"price": 4012.5, "bar": 300, "confirm_bar": 303},
             "prev_low": {"price": 4008.9, "bar": 292, "confirm_bar": 295},
             "last_high": {"price": 4046.0, "bar": 305}, "prev_high": {"price": 4038.0, "bar": 298}}
            if seq_confirmada else
            {"last_low": {"price": 4012.0, "bar": 300, "confirm_bar": 303},
             "prev_low": {"price": 4030.0, "bar": 292, "confirm_bar": 295},
             "last_high": {"price": 4070.0, "bar": 290}, "prev_high": {"price": 4085.0, "bar": 282}})
    mtf = {"1D": {"trend": "RANGE", "leg": {"low": 3950, "high": 4200, "mag_atr": 5.0, "pos_in_leg": 0.4, "dir": "up"},
                  "choch": {"up": False, "dn": False}, "swings": {}, "zones": None, "svp": {"pressure": None}},
           "240": {"trend": "RANGE", "leg": {"low": 3995, "high": 4116, "mag_atr": 4.5, "pos_in_leg": 0.2, "dir": "down"},
                   "choch": {"up": False, "dn": False}, "swings": {}, "zones": zones240, "svp": {"pressure": "sell"}},
           "60": {"trend": "DOWN", "leg": {"low": 4010, "high": 4090, "mag_atr": 8.0, "pos_in_leg": 0.1, "dir": "down"},
                  "choch": {"up": False, "dn": True}, "swings": {}, "zones": None, "svp": {"pressure": "sell"}},
           "15": {"trend": "UP" if seq_confirmada else "DOWN", "leg": leg15, "choch": ch15, "swings": sw15,
                  "zones": None, "svp": {"pressure": "buy" if seq_confirmada else "sell"}}}
    return {"_meta": {"cycle_ts": 1785500000, "price_ref": micro["close"]},
            "source_health": {"mtf": {"status": "fresh"}, "micro_15m": {"status": "fresh"},
                              "regime": {"status": "fresh"}},
            "axes": {"mtf": mtf, "micro_15m": micro,
                     "macro": {"risk_level": "normal", "bias": "bear",
                               "news_gate": {"session": "ny", "high_impact_now": False, "ff_event_le_min": None},
                               "real_yield_10y": 2.4, "usd_broad": 120.7, "vix": 18.5},
                     "regime": {"v5_4h": {"regime": "BEAR", "status": "fresh"},
                                "structural_1d": {"regime": "BEAR", "status": "fresh"}},
                     "confluence": {"15": conf}, "magnets": {"above": [], "below": []}}}


def main():
    cand = {"direction": "LONG", "rule": "sweep_reclaim", "tf": "15", "entry": 4023.0, "sl": 4011.0,
            "target": 4059.0, "rr": 3.0,
            "materiality": {"sl_atr": 2.2, "confluence": 3, "confluence_breakdown": {}}}
    cand_a = dict(cand, entry=4014.0, sl=4000.0, target=4056.0)
    for lab, d, c in (("A FACA (verde isolado, sem sequência, sem zona HTF)", dossier(False), cand_a),
                      ("B VIRAGEM (sweep+reclaim+HL 3 barras+CHoCH-up 15M+demanda 4H+sell-absorvido)", dossier(True), cand)):
        th = E2.run_read(c, d)
        if th.get("error"):
            print(f"{lab}: ERRO {th['error']}")
            continue
        surf = E2.surfaced(th, c)
        print(f"\n=== {lab} ===")
        print(f"surfaced={surf} | converges={th.get('converges')} | convergência={th.get('convergence')} "
              f"| convicção={th.get('conviction')} | contexto={th.get('context_direction')}")
        print(f"tese: {str(th.get('thesis'))[:260]}")


if __name__ == "__main__":
    main()
