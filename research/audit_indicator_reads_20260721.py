#!/usr/bin/env python3
"""AUDITORIA DE PROFUNDIDADE (Cris 2026-07-21): mapear, por ESTUDO no chart 15M, TUDO o que cada tool MCP
devolve (boxes/labels/lines/tables/shapes/study_values) vs o que o store/reader captura — para expor as
dimensoes que ando a STRIPAR (cor e texto do OB Detector, etc.). READ-ONLY, 1 sessao MCP. Nao conclui — dumpa
a estrutura crua de cada tool para eu mapear os blind-spots com rigor."""
import os, sys, json
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/my-strategy/core")
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import tab_pin
from draw_xau_4h_trades import MCPClient

tid = tab_pin.discover_tab("15", symbol_suffix="XAUUSD")
os.environ["TVMCP_TARGET_CHART_ID"] = tid
c = MCPClient(); c.start()


def dump(tool, args=None):
    try:
        return c.call_tool(tool, args or {}) or {}
    except Exception as e:
        return {"_err": str(e)[:80]}


def studies_of(r, item_key):
    """Devolve {study_name: (n_items, sample_item_keys, sample_item)} para um tool de estudos."""
    out = {}
    for s in (r.get("studies") or []):
        items = s.get(item_key) or []
        if isinstance(items, dict):
            items = [items]
        sample = items[0] if items else None
        keys = list(sample.keys()) if isinstance(sample, dict) else type(sample).__name__
        out[(s.get("name") or "?")[:30]] = (len(items) if isinstance(items, list) else "?", keys, sample)
    return out


try:
    print("=== TOOLS DISPONIVEIS (o que existe para ler) ===")
    print("  (fixos: data_get_pine_boxes/labels/lines/tables/shapes, data_get_study_values)")
    print("\n=== BOXES verbose (all_boxes: high/low/TIPO/cor) — o campo certo p/ supply-demand ===")
    vb = dump("data_get_pine_boxes", {"verbose": True})
    for s in (vb.get("studies") or []):
        nm = (s.get("name") or "?")[:30]
        ab = s.get("all_boxes") or []
        types = sorted({(b.get("text") or "—") for b in ab})
        keys = list(ab[0].keys()) if ab else "vazio"
        print(f"  [{nm}] {len(ab)} boxes · campos={keys} · TIPOS(text)={types}")
    print("\n=== LABELS (data_get_pine_labels) — que estudos dao texto, que texto ===")
    for nm, (n, keys, samp) in studies_of(dump("data_get_pine_labels", {"max_labels": 40}), "labels").items():
        txt = samp.get("text") if isinstance(samp, dict) else None
        print(f"  [{nm}] {n} labels · campos={keys} · sample_text={txt!r}")
    print("\n=== LINES (data_get_pine_lines) ===")
    for nm, (n, keys, samp) in studies_of(dump("data_get_pine_lines"), "lines").items():
        print(f"  [{nm}] {n} lines · campos={keys}")
    print("\n=== TABLES (data_get_pine_tables) ===")
    for nm, (n, keys, samp) in studies_of(dump("data_get_pine_tables"), "tables").items():
        print(f"  [{nm}] {n} tables · sample={json.dumps(samp, ensure_ascii=False)[:120]}")
    print("\n=== SHAPES (data_get_pine_shapes) ===")
    for nm, (n, keys, samp) in studies_of(dump("data_get_pine_shapes", {"max_bars": 100}), "activations").items():
        print(f"  [{nm}] {n} activations · campos={keys}")
    print("\n=== STUDY_VALUES — todos os campos por estudo ===")
    sv = dump("data_get_study_values")
    for s in (sv.get("studies") or []):
        print(f"  [{(s.get('name') or '?')[:30]}] valores={list((s.get('values') or {}).keys())}")
finally:
    c.stop()
