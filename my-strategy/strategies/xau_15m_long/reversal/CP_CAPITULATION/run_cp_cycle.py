#!/usr/bin/env python3
"""Cp CAPITULATION — ciclo LIVE alert-only (Cris autorizou produção 2026-07-17; forward = árbitro, e este
runtime É o veículo do forward). Baseline CONGELADO (CP_ENGINE_PREREG_FORWARD_20260716); motor puro
cp_engine_live com PARITY PASS 26/26 vs RAW.
Ciclo (15 em 15 min, launchd): (1) lê tab 15M pinada (OHLC count 500 + pine_shapes 'Market Order') —
read-only, NÃO troca chart, NÃO pausa, coexiste com E0/E1/E2 (mesma técnica tab_pin/regime engine);
(2) appenda barras 15M FECHADAS ao buffer em disco + UNION das bubbles (retenção 10 dias) — cobre pernas
longas além das 500 barras da chamada; (3) corre o motor; (4) alerta Telegram SÓ para entradas cuja barra
de entrada é RECENTE (<= 2 barras) e ainda não alertadas (dedup por fundo_t em disco). Fail-closed: sem
tab 15M / sem barras / OHLC inválido => NO-OP com log, nunca inventa. py3.9 stdlib. Gate:
CP_PRODUCTION_AUTHORIZED=1 para enviar Telegram (senão dry: deteta e loga, não envia)."""
import os, sys, json, time, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
CORE = Path("/Users/cristrein/tradingview-mcp/my-strategy/core")
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(CORE))
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import cp_engine_live as ENG
from draw_xau_4h_trades import MCPClient

STATE = HERE / ".cp_state"; STATE.mkdir(exist_ok=True)
OHLC_F = STATE / "ohlc_15m.jsonl"
BUB_F = STATE / "bubbles.jsonl"
ALERTED_F = STATE / "alerted.jsonl"
LOG = STATE / "cp_cycle.log"
BAR_S = 900
RETAIN_S = 10 * 86400          # retenção buffer: 10 dias (> LEGWIN 480 barras = 5 dias)
FRESH_BARS = 2                 # só alerta entradas com <= 2 barras de idade (sinal operável)
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")   # convenção Cris 2026-07-17: TODA hora humana em Lisboa (interno fica epoch)
iso = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%Y-%m-%d %H:%M")


def _log(o):
    with open(LOG, "a") as fh:
        fh.write(json.dumps(o, ensure_ascii=False) + "\n")


def _load_jsonl(f):
    try:
        return [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    except Exception:
        return []


def find_tab_15m():
    """Tab 15M por descoberta direta (mesma técnica cp_plot_window/context_confluence)."""
    import urllib.request
    with urllib.request.urlopen("http://localhost:9222/json/list", timeout=8) as r:
        tgs = [t["id"] for t in json.loads(r.read())
               if t.get("type") == "page" and "tradingview.com/chart" in (t.get("url") or "").lower()]
    for tid in tgs:
        os.environ["TVMCP_TARGET_CHART_ID"] = tid
        c = MCPClient(); c.start()
        try:
            if str((c.call_tool("chart_get_state") or {}).get("resolution")) == "15":
                return tid
        finally:
            c.stop()
    return None


def read_tab(tid):
    """Lê OHLC (500) + shapes bubbles da tab 15M. Read-only."""
    os.environ["TVMCP_TARGET_CHART_ID"] = tid
    c = MCPClient(); c.start()
    try:
        oh = c.call_tool("data_get_ohlcv", {"count": 500}) or {}
        bars = oh.get("bars") or oh.get("ohlcv") or []
        pb = c.call_tool("data_get_pine_shapes", {"study_filter": "Market Order", "max_bars": 500}) or {}
    finally:
        c.stop()
    pairs = []
    for s in (pb or {}).get("studies", []):
        for a in s.get("activations", []):
            t = a.get("time")
            for plot in (a.get("shapes") or {}):
                pairs.append((t, plot))
    return bars, pairs


def update_buffers(bars, pairs):
    """Appenda barras FECHADAS novas (validadas, monotónico) + union bubbles. Fail-closed."""
    now = int(time.time())
    cut = now - RETAIN_S
    # --- OHLC ---
    rows = [r for r in _load_jsonl(OHLC_F) if r["t"] >= cut]
    have = {r["t"] for r in rows}
    last = max(have) if have else 0
    n_new = 0
    for b in sorted(bars, key=lambda x: x.get("time") or 0):
        t = b.get("time")
        if t is None or b.get("close") is None or t in have:
            continue
        if t + BAR_S > now:                       # barra em formação
            continue
        o, h, l, cc = b.get("open"), b.get("high"), b.get("low"), b.get("close")
        if o is None or h is None or l is None or not (h >= l and h >= cc >= l and h >= o >= l):
            return None, None, f"OHLC inválido em {iso(t)}"
        if t % BAR_S != 0:
            return None, None, f"t {iso(t)} fora da grelha 15M"
        rows.append({"t": t, "o": o, "h": h, "l": l, "c": cc}); have.add(t); n_new += 1
    rows.sort(key=lambda r: r["t"])
    tmp = OHLC_F.with_suffix(".tmp")
    tmp.write_text("\n".join(json.dumps(r) for r in rows) + ("\n" if rows else ""))
    os.replace(tmp, OHLC_F)
    # --- bubbles union ---
    bub = [r for r in _load_jsonl(BUB_F) if (r.get("t") or 0) >= cut]
    seen = {(r["t"], r["plot"]) for r in bub}
    n_bub = 0
    for t, plot in pairs:
        if t is None or t < cut or (t, plot) in seen:
            continue
        bub.append({"t": t, "plot": plot}); seen.add((t, plot)); n_bub += 1
    bub.sort(key=lambda r: r["t"])
    tmp = BUB_F.with_suffix(".tmp")
    tmp.write_text("\n".join(json.dumps(r) for r in bub) + ("\n" if bub else ""))
    os.replace(tmp, BUB_F)
    return (rows, bub), (n_new, n_bub), None


def detect_and_alert(rows, bub, send):
    T = [r["t"] for r in rows]; O = [r["o"] for r in rows]; H = [r["h"] for r in rows]
    L = [r["l"] for r in rows]; C = [r["c"] for r in rows]
    BUYS, SELLS = ENG.bubbles_from_pairs([(r["t"], r["plot"]) for r in bub])
    trades = ENG.scan(T, O, H, L, C, BUYS, SELLS)
    if not trades:
        return [], []
    last_t = T[-1]
    alerted = {r["fundo_t"] for r in _load_jsonl(ALERTED_F)}
    fired = []
    for s in trades:
        if s["fundo_t"] in alerted:
            continue
        if last_t - s["etime"] > FRESH_BARS * BAR_S:      # entrada velha (histórico do buffer) -> só regista
            with open(ALERTED_F, "a") as fh:
                fh.write(json.dumps({**s, "stale": True, "ts": iso(int(time.time()))}) + "\n")
            continue
        # formato único notify.py (Cris 2026-08-19) — antes: texto próprio via telegram_notify da L1 (prefixo errado)
        ok = None
        if send:
            try:
                sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
                import notify
                ok = notify.signal("ENTRADA", "CP CAPITULAÇÃO", "15M", "LONG",
                                   s["ent"], s["sl"], s["tgt"], r=3, audience="group")
            except Exception as e:
                ok = f"ERR {str(e)[:60]}"
        if send and ok is not True:                       # envio TENTADO e FALHOU -> NÃO marca dedup (re-tenta no próximo ciclo)
            continue
        with open(ALERTED_F, "a") as fh:
            fh.write(json.dumps({**s, "telegram": bool(send), "tg_ok": str(ok), "ts": iso(int(time.time()))}) + "\n")
        fired.append(s)
    return trades, fired


def _from_store():
    """STORE-FIRST (Fase 1, 2026-07-18): barras+bubbles do bar-store (zero CDP). None se não-fresco."""
    try:
        import store_reader as SR
        if not SR.fresh("15", mult=5):
            return None
        rows = SR.bars("15")
        bub = [{"t": t, "plot": p} for t, p in SR.shape_pairs("bubbles")]
        return rows, bub
    except Exception:
        return None


def main():
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    send = os.environ.get("CP_PRODUCTION_AUTHORIZED") == "1"
    out = {"ts": ts, "mode": "LIVE" if send else "DRY"}
    st = _from_store()
    if st is not None:
        rows, bub = st
        out["source"] = "store"
    else:
        try:                                    # anti-herd (auditoria #5): store stale -> gate o fallback-MCP
            import store_reader as SR
            if not SR.fallback_ok("cp"):
                out["status"] = "NO-OP: store stale + fallback gated (anti-herd)"; _log(out); print(json.dumps(out)); return
        except Exception:
            pass
        # fallback legado: leitura MCP própria + buffers locais (store doente)
        out["source"] = "mcp-fallback"
        tid = None
        try:
            tid = find_tab_15m()
        except Exception as e:
            out["status"] = f"HARD_STOP CDP: {str(e)[:60]}"; _log(out); print(json.dumps(out)); return
        if not tid:
            out["status"] = "NO_TAB_15M (no-op)"; _log(out); print(json.dumps(out)); return
        try:
            bars, pairs = read_tab(tid)
        except Exception as e:
            out["status"] = f"HARD_STOP read: {str(e)[:60]}"; _log(out); print(json.dumps(out)); return
        if not bars:
            out["status"] = "SEM_BARRAS (no-op)"; _log(out); print(json.dumps(out)); return
        res, counts, err = update_buffers(bars, pairs)
        if err:
            out["status"] = f"HARD_STOP buffer: {err}"; _log(out); print(json.dumps(out)); return
        rows, bub = res
    if not rows:
        out["status"] = "SEM_BARRAS (no-op)"; _log(out); print(json.dumps(out)); return
    out.update({"buf_bars": len(rows), "buf_bub": len(bub), "last_bar": iso(rows[-1]["t"])})
    trades, fired = detect_and_alert(rows, bub, send)
    out.update({"trades_in_buffer": len(trades), "alerts_fired": len(fired), "status": "OK"})
    _log(out); print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
