#!/usr/bin/env python3
"""RECOLHA 1D NATIVO XAUUSD via MCP até ONTEM FECHADO (ordem Cris 2026-07-13). Chart já em
PEPPERSTONE:XAUUSD 1D. Carrega histórico fundo (scroll até 2012), pagina data_get_ohlcv,
EXCLUI a barra em formação (mantém só barras com dia < hoje UTC). Salva no HD externo (raw_external)
+ gzip+sha256+gzip-t+roundtrip+manifest; cache local raw_1d_ohlc.jsonl (substitui, source=chart-native
PEPPERSTONE, consistente). RAW-nativo only, sem resample."""
import json, gzip, hashlib, subprocess, sys, time, datetime as dt
from pathlib import Path
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient
HERE = Path(__file__).resolve().parent
HD = Path("/Volumes/GUTS_ LACIE/TradingData/raw_external/XAUUSD")
PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL = "PEPPERSTONE:XAUUSD"
# "ontem fechado": manter barras com dia < hoje 00:00 UTC (exclui barra em formação de hoje)
TODAY0 = int(dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())

def main():
    assert PAUSE.exists(), "pause flag ausente"
    assert HD.parent.exists(), "HD externo não montado"
    c = MCPClient(); c.start()
    try:
        st = c.call_tool("chart_get_state")
        assert st.get("symbol") == SYMBOL and str(st.get("resolution")) in ("1D", "D"), \
            f"chart {st.get('symbol')}/{st.get('resolution')} != {SYMBOL}/1D"
        # carregar histórico fundo (scroll em saltos até estabilizar)
        prev = -1
        for y in ("2016-01-01", "2012-01-01", "2010-01-01", "2008-01-01"):
            c.call_tool("chart_scroll_to_date", {"date": y}); time.sleep(3)
            r = c.call_tool("data_get_ohlcv", {"count": 1, "summary": False})
            tot = r.get("total_available", 0)
            if tot == prev: break
            prev = tot
        print("total_available:", prev)
        bars = {}
        t0 = int(dt.datetime(1970, 1, 2, tzinfo=dt.timezone.utc).timestamp()); now = int(time.time())
        win = 2*365*86400
        while t0 < now:
            t1 = min(t0+win, now+86400)
            r = c.call_tool("data_get_ohlcv", {"from_time": t0, "to_time": t1, "summary": False, "count": 500})
            for b in r.get("bars") or []:
                if b.get("close") is None: continue
                bars[b["time"]] = {"t": b["time"], "o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]}
            t0 = t1
        ser = [bars[t] for t in sorted(bars) if t < TODAY0]     # exclui barra em formação
        assert ser, "zero barras"
    finally:
        try: c.stop()
        except Exception: pass
    f = "%Y-%m-%d"
    d0 = dt.datetime.utcfromtimestamp(ser[0]["t"]).strftime(f)
    d1 = dt.datetime.utcfromtimestamp(ser[-1]["t"]).strftime(f)
    raw = "".join(json.dumps(r)+"\n" for r in ser)
    HD.mkdir(parents=True, exist_ok=True)
    name = f"XAUUSD_1D_ohlcv_{d0}_to_{d1}"
    gz = HD/(name+".jsonl.gz")
    with gzip.open(gz, "wt") as fh: fh.write(raw)
    sha = hashlib.sha256(gz.read_bytes()).hexdigest()
    (HD/(name+".jsonl.gz.sha256")).write_text(f"{sha}  {gz.name}\n")
    subprocess.run(["gzip", "-t", str(gz)], check=True)
    with gzip.open(gz, "rt") as fh: assert fh.read() == raw, "roundtrip FALHOU"
    gaps = [(ser[i-1]["t"], ser[i]["t"]) for i in range(1, len(ser)) if ser[i]["t"]-ser[i-1]["t"] > 10*86400]
    (HD/(name+"_manifest.json")).write_text(json.dumps({
        "symbol": SYMBOL, "tf": "1D", "n_bars": len(ser), "range": [d0, d1],
        "collected_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "method": "MCP data_get_ohlcv paginação (chart-native, forming bar excluded < today UTC)",
        "sha256": sha, "gzip_test": "PASS", "roundtrip": "PASS", "gaps_gt_10d": len(gaps)}, indent=1))
    (HERE/"raw_1d_ohlc.jsonl").write_text(raw)   # substitui cache local (fonte única consistente)
    print(f"1D nativo: {len(ser)} barras {d0}→{d1} · sha {sha[:16]}… · gaps>10d {len(gaps)} · HD {gz.name}")

if __name__ == "__main__":
    main()
