#!/usr/bin/env python3
"""Plot a chosen BREAKOUT/D1a trade set canonically (long_position + #id label).

Follows docs/CANONICAL_TRADE_PLOTTING.md EXACTLY:
- 2 shapes/trade: long_position (stop/profit in TICKS, mintick 0.01) + text label "#<id>".
- label green #1a8917 if close_R>0 else red #cc0000; at entry + 0.5*R_dollars; bold 12.
NO draw_clear, NO screenshot, NO symbol/timeframe switch, NO vertical lines / boxes / arrows.
Aborts if chart is not PEPPERSTONE:XAUUSD / 240, or any trade has invalid stop/target.

Reuses the canonical MCPClient + price_to_ticks_offset from alert-bridge/draw_xau_4h_trades.py.
"""
import json
import math
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve()
for d in (BASE_DIR.parent, *BASE_DIR.parents):
    if (d / "src" / "server.js").exists():
        ROOT = d
        break
MCP_SERVER_PATH = ROOT / "src" / "server.js"
NODE_BIN = "/opt/homebrew/bin/node"
PLOT_SET = Path("/tmp/t8_plot_set.json")
SYMBOL = "PEPPERSTONE:XAUUSD"
TIMEFRAME = "240"
MINTICK = 0.01


def price_to_ticks_offset(entry_price, level_price, mintick=MINTICK):
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
            text=True, bufsize=1)
        r = self._call_raw("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                          "clientInfo": {"name": "plot-t8", "version": "1.0"}})
        if "error" in r:
            raise RuntimeError(f"MCP init failed: {r['error']}")
        self._notify("notifications/initialized", {})

    def stop(self):
        if self.proc:
            try: self.proc.stdin.close()
            except Exception: pass
            try: self.proc.terminate(); self.proc.wait(timeout=5)
            except Exception: self.proc.kill()

    def _notify(self, method, params):
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method, "params": params}) + "\n")
        self.proc.stdin.flush()

    def _call_raw(self, method, params, timeout=60):
        self._req_id += 1
        rid = self._req_id
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": params}) + "\n")
        self.proc.stdin.flush()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("MCP server closed stdout")
            try:
                r = json.loads(line)
                if r.get("id") == rid:
                    return r
            except json.JSONDecodeError:
                continue
        raise TimeoutError(f"MCP {method} timeout")

    def call_tool(self, name, args=None, timeout=60):
        r = self._call_raw("tools/call", {"name": name, "arguments": args or {}}, timeout=timeout)
        if "error" in r:
            return {"_error": r["error"]}
        content = r.get("result", {}).get("content", [])
        if content and content[0].get("type") == "text":
            try: return json.loads(content[0]["text"])
            except Exception: return {"_raw": content[0]["text"]}
        return r.get("result", {})


def main():
    trades = json.load(open(PLOT_SET))
    # pre-validate ALL trades (hard stop on any invalid)
    for t in trades:
        e, s, tg = t["entry_price"], t["stop_price"], t["target_price"]
        if not (e > s and tg > e):
            print(f"HARD STOP: trade #{t['id']} invalid stop/target e={e} s={s} tg={tg}", file=sys.stderr)
            return 1
        if price_to_ticks_offset(e, s) <= 0 or price_to_ticks_offset(e, tg) <= 0:
            print(f"HARD STOP: trade #{t['id']} ticks <= 0", file=sys.stderr)
            return 1

    client = MCPClient()
    client.start()
    try:
        st = client.call_tool("chart_get_state")
        if st.get("symbol") != SYMBOL or str(st.get("resolution")) != TIMEFRAME:
            print(f"HARD STOP: chart is {st.get('symbol')}/{st.get('resolution')}, expected {SYMBOL}/{TIMEFRAME}",
                  file=sys.stderr)
            return 1
        print(f"chart OK: {st.get('symbol')}/{st.get('resolution')} | plotting {len(trades)} trades")

        ok_pos = ok_lbl = fail = 0
        for k, t in enumerate(trades):
            R_dollars = t["entry_price"] - t["stop_price"]
            color = t.get("color") or ("#1a8917" if t.get("close_R", 0) > 0 else "#cc0000")
            r1 = client.call_tool("draw_shape", {
                "shape": "long_position",
                "point": {"time": t["entry_time"], "price": t["entry_price"]},
                "point2": {"time": t["exit_time"], "price": t["target_price"]},
                "overrides": json.dumps({
                    "stopLevel": price_to_ticks_offset(t["entry_price"], t["stop_price"]),
                    "profitLevel": price_to_ticks_offset(t["entry_price"], t["target_price"]),
                })})
            if r1.get("success"):
                ok_pos += 1
            else:
                fail += 1
                print(f"  #{t['id']} long_position FAIL: {r1}")
            r2 = client.call_tool("draw_shape", {
                "shape": "text",
                "point": {"time": t["entry_time"], "price": t["entry_price"] + 0.5 * R_dollars},
                "text": f"#{t['id']}",
                "overrides": json.dumps({"color": color, "bold": True, "fontsize": 12})})
            if r2.get("success"):
                ok_lbl += 1
            else:
                fail += 1
                print(f"  #{t['id']} label FAIL: {r2}")
            if (k + 1) % 25 == 0:
                print(f"  [{k+1}/{len(trades)}] pos={ok_pos} lbl={ok_lbl} fail={fail}")

        dl = client.call_tool("draw_list")
        n_drawn = len(dl.get("drawings") or dl.get("shapes") or []) if isinstance(dl, dict) else None
        print(json.dumps({"trades": len(trades), "long_position_ok": ok_pos, "label_ok": ok_lbl,
                          "failures": fail, "expected_shapes": 2 * len(trades),
                          "draw_list_count": n_drawn}, indent=2))
    finally:
        client.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
