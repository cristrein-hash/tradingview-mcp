#!/usr/bin/env python3
"""Reader MACRO (P3/E0) — eixo macro/news do dossiê, SÓ leitura dos snapshots EF já produzidos
(external_factors_v2/snapshots/latest.json) + news_gate.read_gate(). 0 tokens, não toca CDP/chart.
Espelha source_health do EF. py3.9. Uso: python3 context_macro.py
"""
import sys, json
from pathlib import Path
BASE = Path(__file__).resolve().parent
REPO = BASE.parent
sys.path.insert(0, str(BASE))
LATEST = REPO / "external_factors_v2" / "snapshots" / "latest.json"


def read_macro():
    try:
        d = json.loads(LATEST.read_text())
    except Exception as e:
        return {"error": f"latest.json ilegivel: {type(e).__name__}", "source_health": "absent"}
    ef = d.get("external_factors", {})
    imm = d.get("layer_A_imminent_le96h", []) or []
    macro = {
        "real_yield_10y": ef.get("external_us10y_real"),
        "usd_broad": ef.get("external_usd_broad"),
        "vix": ef.get("external_vix"),
        "risk_level": ef.get("external_risk_level"),
        "bias": ef.get("external_bias"),
        "main_reasons": ef.get("external_main_reasons", [])[:3],
        # FIX 26/08 (Cris): hours_until do snapshot DECAI (era o valor da hora da coleta — deu "25min"
        # com o print a 14min). Recomputa do release_ts na LEITURA, como o collector já recomendava.
        "imminent_events": [{"event": e.get("event"),
                             "hours_until": (round((e["release_ts"] - _time.time()) / 3600, 1)
                                             if e.get("release_ts") else e.get("hours_until")),
                             "impact": e.get("impact")} for e in imm[:5]],
        "news_live": d.get("news_live"),
        "ef_cycle": d.get("_meta", {}).get("cycle_dt"),
        "ef_stale_series": d.get("stale_series", []),
    }
    try:
        from news_gate import read_gate
        g = read_gate()
        macro["news_gate"] = {"session": g.get("session"), "high_impact_now": g.get("high_impact_now"),
                              "ff_event_le_min": g.get("ff_event_le_min"), "stale": g.get("stale"),
                              "advisory": g.get("advisory")}
    except Exception as e:
        macro["news_gate"] = {"error": f"{type(e).__name__}"}
    return macro


if __name__ == "__main__":
    print(json.dumps(read_macro(), indent=1, ensure_ascii=False))
