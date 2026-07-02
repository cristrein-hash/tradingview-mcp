#!/usr/bin/env python3
"""
draw_xau_4h_trades.py — desenha trades do top combo do backtest XAU 4H
como long_position nativos do TradingView, para visualização.

🚨 AUTORIDADE: docs/project_authority/PLOTTING_CANON_MASTER.md (APPROVED 2026-07-02).
   LER O MASTER ANTES DE QUALQUER PLOT. Este script é a referência viva do HELPER
   (price_to_ticks_offset, MCPClient); em divergência de convenção, o MASTER prevalece.
   Reconciliado 2026-07-02 (Batch R1): draw_clear gated (default NO_CLEAR), screenshot
   gated (default skip), label #<id cronológico>, largura da caixa = BOX_BARS=20
   (separada do horizon de outcome, que permanece intacto).

Pré-requisitos:
    - touch /tmp/claude_recheck.paused
    - launchctl bootout gui/<uid>/com.cristrein.claude-{intraday-,}monitor
    - JSONL do backtest existir em logs/backtests/

Estratégia:
    1. Carrega o JSONL do backtest XAU 4H
    2. Filtra os 43 bars com combo IN_OB_ZONE + NAS:1to2 (top PRELIMINAR)
    3. Pra cada bar, calcula entry/target/stop:
       entry = close do bar
       target = entry + 2.7 × ATR (média do edge histórico em H=10)
       stop = entry - 1 × ATR (referência conservadora)
       exit_time = time do bar +10 candles
    4. Desenha long_position via MCP draw_shape
    5. Adiciona text label com R real obtido em cada trade
    6. Captura screenshot
    7. Restaura chart original

Uso:
    python3 draw_xau_4h_trades.py             # default: todos os 43 trades
    python3 draw_xau_4h_trades.py --limit 10  # só primeiros 10
    python3 draw_xau_4h_trades.py --clear-only  # apenas limpa desenhos atuais
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean
import argparse
import json
import math
import subprocess
import sys
import time

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
MCP_SERVER_PATH = BASE_DIR / "src" / "server.js"
NODE_BIN = "/opt/homebrew/bin/node"
BACKTEST_JSONL = BASE_DIR / "alert-bridge" / "logs" / "backtests" / "XAUUSD_240_2025-11-19_to_2026-05-19.jsonl"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
PAUSE_FLAG = Path("/tmp/claude_recheck.paused")

SYMBOL = "PEPPERSTONE:XAUUSD"
TIMEFRAME = "240"
HORIZON_BARS = 10  # exit (OUTCOME: close_R medido em H=10 — NÃO alterar; não é a largura da caixa)
TARGET_R_MULT = 2.7  # média histórica do top combo H=10
STOP_R_MULT = 1.0
MINTICK = 0.01  # XAUUSD (Pepperstone)
BOX_BARS = 20        # largura canônica da caixa long_position (PLOTTING_CANON_MASTER §10, 4H=20)
BAR_SECONDS = 14400  # 4H


def price_to_ticks_offset(entry_price, level_price, mintick=MINTICK):
    """TradingView long/short_position: stopLevel/profitLevel são OFFSETS EM TICKS a partir
    do entry, NÃO preços absolutos (descoberto 2026-06-11 — preços absolutos passados nesses
    campos produzem níveis ~entry±preço/100). Arredonda para tick inteiro (int round)."""
    if not (isinstance(mintick, (int, float)) and math.isfinite(mintick) and mintick > 0):
        raise ValueError(f"mintick inválido: {mintick!r}")
    for v in (entry_price, level_price):
        if not (isinstance(v, (int, float)) and math.isfinite(v)):
            raise ValueError(f"preço inválido: {v!r}")
    return int(round(abs(level_price - entry_price) / mintick))


class MCPClient:
    def __init__(self):
        self.proc = None
        self._req_id = 0

    def start(self):
        self.proc = subprocess.Popen(
            [NODE_BIN, str(MCP_SERVER_PATH)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1,
        )
        r = self._call_raw("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "draw-trades", "version": "1.0"},
        })
        if "error" in r:
            raise RuntimeError(f"MCP init failed: {r['error']}")
        self._notify("notifications/initialized", {})

    def stop(self):
        if self.proc:
            try: self.proc.stdin.close()
            except: pass
            try: self.proc.terminate(); self.proc.wait(timeout=5)
            except: self.proc.kill()

    def _notify(self, method, params):
        msg = {"jsonrpc": "2.0", "method": method, "params": params}
        self.proc.stdin.write(json.dumps(msg) + "\n"); self.proc.stdin.flush()

    def _call_raw(self, method, params, timeout=60):
        self._req_id += 1
        req_id = self._req_id
        msg = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
        self.proc.stdin.write(json.dumps(msg) + "\n"); self.proc.stdin.flush()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            line = self.proc.stdout.readline()
            if not line: raise RuntimeError("MCP server closed stdout")
            try:
                r = json.loads(line)
                if r.get("id") == req_id: return r
            except json.JSONDecodeError: continue
        raise TimeoutError(f"MCP {method} timeout")

    def call_tool(self, name, args=None, timeout=60):
        r = self._call_raw("tools/call", {"name": name, "arguments": args or {}}, timeout=timeout)
        if "error" in r: return {"_error": r["error"]}
        content = r.get("result", {}).get("content", [])
        if content and content[0].get("type") == "text":
            try: return json.loads(content[0]["text"])
            except: return {"_raw": content[0]["text"]}
        return r.get("result", {})


def load_bars():
    bars = []
    with BACKTEST_JSONL.open() as f:
        for line in f:
            try: bars.append(json.loads(line))
            except: pass
    # Truncate em primeiro bar vazio (safety)
    for i, b in enumerate(bars):
        if not (b.get('ohlcv_last_40_bars') or []):
            return bars[:i]
    return bars


def get_atr14(bar):
    """ATR usando bars closed (excluindo current degenerado)."""
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv) <= 1: return None
    closed = ohlcv[:-1][-14:]
    ranges = [b['high'] - b['low'] for b in closed if b.get('high') and b.get('low') and b['high'] > b['low']]
    return mean(ranges) if ranges else None


def get_state(bar):
    """Reconstrói state mínimo (RSI bucket, NAS bucket, in_ob_zone)."""
    rsi = nas = None
    for s in (bar.get('study_values') or []):
        if 'Relative Strength' in s.get('name', ''):
            try: rsi = float(s.get('values', {}).get('RSI', '').replace('−', '-'))
            except: pass
        if 'NAS' in s.get('name', ''):
            try: nas = float(s.get('values', {}).get('NAS_DISTANCE_FROM_EMA_ATR', '').replace('−', '-'))
            except: pass

    # RSI bucket
    rsi_bucket = None
    if rsi is not None:
        if rsi < 30: rsi_bucket = 'RSI<30'
        elif rsi < 40: rsi_bucket = 'RSI_30-40'
        elif rsi < 60: rsi_bucket = 'RSI_40-60'
        elif rsi < 70: rsi_bucket = 'RSI_60-70'
        else: rsi_bucket = 'RSI>70'

    # NAS bucket
    nas_bucket = None
    if nas is not None:
        if nas < -2: nas_bucket = 'NAS<-2'
        elif nas < -1: nas_bucket = 'NAS_-2to-1'
        elif nas < 1: nas_bucket = 'NAS_-1to1'
        elif nas < 2: nas_bucket = 'NAS_1to2'
        else: nas_bucket = 'NAS>2'

    # in_ob_zone
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    close = ohlcv[-1].get('close') if ohlcv else None
    in_ob = False
    for s in (bar.get('pine_boxes') or []):
        if 'Custom OB' in s.get('name', ''):
            for z in s.get('zones', []):
                hi, lo = z.get('high'), z.get('low')
                if hi is not None and lo is not None and close is not None and lo <= close <= hi:
                    in_ob = True
                    break
            break

    return {'rsi_bucket': rsi_bucket, 'nas_bucket': nas_bucket, 'in_ob_zone': in_ob, 'close': close}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--clear-only", action="store_true")
    p.add_argument("--no-restore", action="store_true")
    p.add_argument("--horizon", type=int, default=HORIZON_BARS)
    p.add_argument("--target-r", type=float, default=TARGET_R_MULT)
    p.add_argument("--stop-r", type=float, default=STOP_R_MULT)
    p.add_argument("--authorized-clear", action="store_true",
                   help="autorização EXPLÍCITA do Cris para draw_clear (PLOTTING_CANON_MASTER §11; default NO_CLEAR)")
    p.add_argument("--screenshot", action="store_true",
                   help="captura screenshot SÓ com pedido explícito do Cris (canon §5; default skip)")
    args = p.parse_args()

    if not PAUSE_FLAG.exists():
        print(f"ERRO: pause flag ausente. Rode: touch {PAUSE_FLAG}", file=sys.stderr)
        return 1

    client = MCPClient()
    print("Spawnando MCP server fresh...")
    client.start()
    print("OK")

    # Salva original chart state
    state = client.call_tool("chart_get_state")
    original_symbol = state.get('symbol')
    original_tf = state.get('resolution')
    print(f"  chart original: {original_symbol} {original_tf}")

    try:
        # Troca pra XAU 4H
        print(f"\nTrocar pra {SYMBOL} {TIMEFRAME}...")
        client.call_tool("chart_set_symbol", {"symbol": SYMBOL})
        time.sleep(1)
        client.call_tool("chart_set_timeframe", {"timeframe": TIMEFRAME})
        time.sleep(1)

        # Limpa desenhos — GATED (default NO_CLEAR, PLOTTING_CANON_MASTER §11)
        if args.authorized_clear:
            print("Limpando desenhos atuais (--authorized-clear)...")
            clr = client.call_tool("draw_clear")
            print(f"  {clr}")
        else:
            print("DRAW_CLEAR BLOQUEADO — default NO_CLEAR (PLOTTING_CANON_MASTER §11). "
                  "Plotagem será ADITIVA. Use --authorized-clear SOMENTE com autorização explícita do Cris.")
            if args.clear_only:
                print("--clear-only sem --authorized-clear: nada a fazer (bloqueado).")
                return 1

        if args.clear_only:
            print("clear-only: saindo.")
            return 0

        # Carrega dataset
        print(f"\nCarregando {BACKTEST_JSONL}...")
        bars = load_bars()
        print(f"  {len(bars)} bars válidos")

        # Filtra combo IN_OB_ZONE + NAS:1to2
        candidates = []
        for i, b in enumerate(bars):
            st = get_state(b)
            if st['in_ob_zone'] and st['nas_bucket'] == 'NAS_1to2':
                atr = get_atr14(b)
                if not atr or atr <= 0 or st['close'] is None: continue
                if i + args.horizon >= len(bars): continue
                ohlcv = b.get('ohlcv_last_40_bars') or []
                if not ohlcv: continue
                entry_time = ohlcv[-1].get('time')
                # close +N (futuro)
                next_b = bars[i + args.horizon]
                next_ohlcv = next_b.get('ohlcv_last_40_bars') or []
                if not next_ohlcv: continue
                exit_time = next_ohlcv[-1].get('time')
                exit_close = next_ohlcv[-1].get('close')
                close_R = (exit_close - st['close']) / atr if exit_close else 0
                candidates.append({
                    'bar_index': i,
                    'entry_time': entry_time,
                    'exit_time': exit_time,
                    'entry_price': st['close'],
                    'atr': atr,
                    'target_price': st['close'] + args.target_r * atr,
                    'stop_price': st['close'] - args.stop_r * atr,
                    'close_R': round(close_R, 2),
                    'rsi_bucket': st['rsi_bucket'],
                })

        print(f"\nTrades encontrados (IN_OB_ZONE + NAS:1to2): {len(candidates)}")
        if args.limit:
            candidates = candidates[:args.limit]
            print(f"Limitado a {len(candidates)}")

        wins = sum(1 for c in candidates if c['close_R'] > 0)
        avg_R = mean(c['close_R'] for c in candidates) if candidates else 0
        print(f"Win rate: {100*wins/len(candidates):.1f}%, avg_R={avg_R:+.2f}")

        # Desenha
        print(f"\nDesenhando {len(candidates)} long_position + labels...")
        drawn_count = 0
        for k, c in enumerate(candidates):
            # Long position
            r1 = client.call_tool("draw_shape", {
                "shape": "long_position",
                "point": {"time": c['entry_time'], "price": c['entry_price']},
                # largura canônica 20 barras (MASTER §10); outcome/horizon NÃO afetado
                "point2": {"time": c['entry_time'] + BOX_BARS * BAR_SECONDS, "price": c['target_price']},
                "overrides": json.dumps({
                    "stopLevel": price_to_ticks_offset(c['entry_price'], c['stop_price']),
                    "profitLevel": price_to_ticks_offset(c['entry_price'], c['target_price']),
                })
            })
            if r1.get('success'):
                drawn_count += 1
            else:
                print(f"  bar {c['bar_index']}: long_position falhou — {r1}")

            # Label canônico #<id cronológico> a 0.5R do entry (MASTER §4/§7); cor = outcome-mode
            R_dollars = c['entry_price'] - c['stop_price']
            label_y = c['entry_price'] + 0.5 * R_dollars
            label_text = f"#{k + 1}"
            r2 = client.call_tool("draw_shape", {
                "shape": "text",
                "point": {"time": c['entry_time'], "price": label_y},
                "text": label_text,
                "overrides": json.dumps({
                    "color": "#1a8917" if c['close_R'] > 0 else "#cc0000",
                    "bold": True,
                    "fontsize": 12,
                })
            })

            if (k + 1) % 5 == 0:
                print(f"  [{k+1}/{len(candidates)}] {drawn_count} desenhados")

        print(f"\nDesenhos criados: {drawn_count} long_position + labels")

        # Screenshot — GATED (canon §5: nunca screenshot sem pedido explícito)
        if args.screenshot:
            print("\nScreenshot (--screenshot, autorizado)...")
            SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            sshot = client.call_tool("capture_screenshot", {"region": "chart"})
            print(f"  {sshot}")
        else:
            print("\nSCREENSHOT_SKIPPED (canon §5 — verificação = success + draw_list; use --screenshot só a pedido do Cris)")

    finally:
        if not args.no_restore and original_symbol:
            print(f"\nRestaurando chart pra {original_symbol} {original_tf}...")
            client.call_tool("chart_set_symbol", {"symbol": original_symbol})
            if original_tf:
                client.call_tool("chart_set_timeframe", {"timeframe": original_tf})
        client.stop()
        print("MCP stopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
