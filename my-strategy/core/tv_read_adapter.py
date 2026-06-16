#!/usr/bin/env python3
"""TV read adapter — XAU-only (Production v2). Leitura controlada do chart via MCP.

Lê (READ-ONLY) um snapshot canônico do chart PEPPERSTONE:XAUUSD via o MCP server
(`src/server.js`, JSON-RPC stdio). NUNCA dirige/troca o chart (não chama set_symbol/
set_timeframe), NUNCA envia Telegram, NUNCA decide trade. Falha (hard stop) em vez de
dirigir o chart agressivamente.

Escopo XAU-only: só PEPPERSTONE:XAUUSD. Timeframes permitidos no design: 240, 60, 15.
Este módulo executa ativamente 240 (L1); 60/15 reservados para futuro.

Sem side effects no import. Default dry-run/read-only.
"""
import json, subprocess, time
from pathlib import Path

REPO = None
for d in [Path(__file__).resolve().parent] + list(Path(__file__).resolve().parents):
    if (d / "src" / "server.js").exists() and (d / "alert-bridge").is_dir():
        REPO = d; break
NODE = "/opt/homebrew/bin/node"
SYMBOL = "PEPPERSTONE:XAUUSD"
ALLOWED_TF = {"240", "60", "15"}
REQUIRED_STUDIES = ("Custom OB Detector", "Relative Strength Index")  # mínimos da L1


class _MCP:
    def __init__(s): s.p = None; s.i = 0
    def start(s):
        s.p = subprocess.Popen([NODE, str(REPO / "src" / "server.js")],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, bufsize=1)
        s._raw("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                              "clientInfo": {"name": "tv_read_adapter", "version": "1"}})
        s.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}) + "\n")
        s.p.stdin.flush()
    def _raw(s, m, pr, to=60):
        s.i += 1; rid = s.i
        s.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": rid, "method": m, "params": pr}) + "\n"); s.p.stdin.flush()
        dl = time.monotonic() + to
        while time.monotonic() < dl:
            ln = s.p.stdout.readline()
            if not ln: raise RuntimeError("mcp closed")
            try:
                r = json.loads(ln)
                if r.get("id") == rid: return r
            except Exception: continue
        raise TimeoutError(m)
    def call(s, name, args=None):
        r = s._raw("tools/call", {"name": name, "arguments": args or {}})
        if "error" in r: return {"_error": r["error"]}
        c = r.get("result", {}).get("content", [])
        if c and c[0].get("type") == "text":
            try: return json.loads(c[0]["text"])
            except Exception: return {"_raw": c[0]["text"]}
        return r.get("result", {})
    def stop(s):
        try: s.p.stdin.close()
        except Exception: pass
        try: s.p.terminate(); s.p.wait(timeout=5)
        except Exception:
            try: s.p.kill()
            except Exception: pass


def _hard(reason):
    return {"ok": False, "hard_stop": reason}


def read_xau_snapshot(timeframe="240"):
    """Lê snapshot canônico XAU via MCP (read-only). Hard-stop se não confirmar
    símbolo/TF/indicadores/campos. NÃO troca o chart."""
    tf = str(timeframe)
    if tf not in ALLOWED_TF:
        return _hard(f"timeframe '{tf}' fora do design XAU ({sorted(ALLOWED_TF)})")
    if REPO is None:
        return _hard("repo/src/server.js não localizado")
    m = _MCP();
    try:
        m.start()
        st = m.call("chart_get_state")
        if st.get("_error"): return _hard(f"chart_get_state falhou: {st['_error']}")
        sym = st.get("symbol"); res = str(st.get("resolution"))
        if sym != SYMBOL:
            return _hard(f"símbolo do chart '{sym}' != {SYMBOL} (NÃO troco símbolo)")
        if res != tf:
            return _hard(f"timeframe do chart '{res}' != requerido '{tf}' (NÃO dirijo chart)")
        names = [s.get("name", "") for s in st.get("studies", [])]
        missing = [req for req in REQUIRED_STUDIES if not any(req in n for n in names)]
        if missing:
            return _hard(f"indicadores necessários ausentes no chart: {missing}")
        # study_values -> RSI / RSI-based MA (estrutura variável -> varredura)
        rsi = rma = nas_dist = None
        svv = m.call("data_get_study_values")  # todos os estudos (RSI + NAS + ...)
        # tenta extrair RSI / RSI-based MA de qualquer formato retornado
        def num(x):
            try: return float(str(x).replace(" ", "").replace(",", "").replace("−", "-"))
            except Exception: return None
        def walk(o):
            nonlocal rsi, rma, nas_dist
            if isinstance(o, dict):
                for k, v in o.items():
                    if isinstance(v, (dict, list)): walk(v)
                    elif k == "RSI": rsi = num(v)
                    elif k in ("RSI-based MA", "RSI-based_MA"): rma = num(v)
                    elif k == "NAS_DISTANCE_FROM_EMA_ATR": nas_dist = num(v)
            elif isinstance(o, list):
                for v in o: walk(v)
        walk(svv)
        rsi_vs_ma = (rsi - rma) if (rsi is not None and rma is not None) else None
        # OHLCV recente (audit/contexto)
        oh = m.call("data_get_ohlcv", {"count": 300})
        bars = oh.get("bars") or oh.get("ohlcv") or []
        bar_time = bars[-1].get("time") if bars else None
        # Custom OB zones
        ob = m.call("data_get_pine_boxes", {"study_filter": "Custom OB"})
        ob_zones = []
        def walk_boxes(o):
            if isinstance(o, dict):
                if "high" in o and "low" in o and isinstance(o.get("high"), (int, float)):
                    ob_zones.append({"high": o["high"], "low": o["low"]})
                for v in o.values(): walk_boxes(v)
            elif isinstance(o, list):
                for v in o: walk_boxes(v)
        walk_boxes(ob)
        # study-values POR BAR (com timestamp) via data_get_study_values_at_bar — fonte causal do
        # bar FECHADO (≠ data-window/forming). Alinhamento por TIME é feito no runtime.
        def _series(filt, fields, count=8):
            r = m.call("data_get_study_values_at_bar", {"study_filter": filt, "count": count})
            out = []
            for s in (r.get("studies") or []):
                for b in (s.get("bars") or []):
                    vals = b.get("values") or {}
                    rec = {"time": b.get("time")}
                    for key, alias in fields.items():
                        v = vals.get(key)
                        rec[alias] = (float(v) if isinstance(v, (int, float)) else
                                      (lambda x: x if x is None else _num(x))(v))
                    out.append(rec)
            return out
        def _num(x):
            try: return float(str(x).replace(" ", "").replace(",", "").replace("−", "-"))
            except Exception: return None
        nas_series = _series("NAS", {"NAS_DISTANCE_FROM_EMA_ATR": "nas_dist"})
        rsi_series = _series("Relative Strength", {"RSI": "rsi", "RSI-based MA": "rsi_ma"})
        return {
            "ok": True,
            "symbol": sym, "timeframe": res,
            "bar_time": bar_time,
            "ohlcv_recent": bars,
            "rsi": rsi, "rsi_ma": rma, "rsi_vs_ma": rsi_vs_ma,
            "nas_dist": nas_dist,
            "ob_zones": ob_zones,
            "nas_series": nas_series,   # [{time, nas_dist}] por bar (fechado)
            "rsi_series": rsi_series,   # [{time, rsi, rsi_ma}] por bar (fechado)
            "studies_present": names,
            "raw_refs": {"studies": "data_get_study_values", "boxes": "data_get_pine_boxes:Custom OB",
                         "ohlcv": "data_get_ohlcv", "study_at_bar": "data_get_study_values_at_bar"},
        }
    finally:
        m.stop()


if __name__ == "__main__":
    import sys
    tf = sys.argv[sys.argv.index("--tf") + 1] if "--tf" in sys.argv else "240"
    print(json.dumps(read_xau_snapshot(tf), ensure_ascii=False, indent=2))
