#!/usr/bin/env python3
"""Plota os 17 trades da célula capitulation+rsi_momentum no chart XAU 4H — CANÔNICO.
Segue docs/CANONICAL_TRADE_PLOTTING.md (long_position largura 20 barras + label #N; ticks; sem screenshot).
Política DECLARADA (§4): SL estrutural = entry − sl_atr×ATR (política do engine L2/BPT); target = +2R
(limiar hit_2R do engine). Cor do label por realR (winner verde / loser vermelho). NÃO faz draw_clear
(Cris limpa manual, §6). Pré-req: /tmp/claude_recheck.paused + daemon/cron pausados.
"""
import os, sys, csv, json, glob, time
AB = "/Users/cristrein/tradingview-mcp/alert-bridge"
sys.path.insert(0, AB)
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset  # reuso canônico

QD = os.path.dirname(os.path.abspath(__file__))
D = os.path.normpath(os.path.join(QD, "..", "..", "results"))
RR = os.path.normpath(os.path.join(QD, "..", "..", "repro_recovery"))
SYMBOL, TF, BAR_SECONDS, WIDTH_BARS = "PEPPERSTONE:XAUUSD", "240", 14400, 20

# ---- célula capit+rsi (state fiel à 2B.5) ----
mat = {(int(r['episode_id']), r['specialist_id']): r for r in csv.DictReader(open(f"{D}/l2_bpt_specialist_ablation_ready_matrix.csv"))}
net = {}
for fp in glob.glob(f"{D}/specialist_out/*.jsonl"):
    fam = os.path.basename(fp)[:-6]
    for l in open(fp):
        if l.strip():
            r = json.loads(l); net[(int(r['episode_id']), fam)] = r.get('net_read')
out = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
pk = {int(json.loads(l)['bar_idx']): json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
def veto(i, s): return int(mat.get((i, s), {}).get('veto_count', '0') or 0) > 0
def review(i, s): return int(mat.get((i, s), {}).get('review_flag_count', '0') or 0) > 0
def state(i, s):
    if veto(i, s): return 'veto'
    st = net.get((i, s), 'neutral')
    if review(i, s) and st == 'neutral': return 'review_flag'
    return st
EP = sorted(set(i for i, _ in mat if i in out))
CELL = [i for i in EP if state(i, 'capitulation') == 'supportive' and state(i, 'rsi_momentum') == 'supportive']

# ---- montar trades (cronológico) ----
trades = []
for i in sorted(CELL, key=lambda x: out[x]['datetime']):
    p = pk[i]; entry = float(p['price']); atr = float(p['atr']); ts = int(p['ts'])
    sl_atr = float(out[i]['sl_atr']); realR = float(out[i]['realR'])
    R_dollars = sl_atr * atr                       # 1R em USD (SL estrutural)
    stop = entry - R_dollars
    target = entry + 2.0 * R_dollars               # +2R = limiar hit_2R do engine (DECLARADO)
    trades.append(dict(bar_idx=i, dt=out[i]['datetime'], entry_time=ts, entry=entry, stop=stop,
                       target=target, R_dollars=R_dollars, close_R=realR, exitype=out[i]['exitype']))

print(f"Trades célula capit+rsi: {len(trades)} (chronologico #1={trades[0]['dt']} .. #{len(trades)}={trades[-1]['dt']})")

cli = MCPClient(); cli.start()
try:
    st = cli.call_tool("chart_get_state"); print(f"chart atual: {st.get('symbol')} {st.get('resolution')}")
    cli.call_tool("chart_set_symbol", {"symbol": SYMBOL}); time.sleep(1)
    cli.call_tool("chart_set_timeframe", {"timeframe": TF}); time.sleep(1)
    n_lp = n_lbl = 0
    for k, t in enumerate(trades, 1):
        assert t['entry'] > t['stop'] and t['target'] > t['entry'], f"validação falhou #{k}"
        r1 = cli.call_tool("draw_shape", {
            "shape": "long_position",
            "point": {"time": t['entry_time'], "price": t['entry']},
            "point2": {"time": t['entry_time'] + WIDTH_BARS * BAR_SECONDS, "price": t['target']},
            "overrides": json.dumps({
                "stopLevel": price_to_ticks_offset(t['entry'], t['stop']),
                "profitLevel": price_to_ticks_offset(t['entry'], t['target']),
            })})
        if r1.get('success'): n_lp += 1
        else: print(f"  #{k} long_position FALHOU: {r1}")
        label_y = t['entry'] + 0.5 * t['R_dollars']
        r2 = cli.call_tool("draw_shape", {
            "shape": "text",
            "point": {"time": t['entry_time'], "price": label_y},
            "text": f"#{k}",
            "overrides": json.dumps({"color": "#1a8917" if t['close_R'] > 0 else "#cc0000", "bold": True, "fontsize": 12})})
        if r2.get('success'): n_lbl += 1
        else: print(f"  #{k} label FALHOU: {r2}")
    print(f"\nDESENHADO: {n_lp} long_position + {n_lbl} labels (de {len(trades)} trades)")
    dl = cli.call_tool("draw_list")
    cnt = dl.get('count') if isinstance(dl, dict) else None
    print(f"draw_list count: {cnt}")
finally:
    cli.stop()
    print("MCP stopped. (chart deixado em XAU 4H)")
