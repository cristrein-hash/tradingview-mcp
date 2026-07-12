#!/usr/bin/env python3
"""COLETA EXÓGENAS DIÁRIO via MCP (ordem Cris 2026-07-12): DXY (chart já posicionado) e US10Y
(troca de símbolo autorizada). Paginação data_get_ohlcv from_time/to_time sobre o buffer em
memória (histórico carregado por scroll). Dedup por time, sort, validação de continuidade.
Organização canónica no HD externo (padrão replay): jsonl.gz + sha256 + gzip -t + manifest +
roundtrip. Cache local pequena no repo p/ uso imediato. Sem tocar em produção."""
import json, gzip, hashlib, subprocess, sys, time, datetime as dt
from pathlib import Path
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient
HERE = Path(__file__).resolve().parent
HD = Path("/Volumes/GUTS_ LACIE/TradingData/raw_external")
PAUSE = Path("/tmp/claude_recheck.paused")
WIN_S = 2*365*86400   # janelas de 2 anos
T_START = int(dt.datetime(1970, 1, 2, tzinfo=dt.timezone.utc).timestamp())

def collect_symbol(c, symbol, tf="1D"):
    st = c.call_tool("chart_get_state")
    if st.get("symbol") != symbol:
        r = c.call_tool("chart_set_symbol", {"symbol": symbol}); time.sleep(3)
    st = c.call_tool("chart_get_state")
    assert st.get("symbol") == symbol, f"chart não mudou para {symbol}: {st.get('symbol')}"
    if str(st.get("resolution")) not in ("1D", "D"):
        c.call_tool("chart_set_timeframe", {"timeframe": "D"}); time.sleep(3)
    # carregar histórico fundo: scroll em saltos até estabilizar total_available
    prev = -1
    for day in ("2016-01-01", "2010-01-01", "2004-01-01", "1998-01-01", "1992-01-01"):
        c.call_tool("chart_scroll_to_date", {"date": day}); time.sleep(3)
        r = c.call_tool("data_get_ohlcv", {"count": 1, "summary": False})
        tot = r.get("total_available", 0)
        if tot == prev: break
        prev = tot
    print(f"[{symbol}] total_available={prev}")
    bars = {}
    t0 = T_START; now = int(time.time())
    while t0 < now:
        t1 = min(t0+WIN_S, now+86400)
        r = c.call_tool("data_get_ohlcv", {"from_time": t0, "to_time": t1, "summary": False, "count": 500})
        for b in r.get("bars") or []:
            if b.get("close") is None: continue
            bars[b["time"]] = {"t": b["time"], "o": b["open"], "h": b["high"],
                               "l": b["low"], "c": b["close"]}
        t0 = t1
    ser = [bars[t] for t in sorted(bars)]
    assert ser, f"{symbol}: zero barras coletadas"
    # validação de continuidade: gaps > 10 dias (fora fins-de-semana/feriados) reportados
    gaps = [(ser[i-1]["t"], ser[i]["t"]) for i in range(1, len(ser))
            if ser[i]["t"]-ser[i-1]["t"] > 10*86400]
    return ser, gaps

def persist(symbol, ser, gaps):
    f = "%Y-%m-%d"
    d0 = dt.datetime.utcfromtimestamp(ser[0]["t"]).strftime(f)
    d1 = dt.datetime.utcfromtimestamp(ser[-1]["t"]).strftime(f)
    outdir = HD/symbol.replace("TVC:", ""); outdir.mkdir(parents=True, exist_ok=True)
    name = f"{symbol.replace('TVC:', '')}_1D_ohlcv_{d0}_to_{d1}.jsonl"
    raw = "\n".join(json.dumps(r) for r in ser)+"\n"
    gz = outdir/(name+".gz")
    with gzip.open(gz, "wt") as fh: fh.write(raw)
    sha = hashlib.sha256(gz.read_bytes()).hexdigest()
    (outdir/(name+".gz.sha256")).write_text(f"{sha}  {gz.name}\n")
    subprocess.run(["gzip", "-t", str(gz)], check=True)
    # roundtrip
    with gzip.open(gz, "rt") as fh: back = fh.read()
    assert back == raw, "roundtrip FALHOU"
    manifest = {"symbol": symbol, "tf": "1D", "n_bars": len(ser), "range": [d0, d1],
                "collected_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "method": "MCP data_get_ohlcv paginação from_time/to_time (buffer via scroll)",
                "sha256": sha, "gzip_test": "PASS", "roundtrip": "PASS",
                "gaps_gt_10d": [[dt.datetime.utcfromtimestamp(a).strftime(f),
                                 dt.datetime.utcfromtimestamp(b).strftime(f)] for a, b in gaps]}
    (outdir/(name.replace(".jsonl", "_manifest.json"))).write_text(json.dumps(manifest, indent=1))
    # cache local pequena
    local = HERE/f"raw_{symbol.replace('TVC:', '').lower()}_1d.jsonl"
    local.write_text(raw)
    print(f"[{symbol}] {len(ser)} barras {d0}→{d1} · sha {sha[:16]}… · gaps>10d: {len(gaps)} · HD: {gz}")
    return manifest

def main():
    assert PAUSE.exists(), "pause flag ausente"
    assert HD.parent.exists(), "HD externo não montado"
    c = MCPClient(); c.start()
    try:
        for sym in ("TVC:DXY", "TVC:US10Y"):
            ser, gaps = collect_symbol(c, sym)
            persist(sym, ser, gaps)
    finally:
        try: c.stop()
        except Exception: pass

if __name__ == "__main__":
    main()
