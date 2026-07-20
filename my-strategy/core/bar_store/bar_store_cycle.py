#!/usr/bin/env python3
"""BAR-STORE — ÚNICO leitor MCP/CDP do stack (Fase 1 da arquitetura realtime, Cris 2026-07-18).
Um ciclo: para cada TF devido, lê a tab pinada (read-only, sem trocar chart) e appenda barras FECHADAS
novas ao store canónico, validadas (grelha/fase, OHLC sanidade, monotónico, t+dur<=now, fail-closed).
Bubbles 15M em union incremental. Consumidores (Cp, regime engine, backfill, futuros) leem FICHEIROS —
zero MCPClient próprio => zero contenção CDP, um validador, buffers idênticos por construção.
Store: 15M/1D/bubbles em store/ ; 4H/1H = os RAW canónicos já existentes (research lê os mesmos).
Cadências internas: 15M+bubbles todo ciclo (60s) · 1H a cada 5min · 4H/1D a cada 15min.
Seed one-time: se store 15M vazio, importa o buffer Cp existente. Heartbeat em store/store_meta.json.
py3.9 stdlib. CLI: --once (default: 1 ciclo) · --status."""
import os, sys, json, time, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
CORE = Path(__file__).resolve().parents[1]
REPO = CORE.parents[1]
sys.path.insert(0, str(CORE))
sys.path.insert(0, str(REPO / "alert-bridge"))
from draw_xau_4h_trades import MCPClient

HERE = Path(__file__).resolve().parent
STORE = HERE / "store"; STORE.mkdir(exist_ok=True)
REV = REPO / "my-strategy/research/revalidation"
CP_STATE = REPO / "my-strategy/strategies/xau_15m_long/reversal/CP_CAPITULATION/.cp_state"
META_F = STORE / "store_meta.json"
LOG = STORE / "store_cycle.log"
LX = ZoneInfo("Europe/Lisbon")
iso = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%Y-%m-%d %H:%M")

# TF -> (dur_s, fase_da_grelha, ficheiro, count_leitura, periodo_poll_s, retenção_s|None=infinita)
# res/symbol default = a chave/XAUUSD; DXY1D lê a tab TVC:DXY 1D e estende o canónico raw_dxy_1d (Layer1).
TFS = {
    "5":   {"dur": 300,   "phase": 0,    "file": STORE / "bars_5m.jsonl",  "count": 60,  "poll": 60,  "retain": 14*86400},
    "15":  {"dur": 900,   "phase": 0,    "file": STORE / "bars_15m.jsonl", "count": 40,  "poll": 60,  "retain": 30*86400},
    "60":  {"dur": 3600,  "phase": 0,    "file": REV / "raw_1h_ohlc.jsonl", "count": 12, "poll": 300, "retain": None},
    "240": {"dur": 14400, "phase": 7200, "file": REV / "raw_4h_ohlc.jsonl", "count": 8,  "poll": 900, "retain": None},
    "1D":  {"dur": 86400, "phase": None, "file": STORE / "bars_1d.jsonl",  "count": 400, "poll": 900, "retain": None},
    "DXY1D": {"dur": 86400, "phase": None, "file": REV / "raw_dxy_1d.jsonl", "count": 400, "poll": 900, "retain": None,
              "res": "1D", "symbol": "DXY"},
}
BUB_F = STORE / "bubbles_15m.jsonl"
BUB_RETAIN = 30 * 86400


def _log(o):
    with open(LOG, "a") as fh:
        fh.write(json.dumps(o, ensure_ascii=False) + "\n")


def _jl(f):
    try:
        return [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    except Exception:
        return []


def _meta():
    try: return json.loads(META_F.read_text())
    except Exception: return {}


def _save_meta(m):
    tmp = META_F.with_suffix(".json.tmp"); tmp.write_text(json.dumps(m)); os.replace(tmp, META_F)


def discover_tabs():
    """1 passagem: mapeia resolution -> target id (sem cache stale)."""
    import urllib.request
    with urllib.request.urlopen("http://localhost:9222/json/list", timeout=8) as r:
        tgs = [t["id"] for t in json.loads(r.read())
               if t.get("type") == "page" and "tradingview.com/chart" in (t.get("url") or "").lower()]
    out = {}
    for tid in tgs:
        os.environ["TVMCP_TARGET_CHART_ID"] = tid
        c = MCPClient(); c.start()
        try:
            res = str((c.call_tool("chart_get_state") or {}).get("resolution"))
            if res and res not in out:
                out[res] = tid
        finally:
            c.stop()
    return out


def seed_15m():
    """One-time: importa buffer Cp existente para o store 15M (mesma validação já feita lá)."""
    tgt = TFS["15"]["file"]
    if tgt.exists() and tgt.stat().st_size > 0:
        return 0
    src = CP_STATE / "ohlc_15m.jsonl"
    rows = _jl(src)
    if rows:
        tgt.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    bs = _jl(CP_STATE / "bubbles.jsonl")
    if bs and not BUB_F.exists():
        BUB_F.write_text("\n".join(json.dumps(r) for r in bs) + "\n")
    return len(rows)


def append_tf(tf, tid, bars):
    """Valida e appenda barras fechadas novas. Devolve (n_novas, erro)."""
    cfg = TFS[tf]; D = cfg["dur"]; f = cfg["file"]
    now = int(time.time())
    rows = _jl(f)
    n0 = len(rows)
    if cfg["retain"]:
        cut = now - cfg["retain"]
        rows = [r for r in rows if r["t"] >= cut]
    trimmed = n0 - len(rows)
    have = {r["t"] for r in rows}
    last = max(have) if have else 0
    phase = cfg["phase"]                            # None (1D) = SEM validação de grelha: a fase diária
                                                    # muda nas transições DST (ex. 2025-11-02) — só
                                                    # monotónico + sanidade OHLC + fechada
    new = []
    for b in sorted(bars, key=lambda x: x.get("time") or 0):
        t = b.get("time")
        if t is None or b.get("close") is None or t in have:
            continue
        if t + D > now:                             # em formação
            continue
        if phase is not None and t % D != phase:
            return 0, f"{tf}: t {iso(t)} fora da fase ({t % D} != {phase})"
        o, h, l, cc = b.get("open"), b.get("high"), b.get("low"), b.get("close")
        if o is None or h is None or l is None or not (h >= l and h >= cc >= l and h >= o >= l):
            return 0, f"{tf}: OHLC inválido em {iso(t)}"
        if t <= last and t in have:
            continue
        new.append({"t": t, "o": o, "h": h, "l": l, "c": cc}); have.add(t)
    if new or trimmed:                              # só reescreve com mudança REAL (WatchPaths = evento limpo)
        rows = sorted(rows + new, key=lambda r: r["t"])
        tmp = f.with_suffix(".jsonl.tmp")
        tmp.write_text("\n".join(json.dumps(r) for r in rows) + ("\n" if rows else ""))
        os.replace(tmp, f)
    return len(new), None


def append_bubbles(pairs):
    now = int(time.time()); cut = now - BUB_RETAIN
    rows = [r for r in _jl(BUB_F) if (r.get("t") or 0) >= cut]
    seen = {(r["t"], r["plot"]) for r in rows}
    n = 0
    for t, plot in pairs:
        if t is None or t < cut or (t, plot) in seen:
            continue
        rows.append({"t": t, "plot": plot}); seen.add((t, plot)); n += 1
    if n:
        rows.sort(key=lambda r: r["t"])
        tmp = BUB_F.with_suffix(".jsonl.tmp")
        tmp.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        os.replace(tmp, BUB_F)
    return n


def _shape_pairs(pb):
    out = []
    for s in (pb or {}).get("studies", []):
        for a in s.get("activations", []):
            t = a.get("time")
            for plot in (a.get("shapes") or {}):
                out.append((t, plot))
    return out


def read_tab(tid, tf, count):
    """Lê TUDO o que os consumidores precisam desta tab numa só sessão MCP:
    OHLC + pine_boxes (zonas/OB) + study_values (indicadores) + (15M) bubbles/NAS shapes."""
    os.environ["TVMCP_TARGET_CHART_ID"] = tid
    c = MCPClient(); c.start()
    try:
        oh = c.call_tool("data_get_ohlcv", {"count": count}) or {}
        bars = oh.get("bars") or oh.get("ohlcv") or []
        boxes = c.call_tool("data_get_pine_boxes") or {}
        sv = c.call_tool("data_get_study_values") or {}
        pairs = nas = []
        if tf == "15":
            pairs = _shape_pairs(c.call_tool("data_get_pine_shapes", {"study_filter": "Market Order", "max_bars": 200}) or {})
            nas = _shape_pairs(c.call_tool("data_get_pine_shapes", {"study_filter": "NAS", "max_bars": 200}) or {})
        return bars, pairs, nas, boxes, sv
    finally:
        c.stop()


def _snap(name, tf, payload):
    f = STORE / f"{name}_{tf}.json"
    tmp = f.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"ts": int(time.time()), "tf": tf, "data": payload}, ensure_ascii=False))
    os.replace(tmp, f)


def append_nas(pairs):
    f = STORE / "nas_15m.jsonl"
    now = int(time.time()); cut = now - BUB_RETAIN
    rows = [r for r in _jl(f) if (r.get("t") or 0) >= cut]
    seen = {(r["t"], r["plot"]) for r in rows}
    n = 0
    for t, plot in pairs:
        if t is None or t < cut or (t, plot) in seen:
            continue
        rows.append({"t": t, "plot": plot}); seen.add((t, plot)); n += 1
    if n:
        rows.sort(key=lambda r: r["t"])
        tmp = f.with_suffix(".jsonl.tmp")
        tmp.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        os.replace(tmp, f)
    return n


def main():
    if "--status" in sys.argv:
        m = _meta()
        for tf, cfg in TFS.items():
            rows = _jl(cfg["file"])
            print(f"  {tf:<4} n={len(rows):>6} last={iso(rows[-1]['t']) if rows else '-'} poll_ts={m.get('poll', {}).get(tf)}")
        bs = _jl(BUB_F); print(f"  bub  n={len(bs):>6} last={iso(bs[-1]['t']) if bs else '-'}")
        return 0
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    out = {"ts": ts}
    n_seed = seed_15m()
    if n_seed: out["seed_15m"] = n_seed
    meta = _meta(); poll = meta.setdefault("poll", {})
    now = int(time.time())
    due = [tf for tf, cfg in TFS.items() if now - (poll.get(tf) or 0) >= cfg["poll"] - 5]
    if not due:
        out["status"] = "NOOP (nada devido)"; _log(out); print(json.dumps(out)); return 0
    # tab->id via tab_pin (cache-first: verifica só a tab necessária, re-enumera em miss) — B da auditoria
    # 2026-07-18: ciclos só-15M passam de 5 sessões MCP (discover_tabs full) para 1 (verify do cache).
    import tab_pin
    errs = []
    for tf in due:
        cfg = TFS[tf]
        res = cfg.get("res", tf); symbol = cfg.get("symbol", "XAUUSD")
        try:
            tid = tab_pin.discover_tab(res, symbol_suffix=symbol)
        except Exception as e:
            errs.append(f"{tf}: discover {str(e)[:40]}"); continue
        if not tid:
            errs.append(f"{tf}: sem tab"); continue
        try:
            bars, pairs, nas, boxes, sv = read_tab(tid, tf, cfg["count"])
        except Exception as e:
            errs.append(f"{tf}: read {str(e)[:40]}"); continue
        n, err = append_tf(tf, tid, bars)
        if err:
            errs.append(err); continue
        out[f"new_{tf}"] = n
        if symbol == "XAUUSD":                      # snaps só XAU (DXY não alimenta o E0 mtf)
            _snap("pine_boxes", tf, boxes)          # zonas/OB p/ E0 mtf
            _snap("study_values", tf, sv)           # indicadores p/ E0 mtf/micro
        if tf == "15":
            out["new_bub"] = append_bubbles(pairs)
            out["new_nas"] = append_nas(nas)
        poll[tf] = now
    meta["last_cycle"] = ts; meta["errors"] = errs
    _save_meta(meta)
    out["errors"] = errs
    out["status"] = "OK" if not errs else f"PARTIAL ({len(errs)} err)"
    _log(out); print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
