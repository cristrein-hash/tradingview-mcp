#!/usr/bin/env python3
"""ACEITAÇÃO — MAPA DO TRADER + VELA-NO-NÍVEL (Cris aprovou o desenho 2026-08-04; dia 04/08 = teste).
Modos:
  --golden : captura o render_composite SEM mapa (fixture determinística) p/ regressão byte-exata (d).
  --full   : corre a aceitação completa:
     (a) a vela 15M das 09:00 (t=1785830400, o 4065.36 h 4073.04 l 4064.72 c 4068.28) DISPARA o vela-no-nível
         SHORT na zona declarada 4066-4073 (entry 4068.28, SL >= 4073.9, alvos incluem ~4042/4028);
     (b) o LONG surfado das 08:03 (entry 4063.36) recebe o prefixo de CONFLITO (trader_map.conflict);
     (c) disciplina de location: barras 02:00 (close 4046.68) e 09:30 (h 4064.57) NÃO disparam;
     (d) regressão: render_composite SEM mapa == golden pré-mudança (byte-exato).
"""
import sys, json
from pathlib import Path

R = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(R / "alert-bridge"))
GOLDEN = Path("/tmp/golden_render_pre_map.txt")


def fixture_dossier():
    return {"_meta": {"cycle_ts": 1, "price_ref": 4060.0},
            "source_health": {"mtf": {"status": "fresh"}, "micro_15m": {"status": "fresh"}},
            "axes": {"mtf": {"15": {"trend": "RANGE", "leg": {"low": 4040, "high": 4070, "mag_atr": 5.0,
                     "pos_in_leg": 0.5, "dir": "up"}, "choch": {"up": False, "dn": False}, "swings": {},
                     "zones": None, "svp": {"pressure": None}}},
                     "micro_15m": {"close": 4060.0, "bar_time": 1000, "ema": {}, "rsi": "50", "rsi_ma": "50",
                                   "dmi": {}, "candles": {}},
                     "macro": {"risk_level": "normal", "news_gate": {"session": "ny", "high_impact_now": False}},
                     "regime": {}, "confluence": {"15": {}}, "magnets": {}}}


def fixture_cand():
    return {"direction": "SHORT", "rule": "zone_reject", "tf": "15", "entry": 4060.0, "sl": 4070.0,
            "target": 4030.0, "rr": 3.0, "src": "x", "materiality": {"sl_atr": 2.0, "confluence": 1,
            "confluence_breakdown": {}}}


def _render_no_map():
    import trader_map
    import e2_quality as E2
    orig = trader_map.MAP_F
    trader_map.MAP_F = R / "alert-bridge" / ".no_such_map.json"      # sem mapa
    try:
        return E2.render_composite(fixture_dossier(), fixture_cand())
    finally:
        trader_map.MAP_F = orig


def golden():
    import e2_quality as E2
    txt = E2.render_composite(fixture_dossier(), fixture_cand())
    GOLDEN.write_text(txt)
    print(f"golden capturado: {len(txt)} chars -> {GOLDEN}")


def full():
    import trader_map
    import vela_no_nivel as VN
    import e2_quality as E2

    tmap = trader_map.load_map()
    assert tmap and any(z["id"] == "supply_4066_4073_w32" for z in tmap["zones"]), "mapa inicial ausente"
    zone = next(z for z in tmap["zones"] if z["id"] == "supply_4066_4073_w32")

    # (a) vela das 09:00 dispara
    bar_0900 = {"t": 1785830400, "o": 4065.36, "h": 4073.04, "l": 4064.72, "c": 4068.28}
    r = VN.decide(bar_0900, zone, atr15=5.77)
    ok_a = bool(r) and r["direction"] == "SHORT" and abs(r["entry"] - 4068.28) < 0.01 and r["sl"] >= 4073.9
    print(f"(a) vela 09:00 dispara SHORT entry 4068.28 SL>=4073.9: {'PASS' if ok_a else 'FALHA'} -> {r}")

    # (b) prefixo de conflito no LONG 08:03
    c = trader_map.conflict({"direction": "LONG", "entry": 4063.36}, tmap, atr=5.77)
    ok_b = c is not None and c["id"] == "supply_4066_4073_w32"
    print(f"(b) LONG 08:03 marca CONFLITO com a zona declarada: {'PASS' if ok_b else 'FALHA'}")

    # (c) disciplina de location: 02:00 e 09:30 NÃO disparam
    bar_0200 = {"t": 1785805200, "o": 4049.5, "h": 4051.9, "l": 4044.8, "c": 4046.68}
    bar_0930 = {"t": 1785832200, "o": 4063.6, "h": 4064.57, "l": 4058.4, "c": 4059.31}
    ok_c = VN.decide(bar_0200, zone, atr15=5.77) is None and VN.decide(bar_0930, zone, atr15=5.77) is None
    print(f"(c) 02:00 e 09:30 NAO disparam (sem toque na zona): {'PASS' if ok_c else 'FALHA'}")

    # (d) regressão byte-exata sem mapa
    assert GOLDEN.exists(), "golden ausente — corre --golden ANTES do edit do e2"
    ok_d = _render_no_map() == GOLDEN.read_text()
    print(f"(d) render SEM mapa == golden pré-mudança: {'PASS' if ok_d else 'FALHA'}")

    # bónus: render COM mapa contém a secção
    ok_e = "# MAPA DO TRADER" in E2.render_composite(fixture_dossier(), fixture_cand())
    print(f"(+) render COM mapa contém secção MAPA DO TRADER: {'PASS' if ok_e else 'FALHA'}")

    allok = ok_a and ok_b and ok_c and ok_d and ok_e
    print(f"\nACEITAÇÃO MAPA+VELA: {'PASS' if allok else 'FALHA'}")
    return 0 if allok else 1


if __name__ == "__main__":
    if "--golden" in sys.argv:
        golden()
    elif "--full" in sys.argv:
        sys.exit(full())
    else:
        print("uso: --golden (antes do edit) | --full (após implementação)")
