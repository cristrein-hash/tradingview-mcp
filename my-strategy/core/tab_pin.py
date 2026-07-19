#!/usr/bin/env python3
"""tab_pin — RECURSO GERAL de coexistência MCP/CDP por TAB DEDICADA (decisão Cris 2026-07-17).

Cada tab do TradingView é um target CDP próprio; `TVMCP_TARGET_CHART_ID` pina o server.js a uma tab.
Setup operacional: 5 tabs XAUUSD (5M/15M/1H/4H/1D), cada uma com os indicadores habilitados.
Runtimes de estratégia (L1, L2, futuras 15M) LEEM a tab do seu TF diretamente — sem trocar
symbol/timeframe, sem restore, sem pausar os daemons E0/E1/E2 (que já leem por tab).

API:
  discover_tab(want_res, symbol_suffix="XAUUSD") -> target_id | None
    Verifica primeiro o cache (.tab_map.json ao lado deste ficheiro); em miss/stale re-enumera
    todas as tabs de chart e reconstrói o mapa {resolution: target_id}. Fail-closed: None se
    a tab do TF pedido não existir (caller decide fallback/HARD_STOP).
  env_pinned(target_id) -> dict — cópia de os.environ com TVMCP_TARGET_CHART_ID setado (p/ subprocess).

py3.9, stdlib. Tab IDs mudam quando o TradingView reinicia — daí verificação antes de usar.
"""
import os, json, urllib.request
from pathlib import Path

CDP_LIST = "http://localhost:9222/json/list"
CACHE = Path(__file__).resolve().parent / ".tab_map.json"


def _mcp():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from tv_read_adapter import _MCP
    c = _MCP(); c.start(); return c


def _chart_targets():
    try:
        with urllib.request.urlopen(CDP_LIST, timeout=8) as r:
            targets = json.loads(r.read())
    except Exception:
        return []
    return [t["id"] for t in targets if t.get("type") == "page"
            and "tradingview.com/chart" in (t.get("url") or "").lower()]


def _state_of(tid):
    """(symbol, resolution) da tab tid, ou (None, None) em falha. Read-only."""
    saved = os.environ.get("TVMCP_TARGET_CHART_ID")
    os.environ["TVMCP_TARGET_CHART_ID"] = tid
    c = None
    try:
        c = _mcp()
        st = c.call("chart_get_state")
        if not isinstance(st, dict) or st.get("_error"):
            return None, None
        return st.get("symbol"), str(st.get("resolution"))
    except Exception:
        return None, None
    finally:
        try:
            if c: c.stop()
        except Exception:
            pass
        if saved is None:
            os.environ.pop("TVMCP_TARGET_CHART_ID", None)
        else:
            os.environ["TVMCP_TARGET_CHART_ID"] = saved


def _load_cache():
    try:
        return json.loads(CACHE.read_text())
    except Exception:
        return {}


def _save_cache(m):
    try:
        tmp = CACHE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(m))
        os.replace(tmp, CACHE)
    except Exception:
        pass


def discover_tab(want_res, symbol_suffix="XAUUSD"):
    """Target-id da tab cujo chart está em want_res (e símbolo bate). None se não existir (fail-closed).
    Cache indexado por (symbol_suffix, resolução) — múltiplos símbolos na mesma resolução (ex. XAU 1D +
    DXY 1D) coexistem sem thrash. Cada símbolo mantém o seu sub-mapa; rediscovery só reescreve o seu."""
    want_res = str(want_res)
    cache = _load_cache()
    sub = cache.get(symbol_suffix) if isinstance(cache.get(symbol_suffix), dict) else {}
    # 1) cache: verifica só a tab necessária (2-3s) antes de re-enumerar tudo
    cached = sub.get(want_res)
    if cached:
        sym, res = _state_of(cached)
        if res == want_res and sym and str(sym).endswith(symbol_suffix):
            return cached
    # 2) rediscovery completa (só tabs deste símbolo)
    m = {}
    for tid in _chart_targets():
        sym, res = _state_of(tid)
        if res and sym and str(sym).endswith(symbol_suffix) and res not in m:
            m[res] = tid
    if m:
        cache[symbol_suffix] = m          # preserva sub-mapas de outros símbolos
        _save_cache(cache)
    return m.get(want_res)


def env_pinned(target_id):
    """Cópia do ambiente com o pin setado — para passar a subprocess.run(env=...)."""
    e = dict(os.environ)
    e["TVMCP_TARGET_CHART_ID"] = target_id
    return e


if __name__ == "__main__":
    for res in ("5", "15", "60", "240", "1D"):
        tid = discover_tab(res)
        print(f"  {res:>4} -> {tid[:8] if tid else 'AUSENTE'}")
