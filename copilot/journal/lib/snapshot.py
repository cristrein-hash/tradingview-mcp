#!/usr/bin/env python3
"""COPILOT/JOURNAL — snapshot ZERO-CDP do contexto no instante da trade (P0). Dossiê E0 (axes) + TODOS os
study_values (15/60/240/1D) + pine_boxes + preço + frescura. Lê SÓ ficheiros (bar-store/E0), sem MCP —
mesma disciplina do E0/Cp. Cris quer TODOS os indicadores capturados, não só a estrutura."""
import json, sys, time
from pathlib import Path
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "alert-bridge"))
MKT = REPO / "external_factors_v2/snapshots/market_context.json"
EXT = REPO / "external_factors_v2/snapshots/latest.json"     # dossiê externo (fed path, eventos, ouro, news, teorias)


def _unpack(v):
    """store_reader devolve (data, age_s) nalgumas funções; tolera ambos os formatos."""
    if isinstance(v, tuple) and len(v) == 2:
        return v[0], v[1]
    return v, None


def build_snapshot():
    import store_reader as SR
    snap = {"built_epoch": int(time.time())}
    try:
        snap["context"] = json.loads(MKT.read_text()).get("axes", {})
    except Exception as e:
        snap["context_error"] = str(e)[:80]
    ind = {}
    for tf in ("15", "60", "240", "1D"):
        try:
            sv, age = _unpack(SR.study_values(tf))
            pb, _ = _unpack(SR.pine_boxes(tf))
            ind[tf] = {"study_values": sv, "pine_boxes": pb, "age_s": age}
        except Exception as e:
            ind[tf] = {"error": str(e)[:60]}
    snap["indicators"] = ind
    try:
        b = SR.bars("15")
        snap["price_at_detection"] = b[-1]["c"] if b else None
        snap["store_fresh"] = {tf: bool(SR.fresh(tf)) for tf in ("15", "60", "240", "1D")}
    except Exception as e:
        snap["price_error"] = str(e)[:60]
    # contexto EXTERNO completo (Cris: quanto mais informação para contextualizar, melhor)
    try:
        ext = json.loads(EXT.read_text())
        snap["external"] = ext
        snap["external_age_s"] = int(time.time()) - (ext.get("_meta", {}).get("cycle_ts") or ext.get("_meta", {}).get("ts_epoch") or 0)
    except Exception as e:
        snap["external_error"] = str(e)[:80]
    return snap


if __name__ == "__main__":
    s = build_snapshot()
    print(f"snapshot: {len(json.dumps(s))} bytes | price {s.get('price_at_detection')} | "
          f"axes {list((s.get('context') or {}).keys())} | fresh {s.get('store_fresh')}")
    for tf, d in (s.get("indicators") or {}).items():
        sv = d.get("study_values")
        n = len((sv or {}).get("studies", [])) if isinstance(sv, dict) else "?"
        print(f"  {tf}: studies={n} age_s={round(d.get('age_s') or 0, 1)}")
