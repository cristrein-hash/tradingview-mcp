#!/usr/bin/env python3
"""4 SONDAS de discriminação dos blocos novos do READ_SYS (FADE EM SUPPLY COM SEQUÊNCIA + CONTINUAÇÃO EM
COMPRESSÃO), reads Opus REAIS sobre dossiês sintéticos controlados:
 P1 NO-FIRE: faca contra-perna sem sweep, 1 rejeição, buy vivo, rótulo+dados de acordo BULL -> recusar.
 P2 FIRE: arquétipo 27/07 — rótulo BULL vs dados 1H DOWN + sweep topo + 2 rejeições na supply 4H + LH hold.
 P3 FIRE: arquétipo 03/08 — com-perna, compressão nas EMAs, ADX morto, zero agressão dos dois lados, sem evento.
 P4 NO-FIRE (guarda): igual a P3 mas com AGRESSÃO COMPRADORA ativa -> recusar.
PASS: P1+P4 recusados E P2+P3 materialmente melhores (convicção ↑ e/ou surfaced). FAIL => git revert."""
import sys
from pathlib import Path
BASE = Path("/Users/cristrein/tradingview-mcp/alert-bridge")
sys.path.insert(0, str(BASE))
import e2_quality as E2


def base_dossier():
    return {"_meta": {"cycle_ts": 1785600000, "price_ref": 4060.0},
            "source_health": {"mtf": {"status": "fresh"}, "micro_15m": {"status": "fresh"},
                              "regime": {"status": "fresh"}},
            "axes": {"mtf": {}, "micro_15m": {}, "macro": {"risk_level": "normal", "bias": "bear",
                     "news_gate": {"session": "london_strong", "high_impact_now": False, "ff_event_le_min": None},
                     "real_yield_10y": 2.4, "usd_broad": 120.5, "vix": 18.0},
                     "regime": {"v5_4h": {"regime": "BEAR", "status": "fresh"},
                                "structural_1d": {"regime": "BEAR", "status": "fresh"}},
                     "confluence": {"15": {}}, "magnets": {"above": [], "below": []}}}


def mtf_common(d):
    d["axes"]["mtf"]["1D"] = {"trend": "RANGE", "leg": {"low": 3950, "high": 4200, "mag_atr": 5.0,
                              "pos_in_leg": 0.45, "dir": "up"}, "choch": {"up": False, "dn": False},
                              "swings": {}, "zones": None, "svp": {"pressure": None}}
    return d


def p1():  # faca: contra-perna, sem sweep, 1 rejeição, buy vivo, rótulo+dados BULL de acordo
    d = mtf_common(base_dossier())
    d["axes"]["mtf"]["240"] = {"trend": "UP", "leg": {"low": 3995, "high": 4090, "mag_atr": 4.0, "pos_in_leg": 0.75, "dir": "up"},
                               "choch": {"up": True, "dn": False}, "swings": {},
                               "zones": {"above": {"low": 4085.0, "high": 4100.0, "src": "Custom OB Dete"}, "below": None},
                               "svp": {"pressure": "buy"}}
    d["axes"]["mtf"]["60"] = {"trend": "UP", "leg": {"low": 4020, "high": 4075, "mag_atr": 6.0, "pos_in_leg": 0.8, "dir": "up"},
                              "choch": {"up": True, "dn": False}, "swings": {}, "zones": None, "svp": {"pressure": "buy"}}
    d["axes"]["mtf"]["15"] = {"trend": "UP", "leg": {"low": 4040, "high": 4072, "mag_atr": 5.0, "pos_in_leg": 0.8, "dir": "up"},
                              "choch": {"up": False, "dn": False}, "swings": {}, "zones": None, "svp": {"pressure": "buy"}}
    d["axes"]["micro_15m"] = {"close": 4068.0, "bar_time": 1785600000,
                              "ema": {"ema9": 4064.0, "ema21": 4060.0, "ema50": 4052.0},
                              "rsi": "63", "rsi_ma": "55", "dmi": {"plus_di": "30", "minus_di": "12"},
                              "candles": {"dominant": "buy", "up_force_atr": 1.4, "dn_force_atr": 0.3}}
    d["axes"]["confluence"]["15"] = {"tf": "15", "leg_dur_bars": 10, "buy_dens": 0.6, "sell": {"dens": 0.1},
                                     "act_dens": 0.9, "leg_sell": 20,
                                     "window": {"bars": 4, "buy": {"n": 3, "weight": 5}, "sell": {"n": 0, "weight": 0}, "net_side": "buy"}}
    cand = {"direction": "SHORT", "rule": "zone_reject", "tf": "60", "entry": 4068.0, "sl": 4079.0,
            "target": 4035.0, "rr": 3.0, "materiality": {"sl_atr": 2.2, "confluence": 2, "confluence_breakdown": {}}}
    return "P1 NO-FIRE faca (sem sweep, buy vivo, rótulo=dados BULL)", d, cand


def p2():  # arquétipo 27/07: rótulo BULL mas dados 1H DOWN + sweep topo + 2 rejeições supply 4H + LH hold
    d = mtf_common(base_dossier())
    d["axes"]["mtf"]["240"] = {"trend": "RANGE", "leg": {"low": 3995, "high": 4116, "mag_atr": 4.5, "pos_in_leg": 0.85, "dir": "up"},
                               "choch": {"up": False, "dn": False}, "swings": {},
                               "zones": {"above": {"low": 4101.0, "high": 4116.0, "src": "Custom OB Dete"},
                                         "below": {"high": 4010.0, "low": 3996.0, "src": "Custom OB Dete"}},
                               "svp": {"pressure": "sell"}}
    # 1H: rótulo/frame diz BULL (leg dir up) MAS trend DOWN — a tensão de rótulo
    d["axes"]["mtf"]["60"] = {"trend": "DOWN", "leg": {"low": 4082, "high": 4112, "mag_atr": 4.0, "pos_in_leg": 0.25, "dir": "up"},
                              "choch": {"up": False, "dn": False},
                              "swings": {"last_high": {"price": 4104.0, "bar": 50}, "prev_high": {"price": 4112.0, "bar": 44},
                                         "last_low": {"price": 4085.0, "bar": 48}, "prev_low": {"price": 4082.0, "bar": 40}},
                              "zones": None, "svp": {"pressure": "sell"}}
    # 15M: sweep do topo (h 4116 varreu 4112) + 2 rejeições na supply + lower-high a segurar
    d["axes"]["mtf"]["15"] = {"trend": "DOWN", "leg": {"low": 4085, "high": 4116, "mag_atr": 5.0, "pos_in_leg": 0.15, "dir": "down"},
                              "choch": {"up": False, "dn": True},
                              "swings": {"last_high": {"price": 4104.0, "bar": 300}, "prev_high": {"price": 4116.0, "bar": 292},
                                         "last_low": {"price": 4087.0, "bar": 298}, "prev_low": {"price": 4092.0, "bar": 290}},
                              "zones": None, "svp": {"pressure": "sell"}}
    d["axes"]["micro_15m"] = {"close": 4087.5, "bar_time": 1785600000,
                              "ema": {"ema9": 4092.0, "ema21": 4096.0, "ema50": 4098.0},
                              "rsi": "38", "rsi_ma": "46", "dmi": {"plus_di": "12", "minus_di": "28"},
                              "candles": {"dominant": "sell", "up_force_atr": 0.3, "dn_force_atr": 1.3}}
    d["axes"]["confluence"]["15"] = {"tf": "15", "leg_dur_bars": 8, "buy_dens": 0.1, "sell": {"dens": 0.6},
                                     "act_dens": 0.8, "leg_sell": 90,
                                     "window": {"bars": 4, "buy": {"n": 1, "weight": 1}, "sell": {"n": 2, "weight": 4}, "net_side": "sell"}}
    cand = {"direction": "SHORT", "rule": "sweep_reclaim", "tf": "60", "entry": 4087.5, "sl": 4105.0,
            "target": 4035.0, "rr": 3.0, "materiality": {"sl_atr": 2.3, "confluence": 3, "confluence_breakdown": {}}}
    return "P2 FIRE fade c/ sequência (rótulo BULL vs dados DOWN + sweep + 2 rejeições)", d, cand


def p3(buy_aggr=False):  # arquétipo 03/08: com-perna, compressão EMAs, ADX morto, zero agressão
    d = mtf_common(base_dossier())
    d["axes"]["mtf"]["240"] = {"trend": "RANGE", "leg": {"low": 4020, "high": 4120, "mag_atr": 4.0, "pos_in_leg": 0.45, "dir": "down"},
                               "choch": {"up": False, "dn": False}, "swings": {},
                               "zones": {"above": {"low": 4101.0, "high": 4116.0, "src": "Custom OB Dete"},
                                         "below": {"high": 4010.0, "low": 3996.0, "src": "Custom OB Dete"}},
                               "svp": {"pressure": "sell"}}
    d["axes"]["mtf"]["60"] = {"trend": "RANGE", "leg": {"low": 4047, "high": 4079, "mag_atr": 4.5, "pos_in_leg": 0.4, "dir": "down"},
                              "choch": {"up": False, "dn": True}, "swings": {}, "zones": {"above": {"low": 4062.0, "high": 4072.0, "src": "Custom OB Dete"}, "below": None},
                              "svp": {"pressure": "sell"}}
    d["axes"]["mtf"]["15"] = {"trend": "DOWN", "leg": {"low": 4047, "high": 4072, "mag_atr": 4.0, "pos_in_leg": 0.55, "dir": "down"},
                              "choch": {"up": False, "dn": True}, "swings": {}, "zones": None, "svp": {"pressure": "sell"}}
    d["axes"]["micro_15m"] = {"close": 4060.5, "bar_time": 1785600000,
                              "ema": {"ema9": 4061.0, "ema21": 4062.0, "ema50": 4063.0},
                              "rsi": "47", "rsi_ma": "49", "dmi": {"plus_di": "11", "minus_di": "15"},
                              "adx": "13", "candles": {"dominant": "none", "up_force_atr": 0.3, "dn_force_atr": 0.4}}
    if buy_aggr:
        d["axes"]["confluence"]["15"] = {"tf": "15", "leg_dur_bars": 8, "buy_dens": 0.6, "sell": {"dens": 0.0},
                                         "act_dens": 0.7, "leg_sell": 0,
                                         "window": {"bars": 4, "buy": {"n": 3, "weight": 5}, "sell": {"n": 0, "weight": 0}, "net_side": "buy"}}
    else:
        d["axes"]["confluence"]["15"] = {"tf": "15", "leg_dur_bars": 8, "buy_dens": 0.0, "sell": {"dens": 0.0},
                                         "act_dens": 0.1, "leg_sell": 0,
                                         "window": {"bars": 4, "buy": {"n": 0, "weight": 0}, "sell": {"n": 0, "weight": 0}, "net_side": "none"}}
    cand = {"direction": "SHORT", "rule": "zone_reject", "tf": "60", "entry": 4060.5, "sl": 4073.0,
            "target": 4023.0, "rr": 3.0, "materiality": {"sl_atr": 2.5, "confluence": 2, "confluence_breakdown": {}}}
    lab = "P4 NO-FIRE guarda (compressão MAS agressão compradora ativa)" if buy_aggr \
        else "P3 FIRE continuação em compressão (ADX morto, zero agressão)"
    return lab, d, cand


def main():
    results = {}
    for lab, d, c in (p1(), p2(), p3(False), p3(True)):
        th = E2.run_read(c, d)
        if th.get("error"):
            print(f"{lab}: ERRO {th['error']}"); continue
        surf = E2.surfaced(th, c)
        results[lab[:2]] = (surf, th.get("conviction"))
        print(f"\n=== {lab} ===")
        print(f"surfaced={surf} | converges={th.get('converges')} | convergência={th.get('convergence')} "
              f"| convicção={th.get('conviction')} | contexto={th.get('context_direction')}")
        print(f"tese: {str(th.get('thesis'))[:240]}")
    p1r = results.get("P1", (True, 99)); p2r = results.get("P2", (False, 0))
    p3r = results.get("P3", (False, 0)); p4r = results.get("P4", (True, 99))
    ok = (not p1r[0]) and (not p4r[0]) and (p2r[0] or (p2r[1] or 0) >= 45) and (p3r[0] or (p3r[1] or 0) >= 45)
    print(f"\nVEREDITO SONDAS: {'PASS' if ok else 'FAIL'} (P1 ref={not p1r[0]}, P4 ref={not p4r[0]}, "
          f"P2 conv={p2r[1]} surf={p2r[0]}, P3 conv={p3r[1]} surf={p3r[0]})")


if __name__ == "__main__":
    main()
