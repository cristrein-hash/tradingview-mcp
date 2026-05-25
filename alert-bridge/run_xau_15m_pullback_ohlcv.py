#!/usr/bin/env python3
"""
run_xau_15m_pullback_ohlcv.py — Coleta OHLCV histórico XAU 15M via MCP batch.

Não usa replay per-bar (impraticável pra 23k bars). Em vez disso:
  - Setup chart_set_symbol + chart_set_timeframe
  - Loop: chart_scroll_to_date(d) → data_get_ohlcv(count=500) → dedup → avança data
  - Save tudo num JSONL local pra analyze_xau_15m_pullback.py consumir

Por que essa abordagem (vs replay):
  - Replay 23k bars × ~4s/bar = ~26h impraticável
  - OHLCV batch ~46 chunks × 5s = ~5-10min
  - Mesma fonte (TradingView oficial)
  - PULLBACK_EMA50 não precisa indicators externos (Bubbles/NAS/OB)

Pré-requisitos:
  - TV Desktop aberto
  - Pause flag: touch /tmp/claude_recheck.paused
  - LaunchAgents MCP-dependentes desativados (claude-intraday-monitor, claude-monitor,
    xau-4h-monitor-daemon, xau-4h-monitor-cron)

Uso:
  python3 run_xau_15m_pullback_ohlcv.py                          # default: 12 meses
  python3 run_xau_15m_pullback_ohlcv.py --months 3 --dry-run     # smoke test 3 meses
  python3 run_xau_15m_pullback_ohlcv.py --resume                 # continua checkpoint

Output:
  alert-bridge/logs/backtests/xau_15m_ohlcv_<start>_to_<end>.jsonl
  alert-bridge/logs/backtests/xau_15m_ohlcv_<start>_to_<end>.checkpoint.json

Cada linha do JSONL = 1 bar OHLCV:
  {"time": 1733280000, "open": 2604.5, "high": 2605.0, "low": 2603.1, "close": 2604.8, "volume": 1234}
"""

from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse
import json
import queue
import subprocess
import sys
import threading
import time

BASE_DIR = Path(__file__).parent.parent
MCP_SERVER_PATH = BASE_DIR / "src" / "server.js"
NODE_BIN = "/opt/homebrew/bin/node"
BACKTESTS_DIR = Path(__file__).parent / "logs" / "backtests"
PAUSE_FLAG = Path("/tmp/claude_recheck.paused")

DEFAULT_SYMBOL = "PEPPERSTONE:XAUUSD"
DEFAULT_TIMEFRAME = "15"
DEFAULT_MONTHS = 12
OHLCV_CHUNK_BARS = 500
PER_CALL_TIMEOUT_S = 60
INIT_TIMEOUT_S = 20
HEALTH_TIMEOUT_S = 15
# chart_set_symbol reloads the chart and can take ~10.6s; give restore headroom.
RESTORE_TIMEOUT_S = 30
INTER_CHUNK_SLEEP_S = 0.5
CHECKPOINT_EVERY_CHUNKS = 5
DEFAULT_SMOKE_TIMEOUT_S = 120


def _log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


class MCPClient:
    """Mínimo MCP client JSON-RPC 2.0 via stdio com timeout real (thread + queue).

    Por que threads: subprocess.PIPE.readline() é syscall blocante. Sem reader
    thread separada, qualquer hang do MCP server trava o Python indefinidamente.
    Reader thread injeta linhas em queue.Queue, e _call_raw espera com get(timeout=N)
    — timeout que realmente dispara.
    """

    def __init__(self, server_path: Path):
        self.server_path = server_path
        self.proc = None
        self._req_id = 0
        self._stdout_q = queue.Queue()
        self._stderr_buf = []
        self._stop_event = threading.Event()
        self._stdout_thread = None
        self._stderr_thread = None

    def start(self):
        self.proc = subprocess.Popen(
            [NODE_BIN, str(self.server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._stdout_thread = threading.Thread(
            target=self._reader_stdout, name="mcp-stdout-reader", daemon=True)
        self._stderr_thread = threading.Thread(
            target=self._reader_stderr, name="mcp-stderr-reader", daemon=True)
        self._stdout_thread.start()
        self._stderr_thread.start()
        resp = self._call_raw("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "xau-15m-ohlcv", "version": "1.0.0"},
        }, timeout=INIT_TIMEOUT_S)
        if "error" in resp:
            raise RuntimeError(f"MCP initialize failed: {resp['error']}")
        self._notify("notifications/initialized", {})

    def _reader_stdout(self):
        try:
            for line in self.proc.stdout:
                if self._stop_event.is_set():
                    break
                self._stdout_q.put(line)
        except Exception:
            pass
        finally:
            self._stdout_q.put(None)  # sentinel: stream fechado

    def _reader_stderr(self):
        try:
            for line in self.proc.stderr:
                if self._stop_event.is_set():
                    break
                self._stderr_buf.append(line.rstrip())
                if len(self._stderr_buf) > 500:
                    self._stderr_buf = self._stderr_buf[-500:]
        except Exception:
            pass

    def stderr_tail(self, n=20):
        return self._stderr_buf[-n:]

    def stop(self):
        """Idempotente, nunca trava. terminate→wait3→kill→wait2→join threads."""
        if not self.proc:
            return
        self._stop_event.set()
        try:
            if self.proc.stdin and not self.proc.stdin.closed:
                self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.terminate()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                self.proc.kill()
            except Exception:
                pass
            try:
                self.proc.wait(timeout=2)
            except Exception:
                pass
        except Exception:
            pass
        for t in (self._stdout_thread, self._stderr_thread):
            if t and t.is_alive():
                t.join(timeout=1)

    def _next_id(self):
        self._req_id += 1
        return self._req_id

    def _notify(self, method, params):
        msg = {"jsonrpc": "2.0", "method": method, "params": params}
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def _call_raw(self, method, params, timeout=PER_CALL_TIMEOUT_S):
        if self.proc.poll() is not None:
            raise RuntimeError(f"MCP server morreu (returncode={self.proc.returncode})")
        req_id = self._next_id()
        msg = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
        try:
            self.proc.stdin.write(json.dumps(msg) + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, ValueError) as e:
            raise RuntimeError(f"MCP stdin write falhou: {e}")
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"MCP {method} timeout {timeout}s (sem resposta do server). "
                    f"stderr tail: {self.stderr_tail(5)}")
            try:
                line = self._stdout_q.get(timeout=min(remaining, 1.0))
            except queue.Empty:
                continue
            if line is None:
                raise RuntimeError(
                    f"MCP server fechou stdout durante {method}. "
                    f"stderr tail: {self.stderr_tail(5)}")
            try:
                resp = json.loads(line)
            except json.JSONDecodeError:
                continue
            if resp.get("id") == req_id:
                return resp

    def call_tool(self, name, arguments=None, timeout=PER_CALL_TIMEOUT_S):
        params = {"name": name, "arguments": arguments or {}}
        resp = self._call_raw("tools/call", params, timeout=timeout)
        if "error" in resp:
            return {"_error": resp["error"]}
        result = resp.get("result", {})
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            try:
                return json.loads(content[0]["text"])
            except Exception:
                return {"_raw_text": content[0]["text"]}
        return result


def _tool_logged(client, name, arguments=None, timeout=PER_CALL_TIMEOUT_S, label=None):
    """Wrap call_tool com log antes/depois + timing. Lança em timeout."""
    tag = label or name
    _log(f">>> MCP call: {tag}  args={arguments or {}}  timeout={timeout}s")
    t0 = time.monotonic()
    try:
        result = client.call_tool(name, arguments=arguments, timeout=timeout)
    except TimeoutError as e:
        elapsed = time.monotonic() - t0
        _log(f"!!! MCP TIMEOUT: {tag} após {elapsed:.1f}s — {e}")
        raise
    except Exception as e:
        elapsed = time.monotonic() - t0
        _log(f"!!! MCP ERROR: {tag} após {elapsed:.1f}s — {type(e).__name__}: {e}")
        raise
    elapsed = time.monotonic() - t0
    if isinstance(result, dict) and "_error" in result:
        _log(f"<<< MCP {tag} retornou _error em {elapsed:.2f}s: {result['_error']}")
    else:
        _log(f"<<< MCP {tag} OK em {elapsed:.2f}s")
    return result


def normalize_bars(ohlcv_resp):
    """Extrai lista de bars do response data_get_ohlcv. Retorna list[dict]."""
    if not isinstance(ohlcv_resp, dict):
        return []
    bars = ohlcv_resp.get("bars") or ohlcv_resp.get("last_5_bars") or []
    out = []
    for b in bars:
        if not isinstance(b, dict):
            continue
        t = b.get("time") or b.get("ts") or b.get("timestamp")
        if t is None:
            continue
        out.append({
            "time": int(t),
            "open": float(b.get("open", 0)),
            "high": float(b.get("high", 0)),
            "low": float(b.get("low", 0)),
            "close": float(b.get("close", 0)),
            "volume": float(b.get("volume", 0)),
        })
    return out


def main():
    parser = argparse.ArgumentParser(description="XAU 15M OHLCV batch collector via MCP")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--timeframe", default=DEFAULT_TIMEFRAME)
    parser.add_argument("--months", type=int, default=DEFAULT_MONTHS,
                        help="Janela retroativa em meses (default 12)")
    parser.add_argument("--end-date", default=None,
                        help="Data final do range (default: hoje). Formato YYYY-MM-DD.")
    parser.add_argument("--chunk-bars", type=int, default=OHLCV_CHUNK_BARS,
                        help="Bars por chamada data_get_ohlcv (cap 500)")
    parser.add_argument("--resume", action="store_true",
                        help="Continua do último checkpoint")
    parser.add_argument("--dry-run", action="store_true",
                        help="Faz só 2 chunks e sai")
    parser.add_argument("--no-restore-chart", action="store_true",
                        help="Skip restore chart no final")
    parser.add_argument("--suffix", default="")
    parser.add_argument("--smoke-timeout", type=int, default=0,
                        help=("Wall-clock max (segundos) pro loop de chunks. 0=desabilitado. "
                              f"Em --dry-run, default vira {DEFAULT_SMOKE_TIMEOUT_S}s."))
    args = parser.parse_args()
    if args.dry_run and args.smoke_timeout == 0:
        args.smoke_timeout = DEFAULT_SMOKE_TIMEOUT_S

    if not PAUSE_FLAG.exists():
        print(f"ERRO: pause flag não encontrada: {PAUSE_FLAG}", file=sys.stderr)
        print("Rode: touch /tmp/claude_recheck.paused", file=sys.stderr)
        return 1

    BACKTESTS_DIR.mkdir(parents=True, exist_ok=True)

    end_dt = datetime.now(timezone.utc)
    if args.end_date:
        end_dt = datetime.fromisoformat(args.end_date).replace(tzinfo=timezone.utc)
    start_dt = end_dt - timedelta(days=args.months * 30)
    end_iso = end_dt.strftime("%Y-%m-%d")
    start_iso = start_dt.strftime("%Y-%m-%d")

    sym_short = args.symbol.split(":")[-1]
    out_basename = f"{sym_short}_{args.timeframe}m_ohlcv_{start_iso}_to_{end_iso}{args.suffix}"
    out_jsonl = BACKTESTS_DIR / f"{out_basename}.jsonl"
    checkpoint_path = BACKTESTS_DIR / f"{out_basename}.checkpoint.json"

    cursor_iso = start_iso
    bars_collected_total = 0
    seen_times = set()

    if args.resume and checkpoint_path.exists():
        try:
            cp = json.loads(checkpoint_path.read_text())
            cursor_iso = cp.get("next_cursor_iso", start_iso)
            bars_collected_total = cp.get("bars_collected_total", 0)
            print(f"RESUME: cursor={cursor_iso}, bars_já_coletados={bars_collected_total}")
            if out_jsonl.exists():
                with out_jsonl.open() as f:
                    for line in f:
                        try:
                            rec = json.loads(line)
                            if "time" in rec:
                                seen_times.add(int(rec["time"]))
                        except Exception:
                            continue
                print(f"  dedup: {len(seen_times)} timestamps já no JSONL")
        except Exception as e:
            print(f"RESUME falhou ({e}), começando do zero")

    print(f"[{datetime.now().isoformat()}] Iniciando OHLCV batch collector")
    print(f"  symbol: {args.symbol}")
    print(f"  timeframe: {args.timeframe}")
    print(f"  range: {start_iso} → {end_iso} ({args.months} meses)")
    print(f"  cursor inicial: {cursor_iso}")
    print(f"  chunk size: {args.chunk_bars} bars")
    print(f"  output: {out_jsonl}")
    print()

    client = MCPClient(MCP_SERVER_PATH)
    original_symbol = None
    original_tf = None
    chunks_done = 0
    exit_code = 0
    t_smoke_start = time.monotonic()

    try:
        _log("Spawnando MCP server...")
        try:
            client.start()
        except Exception as e:
            _log(f"!!! MCP start falhou: {type(e).__name__}: {e}")
            _log(f"    stderr tail: {client.stderr_tail(10)}")
            raise
        _log("MCP conectado.")

        health = _tool_logged(client, "tv_health_check",
                              timeout=HEALTH_TIMEOUT_S, label="tv_health_check")
        if not isinstance(health, dict) or not health.get("cdp_connected"):
            raise RuntimeError(
                f"tv_health_check reportou CDP desconectado ou resposta inválida: {health}")
        _log(f"    CDP: connected={health.get('cdp_connected')}, target_url={health.get('target_url')}")

        state = _tool_logged(client, "chart_get_state",
                             timeout=PER_CALL_TIMEOUT_S, label="chart_get_state[baseline]")
        if isinstance(state, dict):
            original_symbol = state.get("symbol")
            original_tf = state.get("resolution")
            _log(f"    chart original: {original_symbol} {original_tf}")

        if not args.resume:
            _log(f"Setup: trocar pra {args.symbol} {args.timeframe}...")
            r = _tool_logged(client, "chart_set_symbol",
                             {"symbol": args.symbol}, label="chart_set_symbol")
            if not r.get("success"):
                raise RuntimeError(f"chart_set_symbol failed: {r}")
            time.sleep(1)
            r = _tool_logged(client, "chart_set_timeframe",
                             {"timeframe": args.timeframe}, label="chart_set_timeframe")
            if not r.get("success"):
                raise RuntimeError(f"chart_set_timeframe failed: {r}")
            time.sleep(1)

        mode = "a" if args.resume else "w"
        expected_symbol = args.symbol
        expected_tf = args.timeframe
        max_chunks = 2 if args.dry_run else 10_000  # safety upper bound

        with out_jsonl.open(mode, encoding="utf-8") as f:
            t_start_loop = time.monotonic()
            while chunks_done < max_chunks:
                if args.smoke_timeout > 0:
                    elapsed_loop = time.monotonic() - t_smoke_start
                    if elapsed_loop > args.smoke_timeout:
                        _log(f"!! smoke-timeout {args.smoke_timeout}s atingido "
                             f"(elapsed {elapsed_loop:.1f}s). Abortando loop.")
                        break

                guard = _tool_logged(client, "chart_get_state",
                                     timeout=PER_CALL_TIMEOUT_S, label=f"chart_get_state[guard#{chunks_done+1}]")
                if guard.get("symbol") != expected_symbol or guard.get("resolution") != expected_tf:
                    err = (f"CHART MUDOU NO CHUNK {chunks_done}: esperado {expected_symbol} {expected_tf}, "
                           f"recebido {guard.get('symbol')} {guard.get('resolution')}")
                    _log(f"!! {err}")
                    raise RuntimeError(err)

                _log(f"[chunk {chunks_done+1}] cursor={cursor_iso}")
                t0 = time.monotonic()
                sc = _tool_logged(client, "chart_scroll_to_date",
                                  {"date": cursor_iso}, label=f"chart_scroll_to_date[{cursor_iso}]")
                if not sc.get("success"):
                    _log(f"    WARN scroll: {sc}")
                time.sleep(0.5)

                resp = _tool_logged(client, "data_get_ohlcv",
                                    {"count": args.chunk_bars, "summary": False},
                                    label=f"data_get_ohlcv[count={args.chunk_bars}]")
                bars = normalize_bars(resp)
                if not bars:
                    _log(f"    chunk vazio (cursor={cursor_iso}). Encerrando loop.")
                    break

                # Dedup + write
                new_bars = [b for b in bars if b["time"] not in seen_times]
                for b in new_bars:
                    f.write(json.dumps(b, ensure_ascii=False) + "\n")
                    seen_times.add(b["time"])
                f.flush()
                bars_collected_total += len(new_bars)

                last_bar_time = bars[-1]["time"]
                last_bar_iso = datetime.fromtimestamp(last_bar_time, tz=timezone.utc).isoformat()
                first_bar_time = bars[0]["time"]
                first_bar_iso = datetime.fromtimestamp(first_bar_time, tz=timezone.utc).isoformat()
                tf_seconds = int(args.timeframe) * 60 if args.timeframe.isdigit() else 900
                next_cursor_dt = datetime.fromtimestamp(last_bar_time + tf_seconds, tz=timezone.utc)
                cursor_iso = next_cursor_dt.strftime("%Y-%m-%d")

                elapsed = time.monotonic() - t0
                _log(f"    bars: {len(bars)} | novos (dedup): {len(new_bars)} | total: {bars_collected_total}")
                _log(f"    janela: {first_bar_iso} → {last_bar_iso}")
                _log(f"    próximo cursor: {cursor_iso} (chunk={elapsed:.1f}s)")

                # Stop condition: cursor passou end_date
                if next_cursor_dt > end_dt:
                    _log(f"    cursor passou end_date ({end_iso}). Encerrando.")
                    break

                chunks_done += 1
                if chunks_done % CHECKPOINT_EVERY_CHUNKS == 0:
                    cp = {
                        "next_cursor_iso": cursor_iso,
                        "bars_collected_total": bars_collected_total,
                        "chunks_done": chunks_done,
                        "saved_at": datetime.now(timezone.utc).isoformat(),
                    }
                    checkpoint_path.write_text(json.dumps(cp, indent=2))
                    _log(f"    → checkpoint chunk {chunks_done}")

                time.sleep(INTER_CHUNK_SLEEP_S)

            total_elapsed = time.monotonic() - t_start_loop
            _log(f"Loop completo. Total: {bars_collected_total} bars únicos em {total_elapsed/60:.1f}min")

    except KeyboardInterrupt:
        _log("!! KeyboardInterrupt — abortando, finally garante cleanup.")
        exit_code = 130
    except TimeoutError as e:
        _log(f"!! TimeoutError fatal: {e}")
        exit_code = 124
    except Exception as e:
        _log(f"!! Exceção fatal: {type(e).__name__}: {e}")
        exit_code = 1
    finally:
        # Restore chart só se conseguimos identificar original E client ainda vivo
        if not args.no_restore_chart and original_symbol:
            try:
                _tool_logged(client, "chart_set_symbol",
                             {"symbol": original_symbol}, timeout=RESTORE_TIMEOUT_S,
                             label="chart_set_symbol[restore]")
                if original_tf:
                    _tool_logged(client, "chart_set_timeframe",
                                 {"timeframe": original_tf}, timeout=RESTORE_TIMEOUT_S,
                                 label="chart_set_timeframe[restore]")
                _log(f"    chart restaurado: {original_symbol} {original_tf}")
            except Exception as e:
                _log(f"    restore falhou (não-fatal): {type(e).__name__}: {e}")
        try:
            client.stop()
            _log("MCP server stopped (terminate/kill executado).")
        except Exception as e:
            _log(f"!! client.stop() falhou: {e}")
        _log(f"Output: {out_jsonl}")
        if out_jsonl.exists():
            lines = sum(1 for _ in out_jsonl.open())
            _log(f"Linhas no JSONL: {lines}")

    _log(f"Done. exit_code={exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
