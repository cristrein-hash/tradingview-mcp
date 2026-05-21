#!/usr/bin/env python3
"""
run_xau_4h_backtest.py — Standalone backtest XAU 4H via MCP TradingView.

Spawnar o MCP server Node.js como subprocess, fala JSON-RPC 2.0 via stdio,
faz loop bar-a-bar em replay mode, captura snapshot dos indicators e OHLCV,
salva tudo em JSONL local. Suporta checkpoint/resume.

Conexão:
    Este script → MCP server Node.js (stdio) → CDP localhost:9222 → TV Desktop

Pré-requisitos:
    - TV Desktop aberto
    - 4 indicators no chart: Custom OB Detector v10, NAS TopBottom, Bubbles, RSI
    - Pause flag ativa: touch /tmp/claude_recheck.paused
    - Receiver pode estar vivo mas não vai disputar chart (respeita pause flag)

Uso:
    python3 run_xau_4h_backtest.py                       # default: 540 bars desde 2025-11-19
    python3 run_xau_4h_backtest.py --bars 100 --dry-run  # smoke test
    python3 run_xau_4h_backtest.py --resume              # continua do último checkpoint

Output:
    logs/backtests/xau_4h_<start>_to_<end>.jsonl
    logs/backtests/xau_4h_<start>_to_<end>.checkpoint.json
"""

from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import subprocess
import sys
import time

BASE_DIR = Path(__file__).parent.parent
MCP_SERVER_PATH = BASE_DIR / "src" / "server.js"
NODE_BIN = "/opt/homebrew/bin/node"
BACKTESTS_DIR = Path(__file__).parent / "logs" / "backtests"
PAUSE_FLAG = Path("/tmp/claude_recheck.paused")

DEFAULT_SYMBOL = "PEPPERSTONE:XAUUSD"
DEFAULT_TIMEFRAME = "240"
DEFAULT_START_DATE = "2025-11-19"
DEFAULT_BARS = 540
CHECKPOINT_EVERY = 50
PER_CALL_TIMEOUT_S = 60


class MCPClient:
    """Mínimo MCP client JSON-RPC 2.0 via stdio para o server Node.js."""

    def __init__(self, server_path: Path):
        self.server_path = server_path
        self.proc = None
        self._req_id = 0

    def start(self):
        self.proc = subprocess.Popen(
            [NODE_BIN, str(self.server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        # MCP handshake — initialize
        resp = self._call_raw("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "xau-backtest", "version": "1.0.0"},
        })
        if "error" in resp:
            raise RuntimeError(f"MCP initialize failed: {resp['error']}")
        # initialized notification (no response)
        self._notify("notifications/initialized", {})

    def stop(self):
        if self.proc:
            try:
                self.proc.stdin.close()
            except Exception:
                pass
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()

    def _next_id(self):
        self._req_id += 1
        return self._req_id

    def _notify(self, method, params):
        msg = {"jsonrpc": "2.0", "method": method, "params": params}
        line = json.dumps(msg) + "\n"
        self.proc.stdin.write(line)
        self.proc.stdin.flush()

    def _call_raw(self, method, params, timeout=PER_CALL_TIMEOUT_S):
        req_id = self._next_id()
        msg = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
        line = json.dumps(msg) + "\n"
        self.proc.stdin.write(line)
        self.proc.stdin.flush()

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            resp_line = self.proc.stdout.readline()
            if not resp_line:
                raise RuntimeError("MCP server closed stdout")
            try:
                resp = json.loads(resp_line)
            except json.JSONDecodeError:
                continue
            if resp.get("id") == req_id:
                return resp
        raise TimeoutError(f"MCP {method} timeout {timeout}s")

    def call_tool(self, name, arguments=None, timeout=PER_CALL_TIMEOUT_S):
        params = {"name": name, "arguments": arguments or {}}
        resp = self._call_raw("tools/call", params, timeout=timeout)
        if "error" in resp:
            return {"_error": resp["error"]}
        # MCP tool response: result.content[0].text contém JSON string
        result = resp.get("result", {})
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            try:
                return json.loads(content[0]["text"])
            except Exception:
                return {"_raw_text": content[0]["text"]}
        return result


def ts_iso(ts):
    if not ts:
        return None
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()


def capture_bar(client: MCPClient, bar_index: int):
    """Captura snapshot completo de 1 bar. Retorna dict."""
    t0 = time.monotonic()
    snap = {
        "bar_index": bar_index,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }

    rs = client.call_tool("replay_status")
    snap["replay_current_date"] = rs.get("current_date") if isinstance(rs, dict) else None
    snap["replay_current_dt"] = ts_iso(snap["replay_current_date"])

    sv = client.call_tool("data_get_study_values")
    snap["study_values"] = sv.get("studies") if isinstance(sv, dict) else None

    pb = client.call_tool("data_get_pine_boxes", {"verbose": True})
    snap["pine_boxes"] = pb.get("studies") if isinstance(pb, dict) else None

    # max_labels=500 pra capturar TODO histórico do NAS (era 10, perdia 98%)
    # verbose=True pra incluir x (bar_index TV) — necessário pra timing dos labels
    pl = client.call_tool("data_get_pine_labels", {"max_labels": 500, "verbose": True})
    snap["pine_labels"] = pl.get("studies") if isinstance(pl, dict) else None

    # 2026-05-19: nova tool data_get_pine_shapes captura Bubbles (plotshape) bar-a-bar.
    # Filter Bubbles pra reduzir payload; max_bars=20 pra ler só janela ao redor do bar atual.
    # Bubbles é o indicator-chave de order flow, NÃO PODE FALTAR.
    ps = client.call_tool("data_get_pine_shapes", {"study_filter": "Bubbles", "max_bars": 20})
    snap["pine_shapes_bubbles"] = ps.get("studies") if isinstance(ps, dict) else None

    ohlcv = client.call_tool("data_get_ohlcv", {"count": 40, "summary": False})
    if isinstance(ohlcv, dict):
        snap["ohlcv_last_40_bars"] = ohlcv.get("last_5_bars") or ohlcv.get("bars")
        snap["ohlcv_meta"] = {
            "bar_count": ohlcv.get("bar_count"),
            "period_from": ohlcv.get("period", {}).get("from"),
            "period_to": ohlcv.get("period", {}).get("to"),
            "close_current": ohlcv.get("close"),
        }

    snap["elapsed_s"] = round(time.monotonic() - t0, 2)
    return snap


def main():
    parser = argparse.ArgumentParser(description="XAU 4H backtest via MCP standalone")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--timeframe", default=DEFAULT_TIMEFRAME)
    parser.add_argument("--date", default=DEFAULT_START_DATE, help="Replay start date YYYY-MM-DD")
    parser.add_argument("--bars", type=int, default=DEFAULT_BARS)
    parser.add_argument("--checkpoint-every", type=int, default=CHECKPOINT_EVERY)
    parser.add_argument("--resume", action="store_true", help="Continue do último checkpoint")
    parser.add_argument("--dry-run", action="store_true", help="Init+1 bar e sai")
    parser.add_argument("--no-restore-chart", action="store_true", help="Skip restore chart no final")
    parser.add_argument("--suffix", default="", help="Suffix pro output filename (ex: _v2)")
    args = parser.parse_args()

    if not PAUSE_FLAG.exists():
        print(f"ERRO: pause flag não encontrada: {PAUSE_FLAG}", file=sys.stderr)
        print("Rode: touch /tmp/claude_recheck.paused", file=sys.stderr)
        return 1

    BACKTESTS_DIR.mkdir(parents=True, exist_ok=True)
    today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sym_short = args.symbol.split(":")[-1]
    out_basename = f"{sym_short}_{args.timeframe}_{args.date}_to_{today_iso}{args.suffix}"
    out_jsonl = BACKTESTS_DIR / f"{out_basename}.jsonl"
    checkpoint_path = BACKTESTS_DIR / f"{out_basename}.checkpoint.json"

    start_bar = 0
    if args.resume and checkpoint_path.exists():
        try:
            cp = json.loads(checkpoint_path.read_text())
            start_bar = cp.get("last_bar_completed", -1) + 1
            print(f"RESUME: continuando do bar {start_bar}")
        except Exception as e:
            print(f"RESUME falhou ({e}), começando do zero")

    print(f"[{datetime.now().isoformat()}] Iniciando backtest")
    print(f"  symbol: {args.symbol}")
    print(f"  timeframe: {args.timeframe}")
    print(f"  date inicial: {args.date}")
    print(f"  bars total: {args.bars}")
    print(f"  bar inicial: {start_bar}")
    print(f"  output: {out_jsonl}")
    print(f"  checkpoint: {checkpoint_path}")
    print()

    client = MCPClient(MCP_SERVER_PATH)
    print("Spawnando MCP server...")
    client.start()
    print("MCP conectado.")

    # Verifica saúde
    health = client.call_tool("tv_health_check")
    print(f"  CDP: connected={health.get('cdp_connected')}, target_url={health.get('target_url')}")

    original_symbol = None
    original_tf = None
    try:
        # Salvar estado original do chart
        state = client.call_tool("chart_get_state")
        if isinstance(state, dict):
            original_symbol = state.get("symbol")
            original_tf = state.get("resolution")
            print(f"  chart original: {original_symbol} {original_tf}")

        # Setup
        if start_bar == 0:
            print(f"\nSetup: trocar pra {args.symbol} {args.timeframe}...")
            r = client.call_tool("chart_set_symbol", {"symbol": args.symbol})
            if not r.get("success"):
                raise RuntimeError(f"chart_set_symbol failed: {r}")
            time.sleep(1)
            r = client.call_tool("chart_set_timeframe", {"timeframe": args.timeframe})
            if not r.get("success"):
                raise RuntimeError(f"chart_set_timeframe failed: {r}")
            time.sleep(1)

            print(f"replay_start({args.date})...")
            r = client.call_tool("replay_start", {"date": args.date})
            if not r.get("success"):
                raise RuntimeError(f"replay_start failed: {r}")
            print(f"  replay iniciado: {r.get('current_date')} ({ts_iso(r.get('current_date'))})")
            time.sleep(2)
        else:
            print("\nRESUME: assumindo replay já está ativo. Se não, abortar e rodar sem --resume.")

        # Loop principal
        mode = "a" if start_bar > 0 else "w"
        bars_to_run = args.bars - start_bar
        if args.dry_run:
            bars_to_run = min(1, bars_to_run)
            print(f"\nDRY-RUN: capturando só 1 bar")

        print(f"\nLoop {bars_to_run} bars (de {start_bar} a {args.bars-1})...")
        with out_jsonl.open(mode, encoding="utf-8") as f:
            total_elapsed = 0
            expected_symbol = args.symbol
            expected_tf = args.timeframe
            for i in range(start_bar, start_bar + bars_to_run):
                t_bar = time.monotonic()

                # === Defesa contra symbol switch durante backtest (2026-05-19) ===
                # Outras sessões Claude/MCP podem trocar o chart durante 3-15min de run.
                # Validar antes de cada captura: se symbol/tf mudou, abortar com erro claro.
                guard = client.call_tool("chart_get_state")
                if guard.get("symbol") != expected_symbol or guard.get("resolution") != expected_tf:
                    err = (f"CHART MUDOU NO BAR {i}: esperado {expected_symbol} {expected_tf}, "
                           f"recebido {guard.get('symbol')} {guard.get('resolution')}. "
                           f"Provável interferência de outra sessão MCP. Backtest abortado.")
                    print(f"\n!! {err}")
                    snap = {"bar_index": i, "_error": "symbol_switch_detected",
                            "expected": [expected_symbol, expected_tf],
                            "actual": [guard.get('symbol'), guard.get('resolution')],
                            "captured_at": datetime.now(timezone.utc).isoformat()}
                    f.write(json.dumps(snap, ensure_ascii=False) + "\n")
                    f.flush()
                    print(f"!! Bars completos antes do abort: {i - start_bar}")
                    print(f"!! Para retomar: python3 ... --resume (do checkpoint {(i // args.checkpoint_every) * args.checkpoint_every})")
                    raise RuntimeError(err)

                try:
                    snap = capture_bar(client, i)
                except Exception as e:
                    print(f"  ERRO no bar {i}: {e}")
                    snap = {"bar_index": i, "_error": str(e), "captured_at": datetime.now(timezone.utc).isoformat()}

                f.write(json.dumps(snap, ensure_ascii=False) + "\n")
                f.flush()
                bar_elapsed = time.monotonic() - t_bar
                total_elapsed += bar_elapsed

                # Step pro próximo (exceto no último)
                if i < start_bar + bars_to_run - 1:
                    step = client.call_tool("replay_step")
                    if not step.get("success"):
                        print(f"  WARN replay_step bar {i}: {step}")

                # Progress
                if (i + 1) % 10 == 0 or i == start_bar:
                    avg = total_elapsed / max(1, i - start_bar + 1)
                    remaining = (args.bars - i - 1) * avg
                    print(f"  [{datetime.now().strftime('%H:%M:%S')}] Bar {i+1}/{args.bars} "
                          f"({bar_elapsed:.1f}s, avg {avg:.1f}s, ETA {remaining/60:.1f}min)")

                # Checkpoint
                if (i + 1) % args.checkpoint_every == 0:
                    cp = {
                        "last_bar_completed": i,
                        "started_at": datetime.now(timezone.utc).isoformat(),
                        "out_jsonl": str(out_jsonl),
                        "symbol": args.symbol,
                        "timeframe": args.timeframe,
                        "date": args.date,
                    }
                    checkpoint_path.write_text(json.dumps(cp, indent=2))
                    print(f"  → checkpoint bar {i}")

        print(f"\nLoop completo. Total elapsed: {total_elapsed/60:.1f}min ({total_elapsed/max(1,bars_to_run):.1f}s/bar)")

    finally:
        # Cleanup
        print("\nStop replay + restaurar chart...")
        try:
            client.call_tool("replay_stop")
        except Exception as e:
            print(f"  replay_stop falhou: {e}")
        if not args.no_restore_chart and original_symbol:
            try:
                client.call_tool("chart_set_symbol", {"symbol": original_symbol})
                if original_tf:
                    client.call_tool("chart_set_timeframe", {"timeframe": original_tf})
                print(f"  chart restaurado: {original_symbol} {original_tf}")
            except Exception as e:
                print(f"  restore falhou: {e}")
        client.stop()
        print(f"\nMCP server stopped.")
        print(f"Output: {out_jsonl}")
        if out_jsonl.exists():
            lines = sum(1 for _ in out_jsonl.open())
            print(f"Linhas no JSONL: {lines}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
