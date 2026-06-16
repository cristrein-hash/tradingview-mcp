"""Plot V1.4g-RWS trades 2023+ on chart with A6 distinction.
- KEPT (A6 ✓): green long_position with R label
- CUT (A6 ✗): magenta/purple long_position with ✗ overlay text

⚠️ DEPRECATED — DO NOT USE — BUG: stopLevel/profitLevel passados como PREÇO ABSOLUTO
(linha ~23). O TradingView interpreta esses campos como OFFSETS EM TICKS, não preços.
Plotar com este script produz stop/target-artefato. A6 é KEEP_REFERENCE (não operacional).
Para qualquer plotagem nova, usar docs/CANONICAL_TRADE_PLOTTING.md +
alert-bridge/draw_xau_4h_trades.py (price_to_ticks_offset). Mantido só como histórico."""
import json, subprocess
from datetime import datetime

INPUT = "/tmp/v14g_rws_2023plus_with_a6_flag.jsonl"
trades = [json.loads(l) for l in open(INPUT)]
print(f"Total to plot: {len(trades)}  ({sum(1 for t in trades if not t['cut_by_a6'])} kept / {sum(1 for t in trades if t['cut_by_a6'])} CUT by A6)")

def iso_to_unix(iso):
    return int(datetime.fromisoformat(iso).timestamp())

def plot_trade(idx, t):
    entry_time = iso_to_unix(t["ts"])
    exit_time = entry_time + int(t["exit_bars"]) * 4 * 3600
    entry = t["entry"]
    stop = t["stop"]
    exit_price = t["exit_price"]

    # Long position drawing
    # 🔴 BUG (DEPRECATED): preço absoluto — o correto é TICKS:
    #   "stopLevel": round((entry-stop)/0.01), "profitLevel": round((exit_price-entry)/0.01)
    # Ver docs/CANONICAL_TRADE_PLOTTING.md. Não corrigido aqui (script reference-only/histórico).
    overrides = {"stopLevel": stop, "profitLevel": exit_price}
    cmd = ["node", "src/cli/index.js", "draw", "shape",
           "--type", "long_position",
           "--time", str(entry_time), "--price", str(entry),
           "--time2", str(exit_time), "--price2", str(exit_price),
           "--overrides", json.dumps(overrides)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    try: lp_ok = json.loads(r.stdout).get("success", False)
    except: lp_ok = False

    # Text label
    atr = float(t["atr14"])
    label_y = max(exit_price, entry) + 0.7 * atr
    R = float(t["R"])
    mfe = float(t["MFE_R"])
    if t["cut_by_a6"]:
        # Highlighted CUT
        label_text = f"✗A6 R{R:+.1f} MFE{mfe:.1f}"
        color = "#cc00aa"  # magenta
        bold = True
        fontsize = 13
    else:
        # Normal KEPT
        symbol = "✓"
        if R > 0.05:
            color = "#1a8917"  # green
        elif R < -0.05:
            color = "#cc0000"  # red
        else:
            color = "#cc8800"  # amber (BE)
        label_text = f"{symbol}R{R:+.1f}"
        bold = False
        fontsize = 10

    cmd2 = ["node", "src/cli/index.js", "draw", "shape",
            "--type", "text",
            "--time", str(entry_time), "--price", str(label_y),
            "--text", label_text,
            "--overrides", json.dumps({"color": color, "bold": bold, "fontsize": fontsize})]
    r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=20)
    try: tx_ok = json.loads(r2.stdout).get("success", False)
    except: tx_ok = False
    return lp_ok, tx_ok

ok_lp = ok_tx = 0
for i, t in enumerate(trades):
    flag = "✗A6" if t["cut_by_a6"] else "  "
    a, b = plot_trade(i, t)
    if a: ok_lp += 1
    if b: ok_tx += 1
    R = t["R"]; mfe = t["MFE_R"]; sym = "✓" if R > 0.05 else ("=" if abs(R) < 0.05 else "✗")
    print(f"  [{flag}] #{i:>2} {t['ts'][:16]} {sym} entry={t['entry']:.1f} R={R:+.2f} MFE={mfe:.1f}R  lp={'OK' if a else 'FAIL'} tx={'OK' if b else 'FAIL'}")

print(f"\nPlotted: {ok_lp} positions / {ok_tx} labels of {len(trades)} target trades")
