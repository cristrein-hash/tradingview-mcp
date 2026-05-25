#!/usr/bin/env python3
"""run_xau_replay_feature_collect.py — per-bar FEATURE collector for any symbol/timeframe via TradingView Replay.

Timeframe-agnostic: pass --timeframe (15|30|60|… chart resolution string) and --symbol.
Defaults to PEPPERSTONE:XAUUSD 15M. (Renamed from run_xau_15m_replay_backtest.py; the
capture logic is unchanged and already validated on the XAU 15M 3-month block.)

WHY REPLAY (not scroll + data_get_ohlcv): data_get_ohlcv reads only the loaded recent
bars and chart_scroll_to_date does NOT fetch deep history (see run_xau_15m_pullback_ohlcv.py,
which only ever collected ~7 days). Replay mode (replay_start + replay_step) actually
loads/advances historical bars, so each step exposes the chart's full indicator/signal
state AT that historical bar — the basis for a decision-feature dataset.

Mirrors the proven run_xau_4h_backtest.py capture pattern. Reliability > speed.

Per-bar features captured (recorded as null + flagged in _feature_availability when a
source is unavailable — NEVER faked):
  symbol, timeframe, bar_index, replay_current_date (+iso), ohlcv (last bars + meta),
  study_values (all visible indicators), pine_boxes, pine_labels,
  pine_shapes (Bubbles), pine_lines.

USAGE — ALWAYS inside the safe_backtest_window.sh maintenance window (never bare python):
  --symbol SYM        chart symbol (default PEPPERSTONE:XAUUSD)
  --timeframe TF      chart resolution string: 15|30|60 (default 15)
  --start-date YYYY-MM-DD  replay start date (alias --date; default ~90 days ago)
  --end-date YYYY-MM-DD    stop once replay reaches this date (--bars then a safety cap)
  --bars N            total bars to capture (default 80 = smoke) OR safety cap with --end-date
  --checkpoint-every  checkpoint frequency (default 20)
  --resume            continue from the last checkpoint (same live replay only)
  --dry-run           init + 1 bar then exit
Requires /tmp/claude_recheck.paused (set by the maintenance window).
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path


def repo_root():
    """Resolve the tradingview-mcp repo root robustly (survives file moves)."""
    import os
    from pathlib import Path as _Path
    env = os.environ.get("TVMCP_ROOT")
    if env and _Path(env).expanduser().is_dir():
        return _Path(env).expanduser().resolve()
    cur = _Path(__file__).resolve().parent
    for d in (cur, *cur.parents):
        if (d / ".git").exists() or (d / "src" / "server.js").exists() \
           or ((d / "alert-bridge").is_dir() and (d / "my-strategy").is_dir()):
            return d
    raise RuntimeError(f"TVMCP repo root not found from {__file__}; set TVMCP_ROOT or run inside the repo")


BASE_DIR = repo_root()
# Reuse the hardened stdio MCP client (threads + queue + real timeout). Read-only reuse —
# this does NOT modify run_xau_15m_pullback_ohlcv.py; only its MCPClient class is imported.
sys.path.insert(0, str(BASE_DIR / "alert-bridge"))
from run_xau_15m_pullback_ohlcv import MCPClient  # noqa: E402

MCP_SERVER_PATH = BASE_DIR / "src" / "server.js"
BACKTESTS_DIR = BASE_DIR / "alert-bridge" / "logs" / "backtests"
PAUSE_FLAG = Path("/tmp/claude_recheck.paused")

DEFAULT_SYMBOL = "PEPPERSTONE:XAUUSD"
DEFAULT_TIMEFRAME = "15"
DEFAULT_BARS = 80
CHECKPOINT_EVERY = 20
PER_CALL_TIMEOUT_S = 60
RESTORE_TIMEOUT_S = 30

# Feature sources captured per bar (tool, args, snapshot key).
FEATURE_SOURCES = [
    ("data_get_study_values", {}, "study_values"),
    ("data_get_pine_boxes", {"verbose": True}, "pine_boxes"),
    ("data_get_pine_labels", {"max_labels": 500, "verbose": True}, "pine_labels"),
    ("data_get_pine_shapes", {"study_filter": "Bubbles", "max_bars": 20}, "pine_shapes_bubbles"),
    ("data_get_pine_lines", {"verbose": True}, "pine_lines"),
]


def _log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def ts_iso(ts):
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except Exception:
        return None


def capture_bar(client, bar_index, symbol, timeframe):
    """Capture one bar's full feature snapshot. Missing sources -> null + availability flag."""
    t0 = time.monotonic()
    snap = {
        "symbol": symbol,
        "timeframe": timeframe,
        "bar_index": bar_index,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }
    avail = {}

    rs = client.call_tool("replay_status")
    snap["replay_current_date"] = rs.get("current_date") if isinstance(rs, dict) else None
    snap["replay_current_dt"] = ts_iso(snap.get("replay_current_date"))

    for tool, args, key in FEATURE_SOURCES:
        resp = client.call_tool(tool, args)
        val = resp.get("studies") if isinstance(resp, dict) and "studies" in resp else None
        snap[key] = val
        avail[key] = bool(val)  # honest: True only if the source returned studies

    o = client.call_tool("data_get_ohlcv", {"count": 5, "summary": False})
    if isinstance(o, dict) and (o.get("bars") or o.get("last_5_bars")):
        snap["ohlcv"] = o.get("bars") or o.get("last_5_bars")
        snap["ohlcv_meta"] = {
            "bar_count": o.get("bar_count"),
            "period_from": (o.get("period") or {}).get("from"),
            "period_to": (o.get("period") or {}).get("to"),
        }
        avail["ohlcv"] = True
    else:
        snap["ohlcv"] = None
        snap["ohlcv_meta"] = None
        avail["ohlcv"] = False

    snap["_feature_availability"] = avail
    snap["elapsed_s"] = round(time.monotonic() - t0, 2)
    return snap


def main():
    p = argparse.ArgumentParser(description="XAU 15M per-bar feature collector via TradingView Replay")
    p.add_argument("--symbol", default=DEFAULT_SYMBOL)
    p.add_argument("--timeframe", default=DEFAULT_TIMEFRAME)
    p.add_argument("--date", "--start-date", dest="date", default=None,
                   help="Replay START date YYYY-MM-DD (default ~90d ago)")
    p.add_argument("--end-date", dest="end_date", default=None,
                   help="Stop once replay reaches this date YYYY-MM-DD (window mode; --bars is then a safety cap)")
    p.add_argument("--bars", type=int, default=DEFAULT_BARS,
                   help="Bar count (fixed when no --end-date) OR safety cap (with --end-date)")
    p.add_argument("--checkpoint-every", type=int, default=CHECKPOINT_EVERY)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="init + 1 bar then exit")
    p.add_argument("--no-restore-chart", action="store_true")
    p.add_argument("--suffix", default="")
    args = p.parse_args()

    if args.date is None:
        args.date = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")

    end_epoch = None
    if args.end_date:
        try:
            end_epoch = int(datetime.fromisoformat(args.end_date).replace(tzinfo=timezone.utc).timestamp())
        except Exception:
            print(f"ERRO: --end-date inválida: {args.end_date} (use YYYY-MM-DD)", file=sys.stderr)
            return 1

    if not PAUSE_FLAG.exists():
        print(f"ERRO: pause flag não encontrada: {PAUSE_FLAG}", file=sys.stderr)
        print("Rode dentro do maintenance window (safe_backtest_window.sh).", file=sys.stderr)
        return 1

    BACKTESTS_DIR.mkdir(parents=True, exist_ok=True)
    sym_short = args.symbol.split(":")[-1]
    if args.end_date:
        out_basename = f"{sym_short}_{args.timeframe}m_replay_{args.date}_to_{args.end_date}{args.suffix}"
    else:
        out_basename = f"{sym_short}_{args.timeframe}m_replay_{args.date}_{args.bars}bars{args.suffix}"
    out_jsonl = BACKTESTS_DIR / f"{out_basename}.jsonl"
    checkpoint_path = BACKTESTS_DIR / f"{out_basename}.checkpoint.json"

    start_bar = 0
    if args.resume and checkpoint_path.exists():
        try:
            cp = json.loads(checkpoint_path.read_text())
            start_bar = cp.get("last_bar_completed", -1) + 1
            _log(f"RESUME: continuando do bar {start_bar} (replay deve já estar ativo)")
        except Exception as e:
            _log(f"RESUME falhou ({e}); começando do zero")

    _log(f"Iniciando replay feature collect")
    print(f"  symbol={args.symbol} tf={args.timeframe} date={args.date} bars={args.bars} "
          f"start_bar={start_bar} dry_run={args.dry_run}")
    print(f"  output: {out_jsonl}")

    client = MCPClient(MCP_SERVER_PATH)
    client.start()
    _log("MCP conectado.")
    health = client.call_tool("tv_health_check", timeout=15)
    if not isinstance(health, dict) or not health.get("cdp_connected"):
        client.stop()
        _log(f"!! tv_health_check sem CDP: {health}")
        return 1
    _log(f"    CDP connected={health.get('cdp_connected')}")

    exit_code = 0
    original_symbol = original_tf = None
    avail_agg = {}
    bars_done = 0
    first_dt = last_dt = None

    try:
        state = client.call_tool("chart_get_state")
        if isinstance(state, dict):
            original_symbol = state.get("symbol")
            original_tf = state.get("resolution")
            _log(f"    chart original: {original_symbol} {original_tf}")

        if start_bar == 0:
            _log(f"Setup: trocar pra {args.symbol} {args.timeframe}...")
            r = client.call_tool("chart_set_symbol", {"symbol": args.symbol})
            if not r.get("success"):
                raise RuntimeError(f"chart_set_symbol failed: {r}")
            time.sleep(1)
            r = client.call_tool("chart_set_timeframe", {"timeframe": args.timeframe})
            if not r.get("success"):
                raise RuntimeError(f"chart_set_timeframe failed: {r}")
            time.sleep(1)
            _log(f"replay_start({args.date})...")
            r = client.call_tool("replay_start", {"date": args.date})
            if not isinstance(r, dict) or not r.get("success"):
                raise RuntimeError(f"replay_start failed: {r}")
            _log(f"    replay iniciado: current_date={r.get('current_date')} ({ts_iso(r.get('current_date'))})")
            time.sleep(2)
        else:
            _log("RESUME: assumindo replay já ativo (se não, abortar e rodar sem --resume).")

        cap = args.bars  # fixed count (no --end-date) or safety cap (with --end-date)
        if args.dry_run:
            cap = start_bar + 1
            _log("DRY-RUN: capturando só 1 bar")

        mode = "a" if start_bar > 0 else "w"
        if end_epoch:
            _log(f"Loop até end-date {args.end_date} (safety cap {cap} bars), de bar {start_bar}...")
        else:
            _log(f"Loop {cap - start_bar} bars (de {start_bar} a {cap - 1})...")
        with out_jsonl.open(mode, encoding="utf-8") as f:
            i = start_bar
            while i < cap:
                guard = client.call_tool("chart_get_state")
                if guard.get("symbol") != args.symbol or guard.get("resolution") != args.timeframe:
                    err = (f"CHART MUDOU NO BAR {i}: esperado {args.symbol} {args.timeframe}, "
                           f"recebido {guard.get('symbol')} {guard.get('resolution')}")
                    _log(f"!! {err}")
                    f.write(json.dumps({"bar_index": i, "_error": "symbol_switch_detected",
                                        "captured_at": datetime.now(timezone.utc).isoformat()}) + "\n")
                    f.flush()
                    raise RuntimeError(err)

                try:
                    snap = capture_bar(client, i, args.symbol, args.timeframe)
                except Exception as e:
                    _log(f"  ERRO no bar {i}: {type(e).__name__}: {e}")
                    snap = {"bar_index": i, "_error": str(e),
                            "captured_at": datetime.now(timezone.utc).isoformat()}

                f.write(json.dumps(snap, ensure_ascii=False) + "\n")
                f.flush()
                bars_done += 1

                cur = snap.get("replay_current_date")
                if snap.get("replay_current_dt"):
                    last_dt = snap["replay_current_dt"]
                    if first_dt is None:
                        first_dt = last_dt
                for k, v in (snap.get("_feature_availability") or {}).items():
                    avail_agg[k] = avail_agg.get(k, 0) + (1 if v else 0)

                if (i + 1) % 10 == 0 or i == start_bar:
                    _log(f"  bar {i + 1} | replay_dt={snap.get('replay_current_dt')} | {snap.get('elapsed_s')}s")

                if (i + 1) % args.checkpoint_every == 0:
                    checkpoint_path.write_text(json.dumps({
                        "last_bar_completed": i, "out_jsonl": str(out_jsonl),
                        "symbol": args.symbol, "timeframe": args.timeframe,
                        "date": args.date, "end_date": args.end_date,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }, indent=2))
                    _log(f"  → checkpoint bar {i}")

                # stop conditions: reached end-date, or hit the (safety) cap
                if end_epoch and cur and cur >= end_epoch:
                    _log(f"  atingiu end-date {args.end_date} no bar {i} — encerrando")
                    break
                if i + 1 >= cap:
                    if end_epoch:
                        _log(f"  !! safety cap {cap} bars atingido ANTES da end-date {args.end_date} — aumente --bars")
                    break
                step = client.call_tool("replay_step")
                if not isinstance(step, dict) or not step.get("success"):
                    _log(f"  WARN replay_step bar {i}: {step}")
                i += 1

        _log("Loop completo.")

    except Exception as e:
        _log(f"!! Exceção fatal: {type(e).__name__}: {e}")
        exit_code = 1
    finally:
        try:
            client.call_tool("replay_stop", timeout=RESTORE_TIMEOUT_S)
        except Exception as e:
            _log(f"    replay_stop falhou (não-fatal): {e}")
        if not args.no_restore_chart and original_symbol:
            try:
                client.call_tool("chart_set_symbol", {"symbol": original_symbol}, timeout=RESTORE_TIMEOUT_S)
                if original_tf:
                    client.call_tool("chart_set_timeframe", {"timeframe": original_tf}, timeout=RESTORE_TIMEOUT_S)
                _log(f"    chart restaurado: {original_symbol} {original_tf}")
            except Exception as e:
                _log(f"    restore falhou (não-fatal): {e}")
        try:
            client.stop()
        except Exception:
            pass

        # Honest summary: bars captured, real replay date range, per-feature availability.
        _log("===== RESUMO =====")
        _log(f"  bars capturados: {bars_done}")
        _log(f"  replay range real: {first_dt} -> {last_dt}")
        _log(f"  feature availability (bars com dado / {bars_done}):")
        for tool, _args, key in FEATURE_SOURCES:
            _log(f"    {key}: {avail_agg.get(key, 0)}/{bars_done}")
        _log(f"    ohlcv: {avail_agg.get('ohlcv', 0)}/{bars_done}")
        if out_jsonl.exists():
            _log(f"  linhas no JSONL: {sum(1 for _ in out_jsonl.open())}")
        _log(f"  Done. exit_code={exit_code}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
